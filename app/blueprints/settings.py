"""Blueprint Settings."""
from flask import Blueprint, current_app, render_template

from ..apis.settings import Macros
from ..helpers.decorator import auth_required

bp = Blueprint(
    "settings", __name__, template_folder="templates", url_prefix="/settings"
)


@bp.route("/", methods=["GET", "POST", "DELETE"])
@auth_required
def index():
    macros = Macros().get_config()
    return render_template(
        "settings.html", settings=current_app.settings, macros=macros
    )
