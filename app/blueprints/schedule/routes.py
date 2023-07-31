import os
import time
from datetime import datetime as dt
from datetime import timedelta as td

import pytz
from flask import Blueprint, current_app, render_template, request
from flask.cli import with_appcontext
from psutil import process_iter
from suntime import Sun

from ...const import (
    ATTR_AUTOCAMERAINTERVAL,
    ATTR_AUTOCAPTUREINTERVAL,
    ATTR_CMDPOLL,
    ATTR_COMMANDSOFF,
    ATTR_COMMANDSON,
    ATTR_DAWNSTARTMINUTES,
    ATTR_DAYENDMINUTES,
    ATTR_DAYMODE,
    ATTR_DAYS,
    ATTR_DAYSTARTMINUTES,
    ATTR_DUSKENDMINUTES,
    ATTR_GMTOFFSET,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_MAXCAPTURE,
    ATTR_MGMTCOMMAND,
    ATTR_MGMTINTERVAL,
    ATTR_MODE_POLL,
    ATTR_MODES,
    ATTR_PURGEIMAGEHOURS,
    ATTR_PURGELAPSEHOURS,
    ATTR_PURGESPACELEVEL,
    ATTR_PURGESPACEMODE,
    ATTR_PURGEVIDEOHOURS,
    ATTR_TIMES,
    SCHEDULE_FIFOIN,
    SCHEDULE_FIFOOUT,
    SCHEDULE_RESET,
    SCHEDULE_START,
    SCHEDULE_STOP,
)
from ...helpers.decorator import auth_required
from ...helpers.filer import (
    check_motion,
    delete_log,
    file_exists,
    file_get_content,
    get_config,
    get_log_size,
    get_settings,
    open_pipe,
    purge_files,
    send_cmds,
    send_pipe,
    set_settings,
    write_log,
)
from .form import frm_schedule, frm_days_mode

bp = Blueprint(
    "schedule",
    __name__,
    template_folder="templates",
    url_prefix="/schedule",
    cli_group="scheduler",
)
bp.cli.short_help = "Stop/Start scheduler"


@bp.route("/", methods=["GET", "POST"])
@auth_required
def index():
    bk_config = f"{current_app.config['FILE_SETTINGS']}.backup"
    form = frm_schedule()
    form_days_mode = frm_days_mode()
    if request.method == "POST" and (action := request.form.get("action")):
        match action:
            case "start":
                launch_schedule()
            case "stop":
                stop_scheduler()
            case "save":
                write_log("Saved schedule settings")
                set_settings(request.form)
                write_log("Send Schedule reset")
                send_pipe(
                    get_settings(SCHEDULE_FIFOIN),
                    SCHEDULE_RESET,
                )
            case "backup":
                write_log("Backed up schedule settings")
                set_settings(get_settings(), bk_config)
            case "restore":
                write_log("Restored up schedule settings")
                set_settings(get_settings(path_file=bk_config))

    offset = get_time_offset(get_settings(ATTR_GMTOFFSET))

    sunrise = get_sunrise(
        get_settings(ATTR_LATITUDE), get_settings(ATTR_LONGITUDE), offset
    )
    sunset = get_sunset(
        get_settings(ATTR_LATITUDE), get_settings(ATTR_LONGITUDE), offset
    )

    local_time = get_current_local_time(offset=offset)

    period = day_period(
        local_time=local_time,
        sunrise=sunrise,
        sunset=sunset,
        day_mode=get_settings(ATTR_DAYMODE),
        daw=get_settings(ATTR_DAWNSTARTMINUTES),
        day_start=get_settings(ATTR_DAYSTARTMINUTES),
        dusk=get_settings(ATTR_DUSKENDMINUTES),
        day_end=get_settings(ATTR_DAYENDMINUTES),
        times=get_settings(ATTR_TIMES),
    )

    return render_template(
        "schedule.html",
        settings=get_settings(),
        schedule_pid=get_schedule_pid(),
        day_period=period,
        offset=offset,
        sunrise=sunrise.strftime("%H:%M"),
        sunset=sunset.strftime("%H:%M"),
        current_time=local_time.strftime("%H:%M"),
    )


@bp.cli.command("stop", short_help="Stop scheduler task")
@with_appcontext
def stop_scheduler() -> int | None:
    pid = get_schedule_pid()
    os.popen(f"kill {pid}")


@bp.cli.command("start", short_help="Start scheduler task")
@with_appcontext
def start_scheduler() -> int | None:
    pid = get_schedule_pid()
    if not pid:
        scheduler()


