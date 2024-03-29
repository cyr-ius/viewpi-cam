"""Api camera."""

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
@api.route("/video/start", endpoint="captures_video_start")
@api.route("/video/stop", endpoint="captures_video_stop")
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
@api.response(401, "Unauthorized", message)
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
@api.response(401, "Unauthorized", message)
@api.response(422, "Error", message)
@api.route("/timelapse/start", endpoint="captures_timelapse_start")
@api.route("/timelapse/stop", endpoint="captures_timelapse_stop")
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
