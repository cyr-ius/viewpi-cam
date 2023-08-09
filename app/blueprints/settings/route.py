import random

from flask import Blueprint, current_app, render_template, request

from ...helpers.decorator import auth_required
from ...helpers.settings import SettingsException

bp = Blueprint(
    "settings", __name__, template_folder="templates", url_prefix="/settings"
)


@bp.route("/", methods=["GET", "POST", "DELETE"])
@auth_required
def index():
    msg_success = {"type": "success", "message": "Save data"}
    msg_error = {"type": "error", "message": "Failed to save data"}
    if request.method == "GET":
        return render_template(
            "settings.html",
            settings=current_app.settings,
            raspiconfig=current_app.raspiconfig,
            macros=current_app.config["MACROS"],
        )

    if request.method == "POST" and (json := request.json):
        if "upreset" in json.keys():
            current_app.settings.upreset = json["upreset"]
        if ("pilight" or "pipan" or "servo") in json.keys():
            current_app.settings.pilight = json["pilight"]
        if "token" in json.keys():
            token = f"B{random.getrandbits(256)}"
            current_app.settings.token = token
            msg_success.update({"token": token})
        if "macro" in json.keys():
            current_app.settings.ubuttons.append(json)
        if "user_id" in json.keys():
            current_app.settings.users.append(json)

    if request.method == "DELETE" and (json := request.json):
        if ("token") in json.keys():
            del current_app.settings.token
        if "macro" in json.keys():
            current_app.settings.ubuttons.remove(json)
        if "user_id" in json.keys():
            current_app.settings.del_user(json["user_id"])

    try:
        current_app.settings.save()
    except SettingsException as error:
        return msg_error.update({"message": str(error)})
    else:
        return msg_success