def scheduler():
    settings = get_settings()
    if len(settings) == 0:
        write_log("Setttings for scheduler not found")
        return
    if not file_exists(get_config("status_file")):
        write_log("Status mjpeg not found")
        return

    write_log("RaspiCam support started")

    fifo_out = settings[SCHEDULE_FIFOOUT]
    pipeIn = open_pipe(settings[SCHEDULE_FIFOIN])

    capture_start = 0
    timeout = 0
    timeout_max = 0
    while timeout_max == 0 or timeout < timeout_max:
        write_log("Scheduler loop is started")
        last_on_cmd = -1
        last_day_period = -1
        # lastDay = -1
        poll_time = settings[ATTR_CMDPOLL]
        slow_poll = 0
        managechecktime = dt.timestamp(dt.utcnow())
        autocameratime = managechecktime
        modechecktime = managechecktime

        if settings[ATTR_AUTOCAPTUREINTERVAL] > settings[ATTR_MAXCAPTURE]:
            autocapturetime = managechecktime
            autocapture = 2
        else:
            autocapturetime = 0
            autocapture = 0

        lastStatusTime = os.path.getmtime(get_config("status_file"))
        while timeout_max == 0 or timeout < timeout_max:
            time.sleep(poll_time)
            cmd = check_motion(pipeIn)
            if cmd == SCHEDULE_STOP and autocapture == 0:
                if last_on_cmd >= 0:
                    write_log("Stop capture requested")
                    send = settings[ATTR_COMMANDSOFF][last_on_cmd]
                    if send:
                        send_cmds(
                            fifo=fifo_out,
                            str_cmd=send,
                            days=last_day_period,
                        )
                        last_on_cmd = -1
                else:
                    write_log("Stop capture request ignored, already stopped")
            elif cmd == SCHEDULE_START or autocapture == 1:
                if last_day_period >= 0:
                    if autocapture == 1:
                        autocapture = 2
                        write_log("Start triggered by autocapture")
                    else:
                        write_log("Start capture requested from Pipe")

                    send = settings[ATTR_COMMANDSON][last_day_period]
                    if send:
                        send_cmds(
                            fifo=fifo_out,
                            str_cmd=send,
                            days=last_day_period,
                        )
                        last_on_cmd = last_day_period
                        capture_start = dt.timestamp(dt.utcnow())
                else:
                    write_log(
                        "Start capture request ignored, day period not initialised yet"
                    )
            elif cmd == SCHEDULE_RESET:
                write_log("Reload parameters command requested")
                settings = get_settings()
            elif cmd != "":
                write_log(f"Ignore FIFO char {cmd}")

            if slow_poll < 0:
                slow_poll = 10
                timenow = dt.timestamp(dt.utcnow())
                forcePeriodCheck = 0
                if last_on_cmd >= 0:
                    if settings[ATTR_MAXCAPTURE] > 0:
                        if (timenow - capture_start) >= settings[ATTR_MAXCAPTURE]:
                            write_log("Maximum Capture reached. Sending off command")
                            send_cmds(
                                fifo=fifo_out,
                                str_cmd=settings[ATTR_COMMANDSOFF][last_on_cmd],
                            )
                            last_on_cmd = -1
                            autocapture = 0
                            forcePeriodCheck = 1
                if timenow > modechecktime or forcePeriodCheck == 1:
                    modechecktime = timenow + settings[ATTR_MODE_POLL]
                    forcePeriodCheck = 0
                    if last_on_cmd < 0:
                        newDayPeriod = wrap_day_period(settings)
                        # newDay = dt.now().strftime("%w")
                        if newDayPeriod != last_day_period:
                            write_log(f"New period detected {newDayPeriod}")
                            send_cmds(
                                fifo=fifo_out,
                                str_cmd=settings[ATTR_MODES][newDayPeriod],
                                days=settings[ATTR_DAYS],
                                period=newDayPeriod,
                            )
                            last_day_period = newDayPeriod
                            # lastDay = newDay
                if timenow > managechecktime:
                    managechecktime = timenow + settings[ATTR_MGMTINTERVAL]
                    write_log(f"Scheduled management tasks. Next at {managechecktime}")
                    purge_files(
                        settings[ATTR_PURGEVIDEOHOURS],
                        settings[ATTR_PURGEIMAGEHOURS],
                        settings[ATTR_PURGELAPSEHOURS],
                        settings[ATTR_PURGESPACELEVEL],
                        settings[ATTR_PURGESPACEMODE],
                    )
                    cmd = settings[ATTR_MGMTCOMMAND]
                    if cmd != "":
                        write_log(f"exec_macro: {cmd}")
                        send_cmds(fifo=fifo_out, str_cmd=f"sy {cmd}")
                    delete_log(get_log_size())
                if autocapturetime > 0 and (timenow > autocapturetime):
                    autocapturetime = timenow + settings[ATTR_AUTOCAPTUREINTERVAL]
                    write_log("Autocapture request.")
                    autocapture = 1
                if (settings[ATTR_AUTOCAMERAINTERVAL] > 0) and timenow > autocameratime:
                    autocameratime = timenow + 2
                    modTime = os.path.getmtime(get_config("status_file"))
                    if file_get_content(get_config("status_file")) == "halted":
                        if modTime > lastStatusTime:
                            write_log("Autocamera startup")
                            send_cmds(fifo=fifo_out, str_cmd="ru 1")
                    else:
                        if (timenow - modTime) > settings[ATTR_AUTOCAMERAINTERVAL]:
                            write_log("Autocamera shutdown")
                            send_cmds(fifo=fifo_out, str_cmd="md 0;ru 0")
                            lastStatusTime = timenow + 5
                        else:
                            lastStatusTime = timenow
            slow_poll -= 1


