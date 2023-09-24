"""Api camera."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, fields

from ..helpers.decorator import token_required

api = Namespace("Captures")
error_m = api.model("Error", {"message": fields.String(required=True)})

action_m = api.model(
    "Action",
    {"action": fields.Boolean(required=True, description="Stop or Start action")},
)


@api.response(204, "Action execute")
@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/captures/video")
class Camera(Resource):
    """Camera."""

    @token_required
    @api.expect(action_m)
    def post(self):
        """Get capture video."""
        if api.payload.get("action") == "start":
            ca.raspiconfig.send("cam 1")
        if api.payload.get("action") == "stop":
            ca.raspiconfig.send("cam 0")
        return "", 204


@api.response(204, "Action execute")
@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/captures/image")
class Image(Resource):
    """Image."""

    @token_required
    def post(self):
        """Get capture image."""
        ca.raspiconfig.send("im")
        return "", 204


@api.response(204, "Action execute")
@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/captures/timelapse")
class Timelapse(Resource):
    """Timelapse."""

    @token_required
    @api.expect(action_m)
    def post(self):
        """Get capture Timelapse."""
        if api.payload.get("action") == "start":
            ca.raspiconfig.send("tl 1")
        if api.payload.get("action") == "stop":
            ca.raspiconfig.send("tl 0")
        return "", 204
