import json
import os
import shutil
import time
import zipfile
from datetime import datetime as dt
from functools import reduce
from io import BytesIO

# import cv2
from flask import current_app, send_file

from ..const import SCHEDULE_FIFOIN, SCHEDULE_FIFOOUT


def getr(data, keys, default: any = None) -> any:
    """Return value of dict from get recursive key."""
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        data,
    )


def init_settings() -> None:
    raspi_config = get_config()
    default_config = current_app.config["DEFAULT_INIT"]
    if not file_exists(current_app.config["FILE_SETTINGS"]):
        default_config.update(
            {
                SCHEDULE_FIFOIN: raspi_config["motion_pipe"],
                SCHEDULE_FIFOOUT: raspi_config["control_file"],
            }
        )
        set_settings(default_config, current_app.config["FILE_SETTINGS"])


def get_settings(
    attr: str | float | int = None, default=None, path_file=None
) -> dict[str, any] | None:
    """Get settings.json."""
    settings = None
    if not path_file:
        path_file = current_app.config["FILE_SETTINGS"]

    if file_exists(path_file):
        with open(path_file, "r") as f:
            settings = json.loads(f.read())
        if attr:
            return getr(settings, attr, default)
    return settings


def set_settings(data, path_file=None):
    """Set settings.json."""
    if not path_file:
        path_file = current_app.config["FILE_SETTINGS"]

    cur_data = {}
    if os.path.isfile(path_file) and os.stat(path_file).st_size > 0:
        with open(path_file, "r") as f:
            cur_data = json.loads(f.read())
            f.close()

    serialize_data = {}
    days = {}
    for k, v in data.items():
        if "days[" in k:
            index = int(k.replace("days[", "").replace("][]", ""))
            days.update({index: data.getlist(k)})
        elif "[]" in k:
            serialize_data.update({k.replace("[]", ""): data.getlist(k)})
        else:
            serialize_data.update({k: v})

    if days:
        serialize_data.update({"days": days})

    serialize_data = normalize(serialize_data)

    cur_data.update(serialize_data)

    with open(path_file, "w") as f:
        f.write(json.dumps(cur_data))
        f.close()


def get_config(attr: str | float | int = None) -> any:
    """Get raspimjpeg config."""
    raspi_config_orig = get_file_config({}, current_app.config["CONFIG_FILE1"])
    config = get_file_config(raspi_config_orig, raspi_config_orig["user_config"])
    if attr:
        return config.get(attr)
    return config


def set_config(config) -> None:
    """Set raspimjpeg config."""
    user_file = get_config("user_config")
    lines = "#User config file\n"
    for k, v in config:
        lines += f"{k} {v}\n"
    file_set_content(user_file, lines)


# functions to find and delete data files
def get_sorted_files(folder, ascending=True):
    scanfiles = list_folder_files(folder)
    files = {}
    for file in scanfiles:
        if file != "." and file != ".." and is_thumbnail(file):
            fDate = os.path.getmtime(f"{folder}/{file}").hour()
            files[file] = fDate
    if ascending:
        files.sort()
    else:
        files.sort(reverse=True)
    return files.keys()


# functions to find and delete data files
def find_lapse_files(filename):
    media_path = get_config("media_path")

    batch = get_file_index(filename)
    padlen = len(batch)
    fullname = f"{media_path}/{data_filename(filename)}"
    path = f"{media_path}"
    start = os.path.getmtime(fullname).hour()
    files = {}
    scanfiles = list_folder_files(f"{media_path}")
    lapsefiles = []
    for file in scanfiles:
        if file.find(batch):
            if (not is_thumbnail(file)) and get_file_ext(file, "jpg"):
                fDate = os.path.getmtime(f"{media_path}/{file}").hour()
                if fDate >= start:
                    files[file] = fDate + file
    files.sort()
    lapseCount = 1
    for key, value in files.items():
        if key[lapseCount.zfile(padlen) :]:  # noqa: E203
            lapsefiles.append(f"{path}/{key}")
            lapseCount += 1
        else:
            break
    return lapsefiles