def get_schedule_pid():
    for proc in process_iter():
        if "flask" and "scheduler" in proc.cmdline():
            return proc.pid
    return 0


def launch_schedule():
    ret = os.popen("python -m flask scheduler start >/dev/null &")
    return ret


def wrap_day_period(settings):
    offset = get_time_offset(settings[ATTR_GMTOFFSET])

    sunrise = get_sunrise(settings[ATTR_LATITUDE], settings[ATTR_LONGITUDE], offset)
    sunset = get_sunset(settings[ATTR_LATITUDE], settings[ATTR_LONGITUDE], offset)

    local_time = get_current_local_time(offset=offset)

    return day_period(
        local_time=local_time,
        sunrise=sunrise,
        sunset=sunset,
        day_mode=settings[ATTR_DAYMODE],
        daw=settings[ATTR_DAWNSTARTMINUTES],
        day_start=settings[ATTR_DAYSTARTMINUTES],
        dusk=settings[ATTR_DUSKENDMINUTES],
        day_end=settings[ATTR_DAYENDMINUTES],
        times=settings[ATTR_TIMES],
    )


def day_period(
    local_time: dt,
    sunrise: dt,
    sunset: dt,
    day_mode: int | float,
    daw: int | float,
    day_start: int | float,
    dusk: int | float,
    day_end: int | float,
    times,
):
    match day_mode:
        case 0:
            if local_time < (sunrise + td(minutes=daw)).replace(tzinfo=None):
                period = 1
            elif local_time < (sunrise + td(minutes=day_start)).replace(tzinfo=None):
                period = 2
            elif local_time > (sunset + td(minutes=dusk)).replace(tzinfo=None):
                period = 1
            elif local_time > (sunset + td(minutes=day_end)).replace(tzinfo=None):
                period = 4
            else:
                period = 3
        case 1:
            period = 0
        case 2:
            period = find_fixed_time_period(times, local_time)

    return period


def get_current_local_time(minute: bool = False, offset: td = None) -> dt | int:
    now = dt.utcnow()
    if offset:
        now = now + offset
    if minute:
        return now.hour * 60 + now.minute
    return now


def get_sunrise(latitude, longitude, offset: td) -> dt:
    sun = Sun(latitude, longitude)
    day_sunrise: dt = sun.get_sunrise_time()
    return day_sunrise + offset


def get_sunset(latitude, longitude, offset: td) -> dt:
    sun = Sun(latitude, longitude)
    day_sunset: dt = sun.get_sunset_time()
    return day_sunset + offset


def get_time_offset(offset: int | float | str = 0) -> td:
    if isinstance(offset, (int, float)):
        offset = td(hours=offset)
    else:
        try:
            gmt_time = dt.now(pytz.timezone(offset))
            offset = gmt_time.utcoffset()
        except pytz.UnknownTimeZoneError:
            offset = td(hours=0)
    return offset


def find_fixed_time_period(times, cMins: dt) -> int:
    period = len(times) - 1
    max_less_v = -1
    for i in range(0, len(times)):
        fMins = dt.strptime(times[i], "%H:%M")
        if (
            fMins.time() < cMins.time()
            and (fMins.hour * 60 + fMins.minute) > max_less_v  # noqa: W503
        ):
            max_less_v = fMins.hour * 60 + fMins.minute
            period = i
    return period + 5
