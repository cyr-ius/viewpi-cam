"""Api system."""
import requests
import semver
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required, token_required
from ..helpers.raspiconfig import RaspiConfigError
from ..helpers.utils import execute_cmd
from ..services.handle import ViewPiCamException
from .models import command, message

api = Namespace(
    "system",
    path="/api",
    description="Host command",
    decorators=[token_required, role_required("max")],
)
api.add_model("Error", message)
api.add_model("Command", command)


@api.response(204, "Action is success")
@api.response(403, "Forbidden", message)
@api.response(422, "Error", message)
@api.route("/system/restart")
class Restart(Resource):
    """Restart host."""

    def post(self):
        """Execute command."""
        try:
            execute_cmd("echo s > /proc/sysrq-trigger")
            execute_cmd("echo b > /proc/sysrq-trigger")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(204, "Action is success")
@api.response(403, "Forbidden", message)
@api.response(422, "Error", message)
@api.route("/system/shutdown")
class Shutdown(Resource):
    """Restart application."""

    def post(self):
        """Execute command."""
        try:
            execute_cmd("echo s > /proc/sysrq-trigger")
            execute_cmd("echo o > /proc/sysrq-trigger")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(204, "Action is success")
@api.response(403, "Forbidden", message)
@api.response(422, "Error", message)
@api.route("/system/restart/app", endpoint="system_restart_app")
class RestartApp(Resource):
    """Restart application."""

    def post(self):
        """Execute command."""
        try:
            execute_cmd("killall gunicorn")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(403, "Forbidden", message)
@api.response(404, "Not found", message)
@api.response(422, "Error", message)
@api.route("/command")
class Command(Resource):
    """FIFO Command."""

    @api.expect(command)
    def post(self):
        """Send command to control fifo."""
        if cmd := api.payload.get("cmd"):
            try:
                if params := api.payload.get("params"):
                    params = " ".join(params)
                    return ca.raspiconfig.send(f"{cmd} {params}")
                return ca.raspiconfig.send(f"{cmd}")
            except RaspiConfigError as error:
                abort(422, str(error))
        abort(404, f"Command not found {cmd}")


@api.response(403, "Forbidden", message)
@api.response(404, "Not found", message)
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
            rjson["app_version"] = rjson.get("app_version").replace("v", "")
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
        except requests.RequestException as error:
            abort(422, str(error))
