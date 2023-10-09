"""Api system."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort, fields

from ..helpers.decorator import token_required
from ..helpers.raspiconfig import RaspiConfigError
from ..helpers.utils import execute_cmd
from ..services.handle import ViewPiCamException
from .models import message

api = Namespace("system")
api.add_model("Error", message)

command_m = api.model(
    "Command",
    {
        "cmd": fields.String(description="Command", required=True),
        "params": fields.List(
            fields.String(), description="Parameters", required=False
        ),
    },
)


@api.response(204, "Action is success")
@api.response(422, "Error", message)
@api.response(403, "Forbidden", message)
@api.route("/system/restart")
class Restart(Resource):
    """Restart host."""

    @token_required
    def post(self):
        """Execute command."""
        try:
            execute_cmd("echo s > /proc/sysrq-trigger")
            execute_cmd("echo b > /proc/sysrq-trigger")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(204, "Action is success")
@api.response(422, "Error", message)
@api.response(403, "Forbidden", message)
@api.route("/system/shutdown")
class Shutdown(Resource):
    """Restart application."""

    @token_required
    def post(self):
        """Execute command."""
        try:
            execute_cmd("echo s > /proc/sysrq-trigger")
            execute_cmd("echo o > /proc/sysrq-trigger")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(204, "Action is success")
@api.response(422, "Error", message)
@api.response(403, "Forbidden", message)
@api.route("/system/restart/app", endpoint="system_restart_app")
class RestartApp(Resource):
    """Restart application."""

    @token_required
    def post(self):
        """Execute command."""
        try:
            execute_cmd("killall gunicorn")
        except ViewPiCamException as error:
            abort(422, error)
        return "", 204


@api.response(422, "Error", message)
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", message)
@api.route("/command")
class Command(Resource):
    """FIFO Command."""

    @token_required
    @api.expect(command_m)
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
