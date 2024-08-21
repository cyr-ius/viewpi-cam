"""Api system."""

import os
import time

from flask import current_app as ca
from flask import request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..services.raspiconfig import RaspiConfigError
from .models import command, message

api = Namespace(
    "raspiconfig",
    description="RaspiMjpeg is the component that drives video/image capture. This API allows access to these parameters",
    decorators=[role_required("max"), login_required],
)
api.add_model("Command", command)


@api.route("/")
class Setting(Resource):
    """Config."""

    @api.param("type", "All settings ou User settings [sys|user] (default:sys)")
    def get(self):
        """Get config settings."""
        ca.raspiconfig.refresh()
        if request.args.get("type", "") == "user":
            return ca.raspiconfig.user_config
        return ca.raspiconfig.raspi_config


@api.response(204, "Success")
@api.response(401, "Unauthorized")
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
                    params = [str(item) for item in params]
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
@api.route("/status")
class StatusMjpeg(Resource):
    """Status mjpeg."""

    @api.param("last", "Last content")
    def get(self):
        """Get status."""
        file_content = ""
        if not os.path.isfile(ca.raspiconfig.status_file):
            abort(422, "Status file not found.")
        for _ in range(0, 30):
            with open(ca.raspiconfig.status_file, encoding="utf-8") as file:
                file_content = file.read()
                if file_content != request.args.get("last"):
                    break
                time.sleep(0.1)
                file.close()
        os.popen(f"touch {ca.raspiconfig.status_file}")
        return {"status": str(file_content)}
