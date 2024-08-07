"""Blueprint Settings."""

from datetime import datetime as dt

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask import current_app as ca
from flask_login import login_required
from sqlalchemy import delete

from ..apis.rsync import Rsync
from ..apis.settings import Macros, Sets
from ..helpers.database import update_img_db
from ..helpers.decorator import role_required
from ..helpers.filer import allowed_file, zip_extract, zip_folder
from ..models import Files, Multiviews, Presets, Ubuttons, Users, db

bp = Blueprint(
    "settings", __name__, template_folder="templates", url_prefix="/settings"
)


@bp.route("/", methods=["GET"])
@login_required
@role_required("max")
def index():
    macros = Macros().get()
    settings = Sets().get()
    rsync = Rsync().get()
    users = db.session.scalars(db.select(Users).filter(Users.id > 0)).all()
    camera_token, api_token = db.session.execute(
        db.select(Users.cam_token, Users.api_token).filter(Users.id == 0)
    ).one()
    ubuttons = db.session.scalars(db.select(Ubuttons)).all()
    multiviews = db.session.scalars(db.select(Multiviews)).all()
    presets = db.session.scalars(db.select(Presets.mode).group_by("mode")).all()
    return render_template(
        "settings.html",
        settings=settings,
        users=users,
        macros=macros,
        ubuttons=ubuttons,
        multiviews=multiviews,
        presets=presets,
        camera_token=camera_token,
        api_token=api_token,
        rsync=rsync,
    )


@bp.route("/backup", methods=["POST", "GET"])
@login_required
@role_required(["max"])
def backup():
    """Backup Data."""
    date_str = dt.now().strftime("%Y%m%d_%H%M%S")
    zipname = f"config_{date_str}.zip"

    memory_file = zip_folder(ca.config_folder)

    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zipname,
    )


@bp.route("/restore", methods=["POST"])
@login_required
@role_required(["max"])
def restore():
    """Restore configuration."""
    if "file" not in request.files:
        flash("No file part")
    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
    if file and allowed_file(file):
        zip_extract(file, ca.config_folder)
        db.session.execute(delete(Files))
        db.session.commit()
        update_img_db()
    return redirect(url_for("settings.index"))
