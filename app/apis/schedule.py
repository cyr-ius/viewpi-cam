"""Api camera."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, fields

from ..helpers.decorator import token_required
from .error_handler import error_m

api = Namespace("Schedule")
error_m = api.model("Error", error_m)
wild = fields.Wildcard(fields.List(fields.Integer()))
day = api.model("Day", {"*": wild})

schedule = api.model(
    "Schedule",
    {
        "autocamera_interval": fields.Integer(required=True, description="File name"),
        "autocapture_interval": fields.Integer(required=True, description="I/T/V"),
        "cmd_poll": fields.Float(required=True, description="Size"),
        "command_off": fields.List(fields.String(description="Command")),
        "command_on": fields.List(fields.String(description="Command")),
        "dawnstart_minute": fields.Integer(
            required=True, description="Read/Write right on disk"
        ),
        "daystart_minute": fields.Integer(
            required=True, description="Read/Write right on disk"
        ),
        "dayend_minute": fields.Integer(
            required=True, description="Read/Write right on disk"
        ),
        "daymode": fields.Integer(required=True, description="Original name"),
        "days": fields.Nested(day),
        "gmt_offset": fields.String(
            required=False, description="image numbers of timelapse"
        ),
        "latitude": fields.Float(
            required=False, description="image numbers of timelapse"
        ),
        "longitude": fields.Float(
            required=False, description="image numbers of timelapse"
        ),
        "managment_command": fields.String(
            required=False, description="image numbers of timelapse"
        ),
        "managment_interval": fields.Integer(
            required=True, description="Original name"
        ),
        "max_capture": fields.Integer(required=True, description="Size"),
        "mode_poll": fields.Integer(required=True, description="Size"),
        "modes": fields.List(fields.String(description="mode")),
        "purgeimage_hours": fields.Integer(required=True, description="Size"),
        "purgelapse_hours": fields.Integer(required=True, description="Size"),
        "purgevideo_hours": fields.Integer(required=True, description="Size"),
        "purgespace_level": fields.Integer(required=True, description="Size"),
        "purgespace_modeex": fields.Integer(required=True, description="Size"),
        "times": fields.List(fields.String(description="time")),
    },
)


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/schedule")
class Schedule(Resource):
    """Schedule."""

    @token_required
    @api.marshal_with(schedule)
    def get(self):
        return ca.settings

    @api.expect(schedule)
    @api.marshal_with(schedule)
    @token_required
    def put(self):
        ca.settings.update(**api.payload)
        return
