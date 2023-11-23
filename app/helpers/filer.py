"""Files functions."""
import os
import subprocess
from datetime import datetime as dt

from flask import current_app as ca


def find_lapse_files(filename: str) -> list[str]:
    """Return lapse files."""
    media_path = ca.raspiconfig.media_path
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


def delete_mediafiles(filename: str, delete: bool = True) -> int:
    """Delete all files associated with a thumb name."""
    media_path = ca.raspiconfig.media_path
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

    return round(size / 1024)


def data_file_name(file: str) -> str:
    """Return real filename."""
    subdir_char = ca.raspiconfig.subdir_char
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[:i].replace(subdir_char, "/")
    return ""


def data_file_ext(file: str) -> str:
    """Return real filename extension."""
    file = data_file_name(file)
    return get_file_ext(file)


def is_thumbnail(file: str) -> bool:
    """Return is thumbnail file."""
    return file[-7:] == ca.config["THUMBNAIL_EXT"]


def get_file_size(path) -> int:
    """Return file size."""
    if ca.config["FILESIZE_METHOD"] == 0:
        return os.path.getsize(path)
    return f"stat -c%s {path}".strip()


def get_file_ext(file: str) -> str:
    """Return extension file."""
    _, ext = os.path.splitext(file)
    return ext[1:]


def get_file_type(file: str) -> str:
    """Return type file."""
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[i + 1]
    return ""


def get_file_duration(file: str) -> int:
    """Return duration mp4."""
    if get_file_ext(file) == "mp4":
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return float(result.stdout)
    return 0


def get_file_index(file: str) -> str:
    """Return index file."""
    i = file.rfind(".", 0, len(file) - 8)
    if i > 0:
        return file[i + 2 : len(file) - 7]  # noqa: E203
    return ""


def get_file_timestamp(file: str) -> dt:
    """Return timestamp."""
    ext = (len(get_file_ext(file)) + 1) * -1
    sdatetime = file[:ext][-15:].replace("_", "")
    return dt.strptime(sdatetime, "%Y%m%d%H%M%S").timestamp()


def list_folder_files(path: str, ext=None) -> list[str]:
    """List files in folder path."""
    if ext:
        return [
            f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f)) and f".{ext}" in f
        ]
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]


def get_sorted_files(folder: str, ascending: bool = True) -> list[str]:
    """Ordering files."""
    files = {}
    for file in list_folder_files(folder):
        if file != "." and file != ".." and is_thumbnail(file):
            files[file] = os.path.getmtime(f"{folder}/{file}")

    return sorted(files, reverse=ascending is False)


def maintain_folders(
    path, delete_main_files, delete_sub_files, root: bool = True
) -> bool:
    """Sanatize media folders."""
    empty = True
    for folder in list_folder_files(path):
        if os.path.isdir(folder):
            if not maintain_folders(folder, delete_main_files, delete_sub_files, False):
                empty = False
        else:
            if (delete_sub_files and not root) or (delete_main_files and root):
                os.remove(folder)
            else:
                empty = False
    return empty and not root and os.rmdir(path)


def lock_file(filename: str, id: str, lock: bool) -> None:  # pylint: disable=W0622
    """Lock file (remove w via chmod)."""
    media_path = ca.raspiconfig.media_path
    lock_files = ca.settings.get("lock_files", [])
    if lock == 1:
        attr = 0o444
        lock_files.append(id)
    else:
        attr = 0o644
        if id in lock_files:
            lock_files.remove(id)
    ca.settings.update(lock_files=lock_files)
    file_type = get_file_type(filename)
    if file_type == "t":
        #  For time lapse lock all from this batch
        files = find_lapse_files(filename)
        for file in files:
            os.chmod(file, attr)
    else:
        thumb_file = data_file_name(filename)
        if os.path.isfile(f"{media_path}/{thumb_file}"):
            os.chmod(f"{media_path}/{thumb_file}", attr)
        if file_type == "v" and os.path.isfile(f"{media_path}/{thumb_file}.dat"):
            os.chmod(f"{media_path}/{thumb_file}.dat", attr)
        if file_type == "v" and os.path.isfile(f"{media_path}/{thumb_file}.h264"):
            os.chmod(f"{media_path}/{thumb_file}.h264", attr)

    os.chmod(f"{media_path}/{filename}", attr)
