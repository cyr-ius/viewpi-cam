"""Blueprint preview."""
import os
import shutil
import time
import zipfile
from datetime import datetime as dt
from io import BytesIO
from subprocess import PIPE, Popen

from flask import Blueprint
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
from ..helpers.utils import disk_usage, write_log
from ..helpers.preview import get_thumbinfo, thumbs

bp = Blueprint("preview", __name__, template_folder="templates", url_prefix="/preview")


@bp.route("/", methods=["GET", "POST"])
@auth_required
def index():
    """Index page."""
    media_path = ca.raspiconfig.media_path
    time_filter_max = 8
    select_all = ""

    preview_size = int(request.cookies.get("preview_size", 640))
    thumb_size = int(request.cookies.get("thumb_size", 96))
    sort_order = int(request.cookies.get("sort_order", 1))
    show_types = int(request.cookies.get("show_types", 1))
    time_filter = int(request.cookies.get("time_filter", 1))
    preview_id = request.args.get("preview", "")

    if request.method == "POST":
        time_filter = int(request.json.get("time_filter", time_filter))
        sort_order = int(request.json.get("sort_order", sort_order))
        show_types = int(request.json.get("show_types", show_types))

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

    thumbnails = thumbs(
        sort_order=sort_order,
        show_types=show_types,
        time_filter=time_filter,
        time_filter_max=time_filter_max,
    )

    response = make_response(
        render_template(
            "preview.html",
            raspiconfig=ca.raspiconfig,
            disk_usage=disk_usage(),
            preview_size=preview_size,
            thumb_size=thumb_size,
            sort_order=sort_order,
            show_types=show_types,
            time_filter=time_filter,
            time_filter_max=time_filter_max,
            preview_id=preview_id,
            thumbnails=thumbnails,
            select_all=select_all,
        )
    )

    if request.method == "POST":
        response.set_cookie("time_filter", str(time_filter))
        response.set_cookie("sort_order", str(sort_order))
        response.set_cookie("show_types", str(show_types))
        response.set_cookie("preview_size", str(preview_size))
        response.set_cookie("thumb_size", str(thumb_size))

    return response


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
            thumb = get_thumbinfo(uid)
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


def video_convert(filename: str):
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
            rst = cmd.replace(f"i_{i:05d}", f"tmp/i_{i:05d}")
            cmd = f"({rst} {media_path}/{video_file}; rm -rf {tmp};) >/dev/null 2>&1 &"
            write_log(f"start lapse convert: {cmd}")
            Popen(cmd, stdout=PIPE, shell=True)
            shutil.copy(
                src=f"{media_path}/{filename}",
                dst=f"{media_path}/{video_file}.v{file_index}{ca.config['THUMBNAIL_EXT']}",
            )
            write_log("Convert finished")


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
    """Return thumbnails and extra informations."""
    media_path = ca.raspiconfig.media_path
    thumbnails = []
    for file in filesnames:
        file_type = get_file_type(file)
        real_file = data_file_name(file)
        f_number = get_file_index(file)
        lapse_count = 0
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
        duration = 0
        file_size = 0
        file_right = 1
        if os.path.isfile(f"{media_path}/{real_file}"):
            file_size = round(get_file_size(f"{media_path}/{real_file}") / 1024)
            file_timestamp = os.path.getmtime(f"{media_path}/{real_file}")
            try:
                file_right = os.access(f"{media_path}/{real_file}", os.W_OK)
                ca.logger.debug(f"File Right {file_right}")
            except UnboundLocalError:
                file_right = 0
            if file_type == "v":
                duration = round(
                    os.path.getmtime(f"{media_path}/{file}") - file_timestamp
                )
        else:
            file_timestamp = os.path.getmtime(f"{media_path}/{file}")

        if file_type:
            thumbnails.append(
                {
                    "id": real_file[:-4].replace("_", ""),
                    "file_name": file,
                    "file_type": file_type,
                    "file_size": file_size,
                    "file_icon": file_icon,
                    "file_datetime": dt.fromtimestamp(file_timestamp),
                    "file_right": file_right,
                    "real_file": real_file,
                    "file_number": f_number,
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
