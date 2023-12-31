"""Api scheduler."""
from datetime import datetime as dt
from datetime import timedelta as td
from datetime import timezone
from subprocess import PIPE, Popen

import pytz
from flask import current_app as ca
from flask import request
from flask_restx import Namespace, Resource, abort
from suntime import Sun

from ..const import SCHEDULE_RESET
from ..helpers.decorator import role_required, token_required
from ..helpers.fifo import send_motion
from ..helpers.utils import execute_cmd, get_pid, write_log
from ..services.handle import ViewPiCamException
from .models import date_time, day, daymode, forbidden, message, period, schedule

api = Namespace(
    "schedule",
    path="/api",
    description="Scheduler management",
    decorators=[token_required, role_required("max")],
)
api.add_model("Error", message)
api.add_model("Forbidden", forbidden)
api.add_model("Datetime", date_time)
api.add_model("Schedule", schedule)
api.add_model("Day", day)
api.add_model("Daymode", daymode)
api.add_model("Period", period)


@api.route("/schedule")
@api.response(403, "Forbidden", forbidden)
class Settings(Resource):
    """Schedule."""

    @api.marshal_with(schedule)
    def get(self):
        """Get settings scheduler."""
        return ca.settings

    @api.expect(schedule)
    @api.marshal_with(message)
    @api.response(204, "Action is success")
    def put(self):
        """Set settings."""
        cur_tz = ca.settings.gmt_offset
        ca.settings.update(**api.payload)
        if (new_tz := ca.settings.gmt_offset) != cur_tz:
            try:
                execute_cmd(f"ln -fs /usr/share/zoneinfo/{new_tz} /etc/localtime")
                write_log(f"Set timezone {new_tz}")
            except ViewPiCamException as error:
                write_log(error)
        send_motion(SCHEDULE_RESET)
        return "", 204


@api.route("/schedule/actions", doc=False)
@api.route("/schedule/actions/stop", endpoint="schedule_stop")
@api.route("/schedule/actions/start", endpoint="schedule_start")
@api.route("/schedule/actions/backup", endpoint="schedule_backup")
@api.route("/schedule/actions/restore", endpoint="schedule_restore")
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
@api.response(422, "Error", message)
class Actions(Resource):
    """Actions."""

    @api.marshal_with(message)
    def post(self):
        """Post action."""
        match request.endpoint:
            case "api.schedule_start":
                if not get_pid("scheduler"):
                    Popen(["flask", "scheduler", "start"], stdout=PIPE)
                return "", 204
            case "api.schedule_stop":
                pid = get_pid("scheduler")
                try:
                    execute_cmd(f"kill {pid}")
                except ViewPiCamException as error:
                    return abort(422, error)
                return "", 204
            case "api.schedule_backup":
                ca.settings.backup()
                return "", 204
            case "api.schedule_restore":
                ca.settings.restore()
                return "", 204
        abort(404, "Action not found")


@api.route("/schedule/period")
@api.response(403, "Forbidden", forbidden)
class Period(Resource):
    """Sunrise."""

    @api.marshal_with(period)
    @api.expect(daymode)
    def post(self):
        """Post day mode and return period."""
        return {"period": get_period(ca.settings.daymode)}


@api.route("/sun/sunrise")
class Sunrise(Resource):
    """Sunrise."""

    @api.marshal_with(date_time)
    def get(self):
        """Get sunrise datetime."""
        return {"datetime": sun_info("sunrise")}


@api.route("/sun/sunset")
class Sunset(Resource):
    """Sunset."""

    @api.marshal_with(date_time)
    def get(self):
        """Get sunset datetime."""
        return {"datetime": sun_info("sunset")}


def time_offset(offset: int | float | str = 0) -> td:
    """Get time offset."""
    if isinstance(offset, (int, float)):
        noffset = td(hours=offset)
    else:
        try:
            gmt_time = dt.now(pytz.timezone(offset))
            noffset = gmt_time.utcoffset()
        except pytz.UnknownTimeZoneError:
            noffset = td(hours=0)
    return noffset


def utc_offset(offset) -> timezone:
    return timezone(td(seconds=offset))


def dt_now(minute: bool = False) -> dt | int:
    """Get current local time."""
    now = dt.utcnow()
    if ca.settings.gmt_offset:
        offset = time_offset(ca.settings.gmt_offset)
        now = (now + offset).replace(tzinfo=utc_offset(offset.seconds))
    if minute:
        return now.hour * 60 + now.minute
    return now


def sun_info(mode: str) -> dt:
    """Return sunset or sunrise datetime."""
    offset = time_offset(ca.settings.gmt_offset)
    sun = Sun(ca.settings.latitude, ca.settings.longitude)
    if mode.lower() == "sunset":
        sun_time = sun.get_sunset_time()
    else:
        sun_time = sun.get_sunrise_time()
    return sun_time.replace(tzinfo=utc_offset(offset.seconds)) + offset


def get_period(daymode: int) -> int:
    """Get period."""
    now = dt_now()
    sunrise = sun_info("sunrise")
    sunset = sun_info("sunset")

    match daymode:
        case 0:
            if now < (sunrise + td(minutes=ca.settings.dawnstart_minutes)):
                int_period = 1
            elif now < (sunrise + td(minutes=ca.settings.daystart_minutes)):
                int_period = 2
            elif now > (sunset + td(minutes=ca.settings.duskend_minutes)):
                int_period = 1
            elif now > (sunset + td(minutes=ca.settings.dayend_minutes)):
                int_period = 4
            else:
                int_period = 3
        case 1:
            int_period = 0
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

            int_period = int_period + 5

    return int_period
