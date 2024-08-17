"""Api scheduler."""

from datetime import datetime as dt
from datetime import timedelta as td
from datetime import timezone
from subprocess import PIPE, Popen

import pytz
import zoneinfo
from flask import current_app as ca
from flask import request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort
from sqlalchemy import update
from suntime import Sun

from ..helpers.decorator import role_required
from ..helpers.exceptions import ViewPiCamException
from ..helpers.fifo import send_pipe
from ..helpers.utils import execute_cmd, get_pid, get_settings, set_timezone, write_log
from ..models import Calendar, Settings, db
from ..models import Scheduler as scheduler_db
from .models import (
    calendar,
    date_time,
    daymode,
    daysmode,
    message,
    period,
    schedule,
    scheduler,
)

api = Namespace(
    "schedule",
    description="Scheduler management",
    decorators=[role_required("max"), login_required],
)
api.add_model("Datetime", date_time)
api.add_model("Schedule", schedule)
api.add_model("Daymode", daymode)
api.add_model("Period", period)
api.add_model("Scheduler", scheduler)
api.add_model("Calendar", calendar)
api.add_model("Daysmode", daysmode)


@api.route("/")
@api.response(401, "Unauthorized")
class Sets(Resource):
    """Schedule."""

    @api.marshal_with(schedule)
    def get(self):
        """Get settings scheduler."""
        return get_settings()

    @api.expect(schedule)
    @api.response(201, "Success")
    def put(self):
        """Set settings."""
        settings = get_settings()
        cur_tz = settings["gmt_offset"]
        settings.update(api.payload)
        db.session.execute(update(Settings), {"id": 0, "data": settings})
        db.session.commit()
        if (new_tz := settings["gmt_offset"]) != cur_tz:
            try:
                set_timezone(new_tz)
            except ViewPiCamException as error:
                write_log(f"[Timezone] {str(error)}", "error")

        send_pipe(ca.config["SCHEDULE_RESET"])
        return api.payload, 201


@api.route("/scheduler")
@api.response(401, "Unauthorized")
class Scheduler(Resource):
    """Schedule."""

    @api.marshal_with(scheduler, as_list=True)
    @api.param("daymode", description="Daymode id")
    def get(self):
        """Get settings scheduler."""
        if id := request.args.get("daymode"):
            return db.session.scalars(
                db.select(scheduler_db).filter_by(daysmode_id=id)
            ).all()
        return db.session.scalars(db.select(scheduler_db)).all()

    @api.expect(scheduler)
    @api.response(201, "Success")
    def put(self):
        """Set settings."""
        for item in api.payload:
            schedule = db.session.scalars(
                db.select(scheduler_db).filter_by(
                    daysmode_id=item["daymode"], id=int(item["id"])
                )
            ).first()
            schedule.command_on = item["command_on"]
            schedule.command_off = item["command_off"]
            schedule.mode = item["mode"]
            schedule.calendars = []
            for key, value in item["calendar"].items():
                if value:
                    cal = db.session.scalars(
                        db.select(Calendar).filter_by(name=key.capitalize())
                    ).first()
                    schedule.calendars.append(cal)
            db.session.commit()

        send_pipe(ca.config["SCHEDULE_RESET"])
        return api.payload, 201


@api.route("/stop", endpoint="schedule_stop", doc={"description": "Stop scheduler"})
@api.route("/start", endpoint="schedule_start", doc={"description": "Start scheduler"})
@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
class Actions(Resource):
    """Actions."""

    def post(self):
        """Post action."""
        match request.endpoint:
            case "api.schedule_start":
                try:
                    if not get_pid(["*/flask", "scheduler"]):
                        Popen(["flask", "scheduler", "start"], stdout=PIPE)
                    return "", 204
                except FileNotFoundError as error:
                    return abort(422, error)
            case "api.schedule_stop":
                pid = get_pid(["*/flask", "scheduler"])
                try:
                    if pid:
                        execute_cmd(f"kill {pid}")
                except ViewPiCamException as error:
                    return abort(422, error)
                return "", 204


@api.route("/state")
@api.response(201, "Success")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
class State(Resource):
    """State scheduler."""

    def get(self):
        """State"""
        if get_pid(["*/flask", "scheduler"]):
            return {"start": 1, "stop": 0, "state": True}, 201
        return {"start": 0, "stop": 1, "state": False}, 201


