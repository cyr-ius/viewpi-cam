"""Blueprint Settings."""

from flask import Blueprint, render_template
from flask_login import login_required

from ..apis.settings import Macros
from ..helpers.decorator import role_required
from ..models import Multiviews, Presets, Settings, Ubuttons, Users

bp = Blueprint(
    "settings", __name__, template_folder="templates", url_prefix="/settings"
)


@bp.route("/", methods=["GET"])
@login_required
@role_required("max")
def index():
    macros = Macros().get_config()
    users = Users.query.filter(Users.id > 0).all()
    ubuttons = Ubuttons.query.all()
    multiviews = Multiviews.query.all()
    presets = Presets.query.add_column(Presets.mode).group_by("mode").all()
    settings = Settings.query.first()
    return render_template(
        "settings.html",
        settings=settings.data,
        users=users,
        macros=macros,
        ubuttons=ubuttons,
        multiviews=multiviews,
        presets=dict(presets).values(),
    )
