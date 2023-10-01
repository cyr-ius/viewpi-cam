"""Api scheduler."""
from datetime import datetime as dt
from datetime import timedelta as td
from datetime import timezone
from subprocess import PIPE, Popen

import pytz
from flask import current_app as ca
from flask import request
from flask_restx import Namespace, Resource, fields
from suntime import Sun

from ..const import SCHEDULE_RESET
from ..helpers.decorator import token_required
from ..helpers.fifo import send_motion
from ..helpers.utils import execute_cmd, get_pid, write_log
from .models import error_m

api = Namespace("schedule")
api.add_model("Error", error_m)

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
class Settings(Resource):
    """Schedule."""

    @token_required
    @api.marshal_with(schedule)
    def get(self):
        """Get settiings scheduler."""
        return ca.settings

    @api.expect(schedule)
    @api.marshal_with(schedule)
    @token_required
    def put(self):
        """Set settings."""
        cur_tz = ca.settings.gmt_offset
        ca.settings.update(**api.payload)
        if (new_tz := ca.settings.gmt_offset) != cur_tz:
            write_log(f"Set timezone {new_tz}")
            execute_cmd(f"ln -fs /usr/share/zoneinfo/{new_tz} /etc/localtime")
        send_motion(SCHEDULE_RESET)
        return ca.settings


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/schedule/actions/stop", endpoint="schedule_stop")
@api.route("/schedule/actions/start", endpoint="schedule_start")
@api.route("/schedule/actions/backup", endpoint="schedule_backup")
@api.route("/schedule/actions/restore", endpoint="schedule_restore")
class Actions(Resource):
    """Actions."""

    @token_required
    def post(self):
        """Post action."""
        match request.endpoint:
            case "api.schedule_start":
                if not get_pid("scheduler"):
                    Popen(["flask", "scheduler", "start"], stdout=PIPE)
                return "", 200
            case "api.schedule_stop":
                pid = get_pid("scheduler")
                execute_cmd(f"kill {pid}")
                return "", 200
            case "api.schedule_backup":
                ca.settings.backup()
                return "", 200
            case "api.schedule_restore":
                ca.settings.restore()
                return "", 200
        return "Action not found", 422


@api.route("/schedule/period")
class Period(Resource):
    """Sunrise."""

    @api.marshal_with(
        api.model("Period", {"period": fields.Integer(description="period")})
    )
    @api.expect(
        api.model("Period", {"daymode": fields.Integer(description="Day mode")})
    )
    def post(self):
        """Post day mode and return period."""
        now = local_time()
        sunrise = dt.strptime(Sunrise().get().get("datetime"), "%Y-%m-%dT%H:%M:%S%z")
        sunset = dt.strptime(Sunset().get().get("datetime"), "%Y-%m-%dT%H:%M:%S%z")

        match ca.settings.daymode:
            case 0:
                if now < (sunrise + td(minutes=ca.settings.dawnstart_minutes)):
                    period = 1
                elif now < (sunrise + td(minutes=ca.settings.daystart_minutes)):
                    period = 2
                elif now > (sunset + td(minutes=ca.settings.duskend_minutes)):
                    period = 1
                elif now > (sunset + td(minutes=ca.settings.dayend_minutes)):
                    period = 4
                else:
                    period = 3
            case 1:
                period = 0
            case 2:
                int_period = len(ca.settings.times) - 1
                max_less_v = -1
                for str_time in ca.settings.times:
                    f_mins = dt.strptime(str_time, "%H:%M")
                    if (
                        f_mins.time() < now.time()
                        and (f_mins.hour * 60 + f_mins.minute) > max_less_v
                    ):
                        max_less_v = f_mins.hour * 60 + f_mins.minute
                        int_period = ca.settings.times.index(str_time)

                period = int_period + 5

        return {"period": period}


@api.route("/sun/sunrise")
class Sunrise(Resource):
    """Sunrise."""

    @api.marshal_with(
        api.model("Datetime", {"datetime": fields.DateTime(dt_format="iso8601")})
    )
    def get(self):
        """Get sunrise datetime."""
        offset = get_time_offset(ca.settings.gmt_offset)
        sun = Sun(ca.settings.latitude, ca.settings.longitude)
        day_sunrise = sun.get_sunrise_time()
        day_sunrise = day_sunrise.replace(tzinfo=utc_offset(offset.seconds))
        return {"datetime": day_sunrise + offset}


@api.route("/sun/sunset")
class Sunset(Resource):
    """Sunset."""

    @api.marshal_with(
        api.model("Datetime", {"datetime": fields.DateTime(dt_format="iso8601")})
    )
    def get(self):
        """Get sunset datetime."""
        offset = get_time_offset(ca.settings.gmt_offset)
        sun = Sun(ca.settings.latitude, ca.settings.longitude)
        day_sunset = sun.get_sunset_time()
        day_sunset = day_sunset.replace(tzinfo=utc_offset(offset.seconds))
        return {"datetime": day_sunset + offset}


def get_time_offset(offset: int | float | str = 0) -> td:
    """Get time offset."""
    if isinstance(offset, (int, float)):
        offset = td(hours=offset)
    else:
        try:
            gmt_time = dt.now(pytz.timezone(offset))
            offset = gmt_time.utcoffset()
        except pytz.UnknownTimeZoneError:
            offset = td(hours=0)
    return offset


def utc_offset(offset) -> timezone:
    return timezone(td(seconds=offset))


def local_time(minute: bool = False, offset: td = None) -> dt | int:
    """Get current local time."""
    now = dt.utcnow()
    if ca.settings.gmt_offset:
        offset = get_time_offset(ca.settings.gmt_offset)
        now = (now + offset).replace(tzinfo=utc_offset(offset.seconds))
    if minute:
        return now.hour * 60 + now.minute
    return now