# function to get filesize (native php has 2GB limit)
def filesize_n(path):
    if current_app.config["FILESIZE_METHOD"] == 0:
        size = os.stat(path).st_size
        if size > 0:
            return size
        else:
            return 4294967296 - size
    else:
        return f"stat -c%s {path}".strip()


# function to delete all files associated with a thumb name
def delete_mediafiles(filename, delete=True):
    media_path = get_config("media_path")
    size = 0
    t = get_file_type(filename)
    if t == "t":
        #  For time lapse try to delete all from this batch
        files = find_lapse_files(filename)
        for file in files:
            size += filesize_n(f"{media_path}/{file}")
            if delete:
                os.remove(f"{media_path}/{file}")
    else:
        tFile = data_filename(filename)
        if file_exists(f"{media_path}/{tFile}"):
            size += filesize_n(f"{media_path}/{tFile}")
            if delete:
                os.remove(f"{media_path}/{tFile}")
        if t == "v":
            rFile = tFile[: tFile.find(".")]
            if file_exists(f"{media_path}/{tFile}.dat"):
                size += filesize_n(f"{media_path}/{tFile}.dat")
                if delete:
                    os.remove(f"{media_path}/{tFile}.dat")

            if file_exists(f"{media_path}/{rFile}.h264"):
                size += filesize_n(f"{media_path}/{rFile}.h264")
                if delete:
                    os.remove(f"{media_path}/{rFile}.h264")

            if file_exists(f"{media_path}/{rFile}.h264.bad"):
                size += filesize_n(f"{media_path}/{rFile}.h264.bad")
                if delete:
                    os.remove(f"{media_path}/{rFile}.h264.bad")

            if file_exists(f"{media_path}/{rFile}.h264.log"):
                size += filesize_n(f"{media_path}/{rFile}.h264.log")
                if delete:
                    os.remove(f"{media_path}/{rFile}.h264.log")

    size += filesize_n(f"{media_path}/{filename}")
    if delete:
        os.remove(f"{media_path}/{filename}")
    return size / 1024


# function to lock or unlock all files associated with a thumb name
def lock_file(filename: str, lock: bool):
    media_path = get_config("media_path")
    if lock == 1:
        attr = "0444"
    else:
        attr = "0644"
    t = get_file_type(filename)
    if t == "t":
        #  For time lapse lock all from this batch
        files = find_lapse_files(filename)
        for file in files:
            os.popen(f"chmod {attr} {file}")
    else:
        tFile = data_filename(filename)
        if file_exists(f"{media_path}/{tFile}"):
            os.popen(f"chmod {attr} {media_path}/{tFile}")
        if t == "v" and file_exists(f"{media_path}/{tFile}.dat"):
            os.popen(f"chmod {attr} {media_path}/{tFile}.dat")
        if t == "v" and file_exists(f"{media_path}/{tFile}.h264"):
            os.popen(f"chmod {attr} {media_path}/{tFile}.h264")

    os.popen(f"chmod {attr} {media_path}/{filename}")


# Support naming functions
def data_filename(file):
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[:i].replace(get_config("subdir_char"), "/")
    return ""


def data_file_ext(file):
    f = data_filename(file)
    return get_file_ext(f)


def get_file_ext(file):
    i = file.rfind(".")
    if i > 0:
        return file[i + 1 :]  # noqa: E203
    return ""


# Support naming functions
def is_thumbnail(file):
    return file[-7:] == current_app.config["THUMBNAIL_EXT"]


def get_file_type(file):
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[i + 1]
    return ""


def get_file_index(file):
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[i + 2 : len(file) - i - 9]  # noqa: E203
    return ""


def file_exists(filename):
    return os.path.isfile(filename)


def file_get_content(filename):
    return open(filename, "r").read()


