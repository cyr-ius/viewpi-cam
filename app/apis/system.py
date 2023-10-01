"""Api system."""
from flask import current_app as ca
from flask import request
from flask_restx import Namespace, Resource, abort, fields

from ..helpers.decorator import token_required
from ..helpers.utils import execute_cmd
from .models import error_m

api = Namespace("system")
api.add_model("Error", error_m)

command_m = api.model(
    "Command",
    {
        "cmd": fields.String(description="Command", required=True),
        "params": fields.String(description="Parameters", required=False),
    },
)


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route(
    "/system/restart", endpoint="system_restart", doc={"description": "Restart host"}
)
@api.route(
    "/system/shutdown", endpoint="system_shutown", doc={"description": "Shutdown host"}
)
@api.route(
    "/system/restart/app",
    endpoint="system_restart_app",
    doc={"description": "Restart application"},
)
class Actions(Resource):
    """Get log."""

    @token_required
    def post(self):
        """Execute system command."""
        try:
            if request.endpoint == "api.system_restart":
                execute_cmd("echo s > /proc/sysrq-trigger")
                execute_cmd("echo b > /proc/sysrq-trigger")
            if request.endpoint == "api.system_shutown":
                execute_cmd("echo s > /proc/sysrq-trigger")
                execute_cmd("echo o > /proc/sysrq-trigger")
            if request.endpoint == "api.system_restart_app":
                execute_cmd("killall gunicorn")
        except Exception as error:  # pylint: disable=W0718
            abort(422, error)
        return {}, 200


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/commands")
class Command(Resource):
    """FIFO Command."""

    @token_required
    @api.expect(command_m)
    def post(self):
        """Send command to control fifo."""
        if cmd := api.payload.get("cmd"):
            if params := api.payload.get("params"):
                params = " ".join(params)
                rslt = ca.raspiconfig.send(f"{cmd} {params}")
            rslt = ca.raspiconfig.send(f"{cmd}")
            if rslt.get("type") == "error":
                abort(422, **rslt)
            return rslt
        abort(422, f"Command not found {cmd}")
