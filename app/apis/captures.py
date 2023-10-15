"""Api camera."""
from flask import current_app as ca
from flask import request
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import token_required
from ..helpers.raspiconfig import RaspiConfigError
from .models import forbidden, message

api = Namespace("captures", path="/api")
api.add_model("Error", message)
api.add_model("Forbidden", forbidden)


@api.response(204, "Action execute")
@api.response(422, "Error", message)
@api.response(403, "Forbidden", forbidden)
@api.route("/captures/video/start", endpoint="captures_video_start")
@api.route("/captures/video/stop", endpoint="captures_video_stop")
class Camera(Resource):
    """Camera."""

    @token_required
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
@api.response(422, "Error", message)
@api.response(403, "Forbidden", forbidden)
@api.route("/captures/image")
class Image(Resource):
    """Image."""

    @token_required
    def post(self):
        """Get capture image."""
        try:
            ca.raspiconfig.send("im")
            return "", 204
        except RaspiConfigError as error:
            abort(422, error)


@api.response(204, "Action execute")
@api.response(422, "Error", message)
@api.response(403, "Forbidden", forbidden)
@api.route("/captures/timelapse/start", endpoint="captures_timelapse_start")
@api.route("/captures/timelapse/stop", endpoint="captures_timelapse_stop")
class Timelapse(Resource):
    """Timelapse."""

    @token_required
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
