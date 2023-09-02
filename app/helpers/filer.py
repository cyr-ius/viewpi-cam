import os
import shutil
from datetime import datetime as dt
from functools import reduce

from flask import current_app
from psutil import process_iter


def get_pid(pid_type):
    for proc in process_iter():
        if pid_type == "scheduler":
            if "flask" and "scheduler" in proc.cmdline():
                return proc.pid
        if pid_type in proc.cmdline():
            return proc.pid
    return 0


def getr(data, keys, default: any = None) -> any:
    """Return value of dict from get recursive key."""
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        data,
    )


# functions to find and delete data files
def find_lapse_files(filename):
    media_path = current_app.raspiconfig.media_path

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
    media_path = current_app.raspiconfig.media_path
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

        def compute_delete_file(filename, size, delete=True):
            if os.path.isfile(filename):
                size += filesize_n(filename)
                if delete:
                    os.remove(filename)

        compute_delete_file(f"{media_path}/{tFile}")
        # if os.path.isfile(f"{media_path}/{tFile}"):
        #     size += filesize_n(f"{media_path}/{tFile}")
        #     if delete:
        #         os.remove(f"{media_path}/{tFile}")

        if t == "v":
            rFile = tFile[: tFile.find(".")]
            for filename in (
                f"{media_path}/{tFile}.dat",
                f"{media_path}/{rFile}.h264",
                f"{media_path}/{rFile}.h264.bad",
                f"{media_path}/{rFile}.h264.log",
            ):
                compute_delete_file(filename)
            # if os.path.isfile(f"{media_path}/{tFile}.dat"):
            #     size += filesize_n(f"{media_path}/{tFile}.dat")
            #     if delete:
            #         os.remove(f"{media_path}/{tFile}.dat")

            # if os.path.isfile(f"{media_path}/{rFile}.h264"):
            #     size += filesize_n(f"{media_path}/{rFile}.h264")
            #     if delete:
            #         os.remove(f"{media_path}/{rFile}.h264")

            # if os.path.isfile(f"{media_path}/{rFile}.h264.bad"):
            #     size += filesize_n(f"{media_path}/{rFile}.h264.bad")
            #     if delete:
            #         os.remove(f"{media_path}/{rFile}.h264.bad")

            # if os.path.isfile(f"{media_path}/{rFile}.h264.log"):
            #     size += filesize_n(f"{media_path}/{rFile}.h264.log")
            #     if delete:
            #         os.remove(f"{media_path}/{rFile}.h264.log")

    size += filesize_n(f"{media_path}/{filename}")
    if delete:
        os.remove(f"{media_path}/{filename}")
    return size / 1024


# Support naming functions
def data_filename(file):
    subdir_char = current_app.raspiconfig.subdir_char
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[:i].replace(subdir_char, "/")
    return ""


def data_file_ext(file):
    """Return real filename."""
    f = data_filename(file)
    return get_file_ext(f)


def get_file_ext(file):
    """Return extension file."""
    _, ext = os.path.splitext(file)
    return ext


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


def file_add_content(filename, data):
    mode = "w" if not file_exists(filename) else "a"
    with open(filename, mode) as f:
        f.write(data)
        f.close


# def execute_cmd(cmd):
#     return os.popen(cmd)


def write_log(msg):
    log_file = current_app.raspiconfig.log_file
    str_now = dt.now().strftime("%Y/%m/%D %H:%M:%S")
    current_app.logger.info(msg)
    file_add_content(log_file, f"{str_now} {msg}\n")


def delete_log(log_size):
    log_file = current_app.raspiconfig.log_file
    if file_exists(log_file):
        log_lines = open(log_file, "r").readlines()
        if len(log_lines) > log_size:
            with open(log_file, "w") as f:
                f.write(log_lines[:log_size])
                f.close()


def write_debug_log(msg):
    log_file = current_app.config["LOGFILE_DEBUG"]
    str_now = dt.now().strftime("%Y/%m/%D %H:%M:%S")
    current_app.logger.debug(msg)
    file_add_content(log_file, f"{str_now} {msg}\n")


def list_folder_files(path: str, ext=None):
    if ext:
        return [
            f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f)) and f".{ext}" in f
        ]
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]


def send_pipe(pipename: str, cmd: str):
    if not os.path.exists(pipename):
        write_log(f"Making Pipe {pipename}")
        os.popen(f"mkfifo {pipename}")
        os.popen(f"chmod 666 {pipename}")
    try:
        pipe = os.open(pipename, os.O_WRONLY | os.O_NONBLOCK)
        os.write(pipe, f"{cmd}\n".encode("utf-8"))
        os.close(pipe)
        current_app.raspiconfig.refresh()
        write_log(f"Send {cmd}")
        return {"type": "success", "message": f"Send {cmd} successful"}
    except Exception as error:
        write_log(str(error))
        return {"type": "error", "message": f"{error}"}


def disk_usage():
    media_path = current_app.raspiconfig.media_path
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