@api.route("/period")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
class Period(Resource):
    """Sunrise."""

    @api.expect(daymode)
    @api.marshal_with(period, code=201)
    def post(self):
        """Post day mode and return period."""
        if api.payload["daymode"] in [0, 1, 2]:
            return {"period": get_calendar(api.payload["daymode"])}, 201
        abort(422, "Daymode not exist")


@api.response(201, "Success")
@api.response(401, "Unauthorized")
@api.route("/sun/sunrise")
class Sunrise(Resource):
    """Sunrise."""

    @api.marshal_with(date_time, code=201)
    def get(self):
        """Get sunrise datetime."""
        return {"datetime": sun_info("sunrise")}, 201


@api.response(201, "Success")
@api.response(401, "Unauthorized")
@api.route("/sun/sunset")
class Sunset(Resource):
    """Sunset."""

    @api.marshal_with(date_time, code=201)
    def get(self):
        """Get sunset datetime."""
        return {"datetime": sun_info("sunset")}, 201


@api.response(201, "Success")
@api.response(401, "Unauthorized")
@api.route("/gmtoffset")
class GmtOffset(Resource):
    """GMT Offset"""

    def get(self):
        """GMT Offset."""
        gmt_offset = get_settings("gmt_offset")
        return {"gmt_offset": gmt_offset}, 201


@api.response(201, "Success")
@api.response(401, "Unauthorized")
@api.route("/timezones")
class TimeZones(Resource):
    """Timezone"""

    def get(self):
        """Timezone."""
        timezones = zoneinfo.available_timezones()
        return list(timezones), 201


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
    settings = db.session.scalars(db.select(Settings)).first()
    if settings.data["gmt_offset"]:
        offset = time_offset(settings.data["gmt_offset"])
        now = (now + offset).replace(tzinfo=utc_offset(offset.seconds))
    if minute:
        return now.hour * 60 + now.minute
    return now


def sun_info(mode: str) -> dt:
    """Return sunset or sunrise datetime."""
    settings = db.session.scalars(db.select(Settings)).first()
    offset = time_offset(settings.data["gmt_offset"])
    sun = Sun(settings.data["latitude"], settings.data["longitude"])
    if mode.lower() == "sunset":
        sun_time = sun.get_sunset_time()
    else:
        sun_time = sun.get_sunrise_time()
    return sun_time.replace(tzinfo=utc_offset(offset.seconds)) + offset


def get_calendar(daymode: int) -> int:
    """Get calendar."""
    now = dt_now()
    sunrise = sun_info("sunrise")
    sunset = sun_info("sunset")
    settings = db.session.scalars(db.select(Settings)).first()

    match daymode:
        case 0:
            if now < (sunrise + td(minutes=settings.data["dawnstart_minutes"])):
                # Night
                mem_sch = db.session.scalars(
                    db.select(scheduler_db).filter_by(
                        period="night", daysmode_id=daymode
                    )
                ).first()
            elif now < (sunrise + td(minutes=settings.data["daystart_minutes"])):
                # Dawn
                mem_sch = db.session.scalars(
                    db.select(scheduler_db).filter_by(
                        period="dawn", daysmode_id=daymode
                    )
                ).first()
            elif now > (sunset + td(minutes=settings.data["duskend_minutes"])):
                # Night
                mem_sch = db.session.scalars(
                    db.select(scheduler_db).filter_by(
                        period="night", daysmode_id=daymode
                    )
                ).first()
            elif now > (sunset + td(minutes=settings.data["dayend_minutes"])):
                # Dusk
                mem_sch = db.session.scalars(
                    db.select(scheduler_db).filter_by(
                        period="dusk", daysmode_id=daymode
                    )
                ).first()
            else:
                # Day
                mem_sch = db.session.scalars(
                    db.select(scheduler_db).filter_by(period="day", daysmode_id=daymode)
                ).first()
        case 1:
            # AllDay
            mem_sch = db.session.scalars(
                db.select(scheduler_db).filter_by(period="allday", daysmode_id=daymode)
            ).first()
        case 2:
            # Times
            schedulers = db.session.scalars(
                db.select(scheduler_db).filter_by(daysmode_id=2)
            ).all()
            max_less_v = -1
            for scheduler in schedulers:
                str_time = scheduler.period
                f_mins = dt.strptime(str_time, "%H:%M")
                if (
                    f_mins.time() < now.time()
                    and (f_mins.hour * 60 + f_mins.minute) > max_less_v
                ):
                    max_less_v = f_mins.hour * 60 + f_mins.minute
                    mem_sch = scheduler

    return mem_sch.period