def file_set_content(filename, data, bjson=False):
    if bjson:
        data = json.dumps(data)
    content = open(filename, "w")
    content.write(data)
    content.close


def file_add_content(filename, data):
    content = open(filename, "w") if not file_exists(filename) else open(filename, "a")
    content.write(data)
    content.close


def execute_cmd(cmd):
    return os.popen(cmd)


def get_log():
    log_file = get_config("log_file")
    log = []
    if file_exists(log_file):
        lines = open(log_file, "r").readlines()
        lines.sort(reverse=True)
        for line in lines:
            log.append(line.replace("\n", ""))
        return log


def get_log_size():
    config = get_config()
    return int(config["log_size"])


def write_log(msg):
    log_file = get_config("log_file")
    if file_exists(log_file):
        str_now = dt.now().strftime("%Y/%m/%D %H:%M:%S")
        file_add_content(log_file, f"{str_now} {msg}\n")


def delete_log(log_size):
    log_file = get_config("log_file")
    if file_exists(log_file):
        log_lines = open(log_file, "r").readlines()
        if len(log_lines) > log_size:
            file_set_content(log_file, log_lines[:log_size])


def write_debug_log(msg):
    log_file = current_app.config["LOGFILE_DEBUG"]
    str_now = dt.now().strftime("%Y/%m/%D %H:%M:%S")
    file_add_content(log_file, f"{str_now} {msg}\n")


def get_file_config(config: dict[str, any], filename):
    if file_exists(filename):
        data = file_get_content(filename)
        lines = data.split("\n")
        for line in lines:
            if len(line) and line[0:1] != "#":
                index = line.find(" ")
                if index:
                    key = line[0:index]
                    value = line[index + 1 :]  # noqa: E203
                    if value == "true":
                        value = 1
                    if value == "false":
                        value = 0
                    config[key] = value
                else:
                    config[line] = ""
    return config


def list_folder_files(path: str, ext=None):
    if ext:
        return [
            f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f)) and f".{ext}" in f
        ]
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]


def get_shm_cam():
    path_cam = "/dev/shm/mjpeg/cam.jpg"
    if file_exists(path_cam):
        return open(path_cam, "rb").read()


def send_cmds(
    fifo: str, str_cmd: str, days: dict[str, any] | None = None, period: bool = False
):
    if str_cmd and (period is False or is_day_active(days, period)):
        cmds = str_cmd.split(";")
        for cmd in cmds:
            if cmd != "":
                cmd = cmd.strip()
                send_pipe(fifo, cmd)
                time.sleep(0.2)


def open_pipe(pipename: str):
    if not os.path.exists(pipename):
        write_log(f"Making Pipe to receive capture commands {pipename}")
        os.popen(f"mkfifo {pipename}")
        os.popen(f"chmod 666 {pipename}")
    else:
        write_log(f"Capture Pipe already exists ({pipename})")

    try:
        pipe = os.open(pipename, os.O_RDONLY | os.O_NONBLOCK)
    except OSError as e:
        write_log(f"Error open pipe {pipename} {str(e)}")

    return pipe


def send_pipe(pipename: str, cmd: str):
    if not os.path.exists(pipename):
        write_log(f"Making Pipe {pipename}")
        os.popen(f"mkfifo {pipename}")
        os.popen(f"chmod 666 {pipename}")

    try:
        pipe = os.open(pipename, os.O_WRONLY | os.O_NONBLOCK)
    except OSError as error:
        write_log(str(error))
    else:
        os.write(pipe, f"{cmd}\n".encode("utf-8"))
        os.close(pipe)
        write_log(f"Send {cmd}")


def check_motion(pipe):
    if isinstance(pipe, bool):
        return ""
    try:
        ret = os.read(pipe, 0).decode("utf-8")
    except Exception as error:  # noqa: F841
        ret = ""

    return ret


