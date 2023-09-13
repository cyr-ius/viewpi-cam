"""Blueprint Settings."""
import random

from flask import Blueprint, current_app, render_template, request

from ..helpers.decorator import auth_required
from ..helpers.settings import SettingsException

bp = Blueprint(
    "settings", __name__, template_folder="templates", url_prefix="/settings"
)


@bp.route("/", methods=["GET", "POST", "DELETE"])
@auth_required
def index():
    msg = {"type": "success", "message": "Save data"}
    if request.method == "GET":
        macros = {
            item: getattr(current_app.raspiconfig, item)
            for item in current_app.config["MACROS"]
        }
        return render_template("settings.html", settings=current_app.settings, macros=macros)

    try:
        if request.method == "POST" and (json := request.json):
            if any(
                key in json.keys() for key in ("pilight", "pipan", "servo", "upreset")
            ):
                current_app.settings.update(**json)
            if "token" in json.keys():
                token = f"B{random.getrandbits(256)}"
                current_app.settings.update(token=token)
                msg.update({"token": token})
            if "macro" in json.keys():
                current_app.settings.ubuttons.append(json)
                current_app.settings.update(ubuttons=current_app.settings.ubuttons)
            if "user_id" in json.keys():
                current_app.settings.set_user(**json)

        if request.method == "DELETE" and (json := request.json):
            if "token" in json.keys():
                del current_app.settings.token
            if "macro" in json.keys():
                current_app.settings.ubuttons.remove(json)
                current_app.settings.update(ubuttons=current_app.settings.ubuttons)
            if "user_id" in json.keys():
                current_app.settings.del_user(json["user_id"])
    except SettingsException as error:
        msg.update({"type": "error", "message": str(error)})

    return msg
