"""Blueprint preview."""

import os
import shutil
import time
import zipfile
from datetime import datetime as dt
from io import BytesIO

from flask import (
    Blueprint,
    abort,
    make_response,
    render_template,
    request,
    send_file,
)
from flask import current_app as ca
from flask_login import login_required

from ..helpers.database import update_img_db
from ..helpers.decorator import role_required
from ..helpers.exceptions import ViewPiCamException
from ..helpers.filer import (
    data_file_ext,
    data_file_name,
    find_lapse_files,
    get_file_index,
    get_file_type,
)
from ..helpers.utils import disk_usage, execute_cmd, write_log
from ..models import Files as files_db

bp = Blueprint("preview", __name__, template_folder="templates", url_prefix="/preview")


@bp.route("/", methods=["GET"])
@login_required
@role_required(["preview", "medium", "max"])
def index():
    """Index page."""
    time_filter_max = ca.config["TIME_FILTER_MAX"]
    preview_id = request.args.get("preview", "")
    sort_order = request.cookies.get("sort_order", "desc")
    show_types = request.cookies.get("show_types", "both")
    time_filter = int(request.cookies.get("time_filter", 1))

    # Update database
    update_img_db()

    # Get thumbnails from database
    thumbs = get_thumbs(sort_order, show_types, time_filter)

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
            thumbs=thumbs,
        )
    )

    return response


@bp.route("/download", methods=["POST"])
@login_required
@role_required(["preview", "medium", "max"])
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
@login_required
@role_required(["preview", "medium", "max"])
def zipdata():
    """ZIP File."""
    check_list = request.json.get("thumb_id", [])
    if isinstance(check_list, str):
        check_list = [request.json["check_list"]]
    if check_list:
        zip_list = []
        for id in check_list:
            thumb = files_db.query.get(id)
            zip_list.append(thumb.name)

        return get_zip(zip_list)
    abort(404, {"message": "List empty"})


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


def get_thumbs(sort_order: str, show_types: str, time_filter: int):
    """Return thumbnails from database."""
    order = (
        files_db.datetime.desc() if sort_order == "desc" else files_db.datetime.asc()
    )
    match show_types:
        case "both":
            show_types = ["i", "t", "v"]
        case "image":
            show_types = ["i", "t"]
        case _:
            show_types = ["v"]

    if (time_filter := int(time_filter)) == 1:
        files = files_db.query.filter(files_db.type.in_(show_types)).order_by(order)
    elif time_filter == ca.config.get("TIME_FILTER_MAX"):
        dt_search = dt.fromtimestamp(dt.now().timestamp() - (86400 * (time_filter - 2)))
        files = files_db.query.filter(
            files_db.type.in_(show_types), files_db.datetime <= dt_search
        ).order_by(order)
    else:
        dt_lw = dt.fromtimestamp(dt.now().timestamp() - (86400 * (time_filter - 2)))
        dt_gt = dt.fromtimestamp(dt.now().timestamp() - (time_filter - 1) * 86400)
        files = files_db.query.filter(
            files_db.type.in_(show_types),
            files_db.datetime < dt_lw,
            files_db.datetime >= dt_gt,
        ).order_by(order)

    return files.all()
