"""Helper functions."""
import os
import shutil
from datetime import datetime as dt
from functools import reduce

from flask import current_app
from psutil import process_iter


def get_pid(pid_type):
    """Return process id."""
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
    """Return lapse files."""
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
            if (
                (not is_thumbnail(file))
                and (ext := get_file_ext(file))
                and ext == "jpg"
            ):
                f_date = os.path.getmtime(f"{media_path}/{file}").hour()
                if f_date >= start:
                    files[file] = f_date + file
    files.sort()
    lapse_count = 1
    for key in files:
        if key[lapse_count.zfile(padlen) :]:  # noqa: E203
            lapsefiles.append(f"{path}/{key}")
            lapse_count += 1
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


def delete_mediafiles(filename, delete=True):
    """Delete all files associated with a thumb name."""
    media_path = current_app.raspiconfig.media_path
    size = 0
    type_file = get_file_type(filename)

    if type_file == "t":
        #  For time lapse try to delete all from this batch
        files = find_lapse_files(filename)
        for file in files:
            size += filesize_n(f"{media_path}/{file}")
            if delete:
                os.remove(f"{media_path}/{file}")
    else:
        thumb_file = data_filename(filename)

        def compute_delete_file(filename, size, delete=True):
            if os.path.isfile(filename):
                size += filesize_n(filename)
                if delete:
                    os.remove(filename)

        compute_delete_file(f"{media_path}/{thumb_file}", size)

        if type_file == "v":
            raw_file = thumb_file[: thumb_file.find(".")]
            for filename in (
                f"{media_path}/{thumb_file}.dat",
                f"{media_path}/{raw_file}.h264",
                f"{media_path}/{raw_file}.h264.bad",
                f"{media_path}/{raw_file}.h264.log",
            ):
                compute_delete_file(filename, size)

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


def data_file_ext(file: str):
    """Return real filename."""
    file = data_filename(file)
    return get_file_ext(file)


def get_file_ext(file: str):
    """Return extension file."""
    _, ext = os.path.splitext(file)
    return ext


# Support naming functions
def is_thumbnail(file: str) -> bool:
    """Return is thumbnail file."""
    return file[-7:] == current_app.config["THUMBNAIL_EXT"]


def get_file_type(file: str):
    """Return type file."""
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[i + 1]
    return ""


def get_file_index(file: str):
    """Return index file."""
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[i + 2 : len(file) - i - 9]  # noqa: E203
    return ""


def file_add_content(filename: str, data: str) -> None:
    """Add data in file , create if not exist."""
    mode = "w" if not os.path.isfile(filename) else "a"
    with open(filename, mode=mode, encoding="utf-8") as file:
        file.write(data)


# def execute_cmd(cmd):
#     return os.popen(cmd)


def write_log(msg: str) -> None:
    """Write log."""
    log_file = current_app.raspiconfig.log_file
    str_now = dt.now().strftime("%Y/%m/%D %H:%M:%S")
    current_app.logger.info(msg)
    file_add_content(log_file, f"{str_now} {msg}\n")


def delete_log(log_size: int) -> None:
    """Delete log."""
    log_file = current_app.raspiconfig.log_file
    if os.path.isfile(log_file):
        log_lines = open(log_file, mode="r", encoding="utf-8").readlines()
        if len(log_lines) > log_size:
            with open(log_file, mode="w", encoding="utf-8") as file:
                file.write(log_lines[:log_size])
                file.close()


def write_debug_log(msg: str) -> None:
    """Write debug log."""
    log_file = current_app.config["LOGFILE_DEBUG"]
    str_now = dt.now().strftime("%Y/%m/%D %H:%M:%S")
    current_app.logger.debug(msg)
    file_add_content(log_file, f"{str_now} {msg}\n")


def list_folder_files(path: str, ext=None) -> list:
    """List files in folder path."""
    if ext:
        return [
            f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f)) and f".{ext}" in f
        ]
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]


def send_pipe(pipename: str, cmd: str) -> None:
    """Send command to pipe."""
    try:
        pipe = os.open(pipename, os.O_WRONLY | os.O_NONBLOCK)
        os.write(pipe, f"{cmd}\n".encode("utf-8"))
        os.close(pipe)
        current_app.raspiconfig.refresh()
        write_log(f"{pipename} - send {cmd}")
        return {"type": "success", "message": f"Send {cmd} successful"}
    except Exception as error:  # pylint: disable=W0718
        write_log(str(error))
        return {"type": "error", "message": f"{error}"}


def disk_usage() -> tuple[int, int, int, int, str]:
    """Disk usage."""
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
