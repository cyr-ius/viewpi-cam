import os
import shutil
from datetime import datetime as dt

from flask import abort
from flask import current_app as ca

from ..helpers.exceptions import ViewPiCamException
from ..helpers.filer import (
    data_file_name,
    find_lapse_files,
    get_file_index,
    get_file_type,
)
from ..helpers.utils import execute_cmd, write_log
from ..models import Files, db


def video_convert(filename: str) -> None:
    media_path = ca.raspiconfig.media_path
    if check_media_path(filename):
        file_type = get_file_type(filename)
        file_index = get_file_index(filename)

        if file_type == "t" and isinstance(int(file_index), int):
            thumb_files = find_lapse_files(filename)
            tmp = f"{media_path}/{file_type}{file_index}"
            if not os.path.isdir(tmp):
                os.makedirs(tmp, 0o744, True)

            i = 0
            for thumb in thumb_files:
                os.symlink(thumb, f"{tmp}/i_{i:05d}.jpg")
                i += 1

            i = 0
            video_file = f"{data_file_name(filename)[:-4]}.mp4"
            cmd = ca.config["CONVERT_CMD"]
            ext = ca.config["THUMBNAIL_EXT"]
            rst = cmd.replace(f"i_{i:05d}", f"tmp/i_{i:05d}")
            cmd = f"({rst} {media_path}/{video_file}; rm -rf {tmp};) >/dev/null 2>&1 &"
            try:
                write_log(f"Start lapse convert: {cmd}")
                execute_cmd(cmd)
                shutil.copy(
                    src=f"{media_path}/{filename}",
                    dst=f"{media_path}/{video_file}.v{file_index}{ext}",
                )
                write_log("Convert finished")
            except ViewPiCamException as error:
                write_log(f"[Convert] {str(error)}", "error")


def get_thumbs(sort_order: str, show_types: str, time_filter: int):
    """Return thumbnails from database."""
    order = Files.datetime.desc() if sort_order == "desc" else Files.datetime.asc()
    match show_types:
        case "both":
            show_types = ["i", "t", "v"]
        case "image":
            show_types = ["i", "t"]
        case _:
            show_types = ["v"]

    if (time_filter := int(time_filter)) == 1:
        files = db.session.scalars(
            db.select(Files).filter(Files.type.in_(show_types)).order_by(order)
        )
    elif time_filter == ca.config.get("TIME_FILTER_MAX"):
        dt_search = dt.fromtimestamp(dt.now().timestamp() - (86400 * (time_filter - 2)))
        files = db.session.scalars(
            db.select(Files)
            .filter(Files.type.in_(show_types), Files.datetime <= dt_search)
            .order_by(order)
        )
    else:
        dt_lw = dt.fromtimestamp(dt.now().timestamp() - (86400 * (time_filter - 2)))
        dt_gt = dt.fromtimestamp(dt.now().timestamp() - (time_filter - 1) * 86400)
        files = db.session.scalars(
            db.select(Files)
            .filter(
                Files.type.in_(show_types),
                Files.datetime < dt_lw,
                Files.datetime >= dt_gt,
            )
            .order_by(order)
        )

    return files.all()


def check_media_path(filename):
    """Check file if exists to media path."""
    media_path = ca.raspiconfig.media_path
    if os.path.realpath(
        os.path.dirname(f"{media_path}/{filename}")
    ) == os.path.realpath(media_path):
        fullpath = os.path.normpath(os.path.join(media_path, filename))
        if not fullpath.startswith(media_path):
            abort(500, "Media ath not allowed")

        return os.path.isfile(fullpath)
