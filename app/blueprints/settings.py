"""Blueprint Settings."""
from flask import Blueprint
from flask import current_app as ca
from flask import render_template

from ..apis.settings import Macros
from ..helpers.decorator import auth_required, role_required

bp = Blueprint(
    "settings", __name__, template_folder="templates", url_prefix="/settings"
)


@bp.route("/", methods=["GET"])
@auth_required
@role_required("max")
def index():
    macros = Macros().get_config()
    return render_template("settings.html", settings=ca.settings, macros=macros)