def purge_files(
    sch_purgevideohours: int,
    sch_purgeimagehours: int,
    sch_purgelapsehours: int,
    sch_purgespacelevel: int,
    sch_purgespacemode: int,
):
    media_path = get_config("media_path")
    purgeCount = 0
    if sch_purgevideohours > 0 or sch_purgeimagehours > 0 or sch_purgelapsehours > 0:
        files = list_folder_files(media_path)
        currentHours = dt.utcnow().timestamp() / 3600
        for file in files:
            if file != "." and file != ".." and is_thumbnail(file):
                fType = get_file_type(file)
                purgeHours = 0
                match fType:
                    case "i":
                        purgeHours = sch_purgeimagehours
                    case "t":
                        purgeHours = sch_purgelapsehours
                    case "v":
                        purgeHours = sch_purgevideohours
                if purgeHours > 0:
                    fModHours = os.path.getmtime(f"{media_path}/{file}").hour()
                    if fModHours > 0 and (currentHours - fModHours) > purgeHours:
                        os.remove(f"{media_path}/{file}")
                        purgeCount += 1
            elif sch_purgevideohours > 0:
                if ".zip" in file:
                    fModHours = os.path.getmtime(f"{media_path}/{file}").hour()
                    if (
                        fModHours > 0
                        and (currentHours - fModHours)  # noqa: W503
                        > sch_purgevideohours  # noqa: W503
                    ):
                        os.remove(f"{media_path}/{file}")
                        write_log("Purged orphan zip file")

    if sch_purgespacemode > 0:
        total, used, free = shutil.disk_usage(f"{media_path}")
        # level = str_replace(
        #     array("%", "G", "B", "g", "b"), "", sch_purgespacelevel
        # )

        match sch_purgespacemode:
            case 1, 2:
                level = min(max(sch_purgespacelevel, 3), 97) * total / 100
            case 3, 4:
                level = level * 1048576.0

        match sch_purgespacemode:
            case 1, 3:
                if free < level:
                    p_files = get_sorted_files(media_path, False)
                    for p_file in p_files:
                        if free < level:
                            free += delete_mediafiles(p_file)
                        purgeCount += 1
            case 2, 4:
                p_files = get_sorted_files(media_path, False)
                for p_file in p_files:
                    del_l = level <= 0
                    level -= delete_mediafiles(p_file, del_l)
                    if del_l:
                        purgeCount += 1

    if purgeCount > 0:
        write_log("Purged purgeCount Files")


def json2dict(data: list | str):
    if isinstance(data, list):
        return [json2dict(value) for value in data]
    try:
        return int(data)
    except Exception:
        try:
            return float(data)
        except Exception:
            return data


def normalize(data: list | dict):
    for k, v in data.items():
        if isinstance(v, dict):
            data.update({k: normalize(v)})
        data.update({k: json2dict(v)})
    return data


def get_zip(files: list):
    media_path = get_config("media_path")
    date_str = dt.now().strftime("%Y%m%d_%H%M%S")
    zipname = f"cam_{date_str}.zip"

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, "a") as zf:
        for individualFile in files:
            file_name = data_filename(individualFile)
            try:
                data = zipfile.ZipInfo(file_name)
                data.date_time = time.localtime(time.time())[:6]
                data.compress_type = zipfile.ZIP_DEFLATED
                # zf.writestr(data, f"{media_path}/{data_filename(individualFile)}")
                zf.write(f"{media_path}/{file_name}", file_name, data.compress_type)
            except FileNotFoundError:
                continue
    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zipname,
    )


def maintain_folders(path, delete_main_files, delete_sub_files, root: bool = True):
    empty = True
    for file in list_folder_files(path):
        if os.path.isdir(file):
            if not maintain_folders(file, delete_main_files, delete_sub_files, False):
                empty = False
        else:
            if (delete_sub_files and not root) or (delete_main_files and root):
                os.remvove(file)
            else:
                empty = False
    return empty and not root and os.rmdir(path)


