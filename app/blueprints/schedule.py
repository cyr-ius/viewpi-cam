"""Blueprint Scheduler."""

import zoneinfo
from flask import Blueprint, render_template
from flask import current_app as ca
from flask_login import login_required

from ..apis.schedule import dt_now, get_calendar, sun_info, time_offset
from ..helpers.decorator import role_required
from ..helpers.utils import get_pid, get_settings
from ..models import Scheduler as scheduler_db
from ..models import db

bp = Blueprint(
    "schedule", __name__, template_folder="templates", url_prefix="/schedule"
)


@bp.route("/", methods=["GET"])
@login_required
@role_required(["max"])
def index():
    """Index page."""
    settings = get_settings()
    schedulers = db.session.scalars(
        db.select(scheduler_db).filter_by(daysmode_id=settings["daymode"])
    ).all()

    selected_scheduler = []
    for scheduler in schedulers:
        days = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        for day in scheduler.calendars:
            days[int(day.id)] = 1
        scheduler.days = days
        selected_scheduler.append(scheduler)

    return render_template(
        "schedule.html",
        control_file=ca.raspiconfig.control_file,
        current_time=dt_now().strftime("%H:%M"),
        motion_pipe=ca.raspiconfig.motion_pipe,
        offset=time_offset(settings["gmt_offset"]),
        period=get_calendar(settings["daymode"]),
        schedule_pid=get_pid(["*/flask", "scheduler"]),
        settings=settings,
        sunrise=sun_info("sunrise").strftime("%H:%M"),
        sunset=sun_info("sunset").strftime("%H:%M"),
        timezones=zoneinfo.available_timezones(),
        scheduler=selected_scheduler,
    )
