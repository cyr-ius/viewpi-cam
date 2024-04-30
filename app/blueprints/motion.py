"""Blueprint for Motion (external capture)."""

from datetime import datetime as dt

from flask import Blueprint, request, send_file
from flask import current_app as ca
from flask_login import login_required

from ..helpers.filer import allowed_file, zip_extract, zip_folder

bp = Blueprint("motion", __name__, url_prefix="/motion")


@bp.route("/action/<string:action>", methods=["POST"])
@login_required
def action(action: str) -> None:
    """Backup motion config."""
    match action:
        case "backup":
            date_str = dt.now().strftime("%Y%m%d_%H%M%S")
            zipname = f"motion_config_{date_str}.zip"
            memory_file = zip_folder(ca.config_folder)
            return send_file(
                memory_file,
                mimetype="application/zip",
                as_attachment=True,
                download_name=zipname,
            )
        case "restore":
            if (
                (file := request.files.get("file"))
                and file.filename != ""
                and allowed_file(file)
            ):
                zip_extract(file, ca.config_folder)