def check_media_path(filename):
    media_path = get_config("media_path")
    if os.path.realpath(
        os.path.dirname(f"{media_path}/{filename}")
    ) == os.path.realpath(media_path):
        return file_exists(f"{media_path}/{filename}")


def disk_usage():
    media_path = get_config("media_path")
    total, used, free = shutil.disk_usage(f"{media_path}")
    percent_used = round((total - used) / total * 100, 1)
    if percent_used > 98:
        colour = "Red"
    elif percent_used > 90:
        colour = "Orange"
    else:
        colour = "LightGreen"

    return (
        round(total / 1048576),
        round(used / 1048576),
        round(free / 1048576),
        int(percent_used),
        colour,
    )


def get_thumbnails(sort_order, show_types, time_filter, time_filter_max):
    media_path = get_config("media_path")
    files = list_folder_files(media_path)
    thumbnails = {}
    for file in files:
        file_timestamp = os.path.getmtime(f"{media_path}/{file}")
        if time_filter == 1:
            include = True
        else:
            time_delta = dt.now().timestamp() - file_timestamp
            if time_filter == time_filter_max:
                include = time_delta >= (86400 * (time_filter - 2))
            else:
                include = time_delta >= (86400 * (time_filter - 2)) and (
                    time_delta < ((time_filter - 1) * 86400)
                )
        if include:
            file_type = get_file_type(file)
            if (
                show_types == 1
                or (  # noqa: W503
                    show_types == 2 and (file_type == "i" or file_type == "t")
                )
                or (show_types == 3 and file_type == "v")  # noqa: W503
            ):
                thumbnails[file] = f"{file_type}_{file_timestamp}"

    if sort_order == 1:
        thumbnails = dict(sorted(thumbnails.items()))
    else:
        thumbnails = dict(sorted(thumbnails.items(), reverse=True))

    return list(thumbnails.keys())


def draw_files(filesnames: list):
    media_path = get_config("media_path")
    thumbnails = []
    for file in filesnames:
        file_type = get_file_type(file)
        real_file = data_filename(file)
        f_number = get_file_index(file)
        lapse_count = 0
        match file_type:
            case "v":
                file_icon = "bi-camera-reels"
            case "t":
                file_icon = "bi-images"
                lapse_count = f"({find_lapse_files(file)})"
            case "i":
                file_icon = "bi-camera"
            case _:
                file_icon = "bi-camera"
        duration = 0
        if file_exists(f"{media_path}/{real_file}"):
            file_size = round(filesize_n(f"{media_path}/{real_file}") / 1024)
            file_timestamp = os.path.getmtime(f"{media_path}/{real_file}")
            if file_type == "v":
                duration = file_timestamp - os.path.getmtime(f"{media_path}/{file}")
        else:
            file_size = 0
            file_timestamp = os.path.getmtime(f"{media_path}/{file}")

        if file_type:
            file_datetime = dt.fromtimestamp(file_timestamp)
            thumbnails.append(
                {
                    "file_name": file,
                    "file_type": file_type,
                    "file_size": file_size,
                    "file_icon": file_icon,
                    "file_datetime": file_datetime,
                    "real_file": real_file,
                    "file_number": f_number,
                    "lapse_count": lapse_count,
                    "duration": duration,
                }
            )

    return thumbnails


def gather_img(pDelay=0.1):
    """Stream image."""
    while True:
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + get_shm_cam() + b"\r\n")
        time.sleep(pDelay)
        # cam_jpg = get_shm_cam()
        # _, frame = cv2.imencode(".jpg", cam_jpg)
        # img = Image.open("/dev/shm/mjpeg/cam.jpg")
        # yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + img.tobytes() + b"\r\n")


def is_day_active(days, period: int) -> bool:
    if days:
        day = dt.now().strftime("%w")
        return int(day) in days[str(period)]
    return False
