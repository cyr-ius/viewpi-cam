"""Api camera."""

import os
import time

from flask import current_app as ca
from flask import request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..services.raspiconfig import RaspiConfigError
from .models import message

api = Namespace(
    "captures",
    description="Stop/Start capture and preview camera/images",
    decorators=[role_required("max"), login_required],
)


@api.response(204, "Action execute")
@api.response(401, "Unauthorized", message)
@api.response(422, "Error", message)
@api.route(
    "/video/start", endpoint="captures_video_start", doc={"description": "Start camera"}
)
@api.route(
    "/video/stop", endpoint="captures_video_stop", doc={"description": "Stop camera"}
)
class Camera(Resource):
    """Camera."""

    def post(self):
        """Get capture video."""
        try:
            if request.endpoint == "api.captures_video_start":
                ca.raspiconfig.send("cam 1")
            if request.endpoint == "api.captures_video_stop":
                ca.raspiconfig.send("cam 0")
            return "", 204
        except RaspiConfigError as error:
            abort(422, error)


@api.response(204, "Action execute")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
@api.route("/image")
class Image(Resource):
    """Image."""

    def post(self):
        """Get capture image."""
        try:
            ca.raspiconfig.send("im")
            return "", 204
        except RaspiConfigError as error:
            abort(422, error)


@api.response(204, "Action execute")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
@api.route(
    "/timelapse/start",
    endpoint="captures_timelapse_start",
    doc={"description": "Start timelapse"},
)
@api.route(
    "/timelapse/stop",
    endpoint="captures_timelapse_stop",
    doc={"description": "Stop timelapse"},
)
class Timelapse(Resource):
    """Timelapse."""

    def post(self):
        """Get capture Timelapse."""
        try:
            if request.endpoint == "captures_timelapse_start":
                ca.raspiconfig.send("tl 1")
            if request.endpoint == "captures_timelapse_stop":
                ca.raspiconfig.send("tl 0")
            return "", 204
        except RaspiConfigError as error:
            abort(422, error)


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
