"""Blueprint preview."""
import os
import shutil
import time
import zipfile
from datetime import datetime as dt
from io import BytesIO
from typing import Any

from flask import Blueprint, config
from flask import current_app as ca
from flask import make_response, render_template, request, send_file

from ..helpers.decorator import auth_required
from ..helpers.filer import (
    data_file_ext,
    data_file_name,
    find_lapse_files,
    get_file_index,
    get_file_size,
    get_file_type,
    list_folder_files,
)
from ..helpers.utils import disk_usage, execute_cmd, write_log
from ..services.handle import ViewPiCamException

bp = Blueprint("preview", __name__, template_folder="templates", url_prefix="/preview")


@bp.route("/", methods=["GET"])
@auth_required
def index():
    """Index page."""
    time_filter_max = config["TIME_FILTER_MAX"]
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

            return send_file(
                f"{media_path}/{dx_file}",
                mimetype=mimetype,
                as_attachment=True,
                download_name=dx_file,
            )
        else:
            return get_zip([filename])


@bp.route("/zipfile", methods=["POST"])
@auth_required
def zipdata():
    """ZIP File."""
    check_list = request.json.get("check_list", [])
    if isinstance(check_list, str):
        check_list = [request.json["check_list"]]
    if check_list:
        zip_list = []
        for uid in check_list:
            thumb = get_thumbnails_id(uid)
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


def get_thumbnails(sort_order, show_types, time_filter, time_filter_max):
    """Return files."""
    media_path = ca.raspiconfig.media_path
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
                (show_types == "both" and (file_type in ["i", "t", "v"]))
                or (show_types == "image" and (file_type in ["i", "t"]))
                or (show_types == "video" and file_type == "v")
            ):
                thumbnails[file] = f"{file_type}_{file_timestamp}"

    if sort_order == "asc":
        thumbnails = dict(sorted(thumbnails.items()))
    else:
        thumbnails = dict(sorted(thumbnails.items(), reverse=True))

    return list(thumbnails.keys())


def draw_files(filesnames: list):
    """Return thumbnails and extra informations."""
    media_path = ca.raspiconfig.media_path
    thumbnails = []
    for file in filesnames:
        file_type = get_file_type(file)
        real_file = data_file_name(file)
        file_id = real_file[:-4].replace("_", "")
        file_number = get_file_index(file)
        file_lock = file_id in ca.settings.get("lock_files", [])
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
            file_timestamp = os.path.getmtime(f"{media_path}/{real_file}")
            if file_type == "v":
                duration = round(
                    os.path.getmtime(f"{media_path}/{file}") - file_timestamp
                )
        else:
            file_timestamp = os.path.getmtime(f"{media_path}/{file}")

        if file_type:
            thumbnails.append(
                {
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
            )

    ca.logger.debug(f"Thumbnails: {thumbnails}")
    return thumbnails


def check_media_path(filename):
    """Check file if existe media path."""
    media_path = ca.raspiconfig.media_path
    if os.path.realpath(
        os.path.dirname(f"{media_path}/{filename}")
    ) == os.path.realpath(media_path):
        return os.path.isfile(f"{media_path}/{filename}")


def thumbs(
    sort_order: bool = False,
    show_types: bool = True,
    time_filter: int = 1,
    time_filter_max: int = 8,
) -> dict[str, Any]:
    """Get details files infos."""
    thumb_filenames = get_thumbnails(
        sort_order=sort_order,
        show_types=show_types,
        time_filter=time_filter,
        time_filter_max=time_filter_max,
    )
    return draw_files(thumb_filenames)


def get_thumbnails_id(uid: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
    """Get file name and real name."""
    media_path = ca.raspiconfig.media_path
    files = list_folder_files(media_path)
    thumbnails = []
    for file in files:
        real_file = data_file_name(file)
        file_id = real_file[:-4].replace("_", "")
        if real_file:
            thumb = {"id": file_id, "real_file": real_file, "file_name": file}
            if uid and uid == file_id:
                return thumb
            thumbnails.append(thumb)
    return thumbnails
