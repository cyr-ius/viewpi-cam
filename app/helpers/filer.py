"""Helper functions."""
import os
import shutil
from datetime import datetime as dt
from subprocess import PIPE, Popen

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


def find_lapse_files(filename):
    """Return lapse files."""
    media_path = current_app.raspiconfig.media_path
    files = {}
    lapsefiles = []

    batch = get_file_index(filename)
    padlen = len(batch)
    fullname = f"{media_path}/{data_file_name(filename)}"
    if not os.path.isfile(fullname):
        return lapsefiles
    start = os.path.getmtime(fullname)
    scanfiles = list_folder_files(f"{media_path}")
    for file in scanfiles:
        if file.find(batch):
            if (
                (not is_thumbnail(file))
                and (ext := get_file_ext(file))
                and ext == "jpg"
            ):
                f_date = os.path.getmtime(f"{media_path}/{file}")
                if f_date >= start:
                    files[file] = str(f_date) + file

    lapse_count = 1
    for key in sorted(files):
        if key[int(str(lapse_count).zfill(padlen)) :]:  # noqa: E203
            lapsefiles.append(f"{media_path}/{key}")
            lapse_count += 1
        else:
            break
    return lapsefiles


def delete_mediafiles(filename, delete=True):
    """Delete all files associated with a thumb name."""
    media_path = current_app.raspiconfig.media_path
    size = 0
    type_file = get_file_type(filename)

    def compute_delete_file(file_name, size, delete):
        if os.path.isfile(file_name):
            size += get_file_size(file_name)
            if delete:
                os.remove(file_name)

    if type_file == "t":
        #  For time lapse try to delete all from this batch
        files = find_lapse_files(filename)
        for file in files:
            compute_delete_file(file, size, delete)
    else:
        thumb_file = data_file_name(filename)
        compute_delete_file(f"{media_path}/{thumb_file}", size, delete)

        if type_file == "v":
            raw_file = thumb_file[: thumb_file.find(".")]
            for file in (
                f"{media_path}/{thumb_file}.dat",
                f"{media_path}/{raw_file}.h264",
                f"{media_path}/{raw_file}.h264.bad",
                f"{media_path}/{raw_file}.h264.log",
            ):
                compute_delete_file(file, size, delete)

    compute_delete_file(f"{media_path}/{filename}", size, delete)

    return size / 1024


def data_file_name(file):
    """Return real filename."""
    subdir_char = current_app.raspiconfig.subdir_char
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[:i].replace(subdir_char, "/")
    return ""


def data_file_ext(file: str):
    """Return real filename extension."""
    file = data_file_name(file)
    return get_file_ext(file)


# Support naming functions
def is_thumbnail(file: str) -> bool:
    """Return is thumbnail file."""
    return file[-7:] == current_app.config["THUMBNAIL_EXT"]


def get_file_size(path):
    """Return file size."""
    if current_app.config["FILESIZE_METHOD"] == 0:
        return os.path.getsize(path)
    return f"stat -c%s {path}".strip()


def get_file_ext(file: str):
    """Return extension file."""
    _, ext = os.path.splitext(file)
    return ext[1:]


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
        return file[i + 2 : len(file) - 7]  # noqa: E203
    return ""


def execute_cmd(cmd):
    """Execute shell command."""
    return Popen(cmd, stdout=PIPE, shell=True)


def write_log(msg: str) -> None:
    """Write log."""
    log_file = current_app.raspiconfig.log_file
    str_now = dt.now().strftime("%Y/%m/%d %H:%M:%S")
    current_app.logger.info(msg)

    mode = "w" if not os.path.isfile(log_file) else "a"
    with open(log_file, mode=mode, encoding="utf-8") as file:
        file.write(f"{{{str_now}}} {msg}\n")


def delete_log(log_size: int) -> None:
    """Delete log."""
    log_file = current_app.raspiconfig.log_file
    if os.path.isfile(log_file):
        log_lines = open(log_file, mode="r", encoding="utf-8").readlines()
        if len(log_lines) > log_size:
            with open(log_file, mode="w", encoding="utf-8") as file:
                file.write(log_lines[:log_size])
                file.close()


def list_folder_files(path: str, ext=None) -> list:
    """List files in folder path."""
    if ext:
        return [
            f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f)) and f".{ext}" in f
        ]
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]


def disk_usage() -> tuple[int, int, int, int, str]:
    """Disk usage."""
    media_path = current_app.raspiconfig.media_path
    total, used, free = shutil.disk_usage(f"{media_path}")
    percent_used = round(used / total * 100)
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
