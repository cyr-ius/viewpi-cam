"""Blueprint Settings."""

from flask import Blueprint, render_template

from ..apis.settings import Macros
from ..helpers.decorator import auth_required, role_required
from ..models import Multiviews, Presets, Settings, Ubuttons, Users

bp = Blueprint(
    "settings", __name__, template_folder="templates", url_prefix="/settings"
)


@bp.route("/", methods=["GET"])
@auth_required
@role_required("max")
def index():
    macros = Macros().get_config()
    users = Users.query.all()
    ubuttons = Ubuttons.query.all()
    multiviews = Multiviews.query.all()
    settings = Settings.query.get(1)
    presets = Presets.query.add_column(Presets.mode).group_by("mode").all()
    return render_template(
        "settings.html",
        settings=settings,
        users=users,
        macros=macros,
        ubuttons=ubuttons,
        multiviews=multiviews,
        presets=dict(presets).values(),
    )
