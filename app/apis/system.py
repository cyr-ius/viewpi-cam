"""Api system."""

import requests
import semver
from flask import current_app as ca
from flask import request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..helpers.exceptions import ViewPiCamException
from ..helpers.utils import disk_usage, execute_cmd
from ..models import Presets as db_presets, db
from ..services.raspiconfig import RaspiConfigError
from .models import command, locales, message, preset

api = Namespace(
    "system",
    description="Host command",
    # decorators=[role_required("max"), login_required],
)
api.add_model("Command", command)
api.add_model("Locales", locales)
api.add_model("Preset", preset)


@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
@api.route("/restart")
class Restart(Resource):
    """Restart host."""

    @login_required
    @role_required("max")
    def post(self):
        """Execute command."""
        try:
            execute_cmd("echo s > /proc/sysrq-trigger")
            execute_cmd("echo b > /proc/sysrq-trigger")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
@api.route("/shutdown")
class Shutdown(Resource):
    """Restart application."""

    @login_required
    @role_required("max")
    def post(self):
        """Execute command."""
        try:
            execute_cmd("echo s > /proc/sysrq-trigger")
            execute_cmd("echo o > /proc/sysrq-trigger")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
@api.route("/restart/app", endpoint="system_restart_app")
class RestartApp(Resource):
    """Restart application."""

    @login_required
    @role_required("max")
    def post(self):
        """Execute command."""
        try:
            execute_cmd("killall gunicorn")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(404, "Not found", message)
@api.response(422, "Error", message)
@api.route("/command")
class Command(Resource):
    """FIFO Command."""

    @login_required
    @role_required("max")
    @api.expect(command)
    def post(self):
        """Send command to control fifo."""
        if cmd := api.payload.get("cmd"):
            try:
                if params := api.payload.get("params"):
                    params = " ".join(params)
                    ca.raspiconfig.send(f"{cmd} {params}")
                else:
                    ca.raspiconfig.send(f"{cmd}")
                return "", 204
            except RaspiConfigError as error:
                abort(422, str(error))
        abort(404, f"Command not found {cmd}")


@api.response(200, "Success")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
@api.route("/version")
class Version(Resource):
    """Version."""

    def get(self):
        """Get version."""
        try:
            response = requests.get(ca.config["GIT_URL"], timeout=ca.config["TIMEOUT"])
            response.raise_for_status()
            rjson = response.json()
            rjson["app_version"] = rjson.get("tag_name").replace("v", "")
            current_version = ca.config["VERSION"].replace("v", "")
            rjson.update(
                {
                    "current_version": current_version,
                    "update_available": semver.compare(
                        rjson["app_version"], current_version
                    ),
                }
            )
            return rjson
        except (ValueError, requests.RequestException) as error:
            abort(422, str(error))


@api.response(200, "Success")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
@api.route("/disk/free")
class Freespace(Resource):
    """Free space disk."""

    @login_required
    @role_required("max")
    def get(self):
        """Get free space."""
        try:
            total, used, free, prc, color = disk_usage()
            return {
                "total": total,
                "used": used,
                "free": free,
                "prc": prc,
                "color": color,
            }
        except requests.RequestException as error:
            abort(422, str(error))


@api.response(401, "Unauthorized")
@api.route("/locales")
class Locales(Resource):
    """Language for user."""

    @api.marshal_with(locales)
    def get(self):
        """Get all languages."""
        return {"locales": ca.config["LOCALES"]}


@api.response(401, "Unauthorized")
@api.route("/presets")
class Presets(Resource):
    """Presets."""

    @api.param(
        "preset", "Select preset ['v2'|'P-OV5647'|'P-IMX219'|'N-OV5647|'N-IMX219']"
    )
    @api.marshal_with(preset, as_list=True)
    def get(self):
        """Presets video."""
        if preset := request.args.get("preset"):
            return db.session.scalars(
                db.select(db_presets).filter_by(mode=preset)
            ).all()
        return abort(404)


@api.response(401, "Unauthorized")
@api.route("/userlevel")
class UserLevel(Resource):
    """User Level."""

    def get(self):
        """Get user level."""
       
        userlevel = [{"name":k, "right":v} for k, v in ca.config["USERLEVEL"].items()]
        return userlevel