"""Blueprint preview."""

import os
import shutil
import time
import zipfile
from datetime import datetime as dt
from io import BytesIO
from typing import Any

from flask import Blueprint, abort, make_response, render_template, request, send_file
from flask import current_app as ca

from ..helpers.decorator import auth_required, role_required
from ..helpers.filer import (
    data_file_ext,
    data_file_name,
    find_lapse_files,
    get_file_duration,
    get_file_index,
    get_file_size,
    get_file_timestamp,
    get_file_type,
    list_folder_files,
)
from ..helpers.utils import disk_usage, execute_cmd, write_log
from ..helpers.exceptions import ViewPiCamException
from ..models import LockFiles

bp = Blueprint("preview", __name__, template_folder="templates", url_prefix="/preview")


@bp.route("/", methods=["GET"])
@auth_required
@role_required(["preview", "medium", "max"])
def index():
    """Index page."""
    time_filter_max = ca.config["TIME_FILTER_MAX"]
    preview_id = request.args.get("preview", "")
    show_types = request.cookies.get("show_types", "both")
    sort_order = request.cookies.get("sort_order", "desc")
    time_filter = int(request.cookies.get("time_filter", 1))

    response = make_response(
        render_template(
            "preview.html",
            disk_usage=disk_usage(),
            preview_id=preview_id,
            raspiconfig=ca.raspiconfig,
            show_types=show_types,
            sort_order=sort_order,
            time_filter_max=time_filter_max,
            time_filter=time_filter,
        )
    )

    return response


@bp.route("/download", methods=["POST"])
@role_required(["preview", "medium", "max"])
@auth_required
def download():
    """Download File."""
    media_path = ca.raspiconfig.media_path
    if (filename := request.json.get("filename")) and check_media_path(filename):
        if get_file_type(filename) != "t":
            dx_file = data_file_name(filename)
            if data_file_ext(filename) == "jpg":
                mimetype = "image/jpeg"
            else:
                mimetype = "video/mp4"

            fullpath = os.path.normpath(os.path.join(media_path, dx_file))
            if not fullpath.startswith(media_path):
                abort(500, "Download not allowed")

            return send_file(
                fullpath, mimetype=mimetype, as_attachment=True, download_name=dx_file
            )
        else:
            return get_zip([filename])


@bp.route("/zipfile", methods=["POST"])
@role_required(["preview", "medium", "max"])
@auth_required
def zipdata():
    """ZIP File."""
    check_list = request.json.get("check_list", [])
    if isinstance(check_list, str):
        check_list = [request.json["check_list"]]
    if check_list:
        zip_list = []
        for id in check_list:
            thumb = get_thumb(id)
            zip_list.append(thumb["file_name"])

        return get_zip(zip_list)


def get_zip(files: list):
    """Zip files."""
    media_path = ca.raspiconfig.media_path
    date_str = dt.now().strftime("%Y%m%d_%H%M%S")
    zipname = f"cam_{date_str}.zip"

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, "a") as zip_file:
        for file in files:
            file_name = data_file_name(file)
            try:
                data = zipfile.ZipInfo(file_name)
                data.date_time = time.localtime(time.time())[:6]
                data.compress_type = zipfile.ZIP_DEFLATED
                zip_file.write(
                    f"{media_path}/{file_name}", file_name, data.compress_type
                )
            except FileNotFoundError:
                continue
    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zipname,
    )


def get_thumbnails(
    sort_order: str = "asc",
    show_types: str = "both",
    time_filter: int = 1,
    time_filter_max: int = 8,
):
    """Return thumbnails and extra information."""
    media_path = ca.raspiconfig.media_path
    select_thumbs = {}
    thumbnails = []
    for file in list_folder_files(media_path):
        file_type = get_file_type(file)
        real_file = data_file_name(file)
        file_id = real_file[:-4].replace("_", "")
        file_number = get_file_index(file)
        file_lock = LockFiles.query.get(file_id) is not None
        file_size = 0
        lapse_count = 0
        duration = 0

        match file_type:
            case "v":
                file_icon = "bi-camera-reels"
            case "t":
                file_icon = "bi-images"
                lapse_count = len(find_lapse_files(file))
            case "i":
                file_icon = "bi-camera"
            case _:
                file_icon = "bi-camera"
        if os.path.isfile(f"{media_path}/{real_file}"):
            file_size = round(get_file_size(f"{media_path}/{real_file}") / 1024)
            file_timestamp = get_file_timestamp(real_file)
            if file_type == "v":
                duration = get_file_duration(f"{media_path}/{real_file}")
        else:
            file_timestamp = (
                get_file_timestamp(real_file)
                if real_file != ""
                else get_file_timestamp(file)
            )

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

        if include and file_type:
            if (
                (show_types == "both" and (file_type in ["v", "i", "t"]))
                or (show_types == "image" and (file_type in ["i", "t"]))
                or (show_types == "video" and file_type == "v")
            ):
                select_thumbs.update(
                    {
                        file_timestamp: {
                            "id": file_id,
                            "file_name": file,
                            "file_type": file_type,
                            "file_size": file_size,
                            "file_icon": file_icon,
                            "file_datetime": dt.fromtimestamp(file_timestamp),
                            "file_lock": file_lock,
                            "real_file": real_file,
                            "file_number": file_number,
                            "lapse_count": lapse_count,
                            "duration": duration,
                        }
                    }
                )

    if sort_order == "asc":
        select_thumbs = dict(sorted(select_thumbs.items()))
    else:
        select_thumbs = dict(sorted(select_thumbs.items(), reverse=True))

    thumbnails = list(select_thumbs.values())

    return thumbnails


def get_thumb(
    id: str | None = None,  # pylint: disable=W0622
) -> dict[str, Any] | list[dict[str, Any]]:
    """Get file name and real name."""
    for thumb in get_thumbnails():
        if thumb["id"] == id:
            return thumb


def check_media_path(filename):
    """Check file if existe media path."""
    media_path = ca.raspiconfig.media_path
    if os.path.realpath(
        os.path.dirname(f"{media_path}/{filename}")
    ) == os.path.realpath(media_path):
        fullpath = os.path.normpath(os.path.join(media_path, filename))
        if not fullpath.startswith(media_path):
            abort(500, "Media ath not allowed")

        return os.path.isfile(fullpath)


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
                write_log(f"Error converting ({error})")
