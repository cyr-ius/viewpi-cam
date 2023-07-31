from flask import Blueprint, render_template, request, current_app
from ...helpers.decorator import auth_required
from .form import frm_settings, frm_user_buttons, frm_token, frm_users
import random

bp = Blueprint(
    "settings", __name__, template_folder="templates", url_prefix="/settings"
)


@bp.route("/", methods=["GET", "POST"])
@auth_required
def index():
    current_app.logger.info(current_app.settings.data)
    current_app.logger.info(current_app.settings.users)
    form_users = frm_users(request.form, data=current_app.settings.data)
    form_sets = frm_settings(request.form, data=current_app.settings.data)
    form_token = frm_token(request.form, data=current_app.settings.data)
    form_ubuttons = frm_user_buttons(request.form, data=current_app.settings.data)

    if request.method == "GET" and current_app.settings.users:
        form_users.users.append_entry()

    if request.method == "GET" and current_app.settings.user_buttons:
        form_ubuttons.user_buttons.append_entry()

    if request.method == "POST":
        if request.form.get("token") == "generate":
            token = random.getrandbits(256)
            current_app.settings.token = f"B{token}"

        if request.form.get("token") == "reset":
            current_app.settings.set(token=None)

    if form_sets.validate_on_submit():
        form_sets.populate_obj(current_app.settings)

    if form_ubuttons.validate_on_submit():
        form_ubuttons.populate_obj(current_app.settings)
        current_app.logger.info(current_app.settings.user_buttons)

    if form_users.validate_on_submit():
        form_users.populate_obj(current_app.settings)
        current_app.logger.info(current_app.settings.users)

    return render_template(
        "settings.html",
        settings=current_app.settings.data,
        form_sets=form_sets,
        form_ubuttons=form_ubuttons,
        form_token=form_token,
        form_users=form_users,
    )
