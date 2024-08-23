"""Blueprint preview."""

import os
import time
import zipfile
from datetime import datetime as dt
from io import BytesIO

from flask import Blueprint, abort, make_response, render_template, request, send_file
from flask import current_app as ca
from flask_login import login_required

from ..helpers.database import update_img_db
from ..helpers.decorator import role_required
from ..helpers.filer import data_file_ext, data_file_name, get_file_type
from ..helpers.transform import check_media_path, get_thumbs
from ..helpers.utils import disk_usage
from ..models import Files, db

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
    check_list = request.json.get("thumb_ids", [])
    check_list = [check_list] if isinstance(check_list, str) else check_list
    if check_list:
        zip_list = []
        for id in check_list:
            if thumb := db.session.scalars(db.select(Files).filter_by(id=id)).first():
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
