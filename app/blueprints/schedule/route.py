import os
import shutil
import time
from datetime import datetime as dt
from datetime import timedelta as td
from subprocess import Popen

import pytz
from flask import Blueprint, current_app, render_template, request
from flask.cli import with_appcontext
from psutil import process_iter
from suntime import Sun

from ...const import SCHEDULE_RESET, SCHEDULE_START, SCHEDULE_STOP
from ...helpers.decorator import auth_required
from ...helpers.filer import (
    delete_log,
    delete_mediafiles,
    get_file_type,
    is_thumbnail,
    list_folder_files,
    send_pipe,
    write_log,
)
from ...helpers.raspiconfig import RaspiConfigError

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
    msg = {"type": "success"}
    if request.method == "POST" and (action := request.json.pop("action", None)):
        try:
            match action:
                case "start":
                    launch_schedule()
                    msg.update({"message": "Start scheduler"})
                case "stop":
                    pid = get_schedule_pid()
                    os.popen(f"kill {pid}")
                    msg.update({"message": "Stop scheduler"})
                case "save":
                    write_log("Saved schedule settings")
                    current_app.settings.update(**request.json)
                    write_log("Send Schedule reset")
                    send_pipe(current_app.settings.fifo_in, SCHEDULE_RESET)
                    msg.update({"message": "Save data"})
                case "backup":
                    write_log("Backed up schedule settings")
                    current_app.settings.backup()
                    msg.update({"message": "Backup file settings"})
                case "restore":
                    write_log("Restored up schedule settings")
                    current_app.settings.restore()
                    msg.update({"message": "Restore file settings"})
        except RaspiConfigError as error:
            msg = {"type": "error", "message": str(error)}
        finally:
            return msg

    if request.method == "GET":
        offset = get_time_offset(current_app.settings.gmt_offset)

        sunrise = get_sunrise(
            current_app.settings.latitude, current_app.settings.longitude, offset
        )
        sunset = get_sunset(
            current_app.settings.latitude, current_app.settings.longitude, offset
        )

        local_time = get_current_local_time(offset=offset)

        period = day_period(
            local_time=local_time,
            sunrise=sunrise,
            sunset=sunset,
            day_mode=current_app.settings.daymode,
            daw=current_app.settings.dawnstart_minutes,
            day_start=current_app.settings.daystart_minutes,
            dusk=current_app.settings.duskend_minutes,
            day_end=current_app.settings.dayend_minutes,
            times=current_app.settings.times,
        )

        return render_template(
            "schedule.html",
            settings=current_app.settings,
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
    scheduler()


def launch_schedule():
    ret = Popen(["python", "-m", "flask", "scheduler", "start"])
    return ret


def scheduler():
    if not os.path.isfile(current_app.raspiconfig.status_file):
        write_log("Status mjpeg not found")
        return

    write_log("RaspiCam support started")

    fifo_out = current_app.settings.fifo_out
    pipeIn = open_pipe(current_app.settings.fifo_in)

    capture_start = 0
    timeout = 0
    timeout_max = 0
    while timeout_max == 0 or timeout < timeout_max:
        write_log("Scheduler loop is started")
        last_on_cmd = -1
        last_day_period = -1
        # lastDay = -1
        poll_time = current_app.settings.cmd_poll
        slow_poll = 0
        managechecktime = dt.timestamp(dt.utcnow())
        autocameratime = managechecktime
        modechecktime = managechecktime

        if current_app.settings.autocapture_interval > current_app.settings.max_capture:
            autocapturetime = managechecktime
            autocapture = 2
        else:
            autocapturetime = 0
            autocapture = 0

        lastStatusTime = os.path.getmtime(current_app.raspiconfig.status_file)
        while timeout_max == 0 or timeout < timeout_max:
            time.sleep(poll_time)
            cmd = check_motion(pipeIn)
            if cmd == SCHEDULE_STOP and autocapture == 0:
                if last_on_cmd >= 0:
                    write_log("Stop capture requested")
                    send = current_app.settings.commands_off[last_on_cmd]
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

                    send = current_app.settings.commands_on[last_day_period]
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
                current_app.settings.refresh()
            elif cmd != "":
                write_log(f"Ignore FIFO char {cmd}")

            slow_poll -= 1
            if slow_poll < 0:
                slow_poll = 10
                timenow = dt.timestamp(dt.utcnow())
                forcePeriodCheck = 0
                if last_on_cmd >= 0:
                    if current_app.settings.max_capture > 0:
                        if (
                            timenow - capture_start
                        ) >= current_app.settings.max_capture:
                            write_log("Maximum Capture reached. Sending off command")
                            send_cmds(
                                fifo=fifo_out,
                                str_cmd=current_app.settings.commands_off[last_on_cmd],
                            )
                            last_on_cmd = -1
                            autocapture = 0
                            forcePeriodCheck = 1
                if timenow > modechecktime or forcePeriodCheck == 1:
                    modechecktime = timenow + current_app.settings.mode_poll
                    forcePeriodCheck = 0
                    if last_on_cmd < 0:
                        newDayPeriod = wrap_day_period()
                        # newDay = dt.now().strftime("%w")
                        if newDayPeriod != last_day_period:
                            write_log(f"New period detected {newDayPeriod}")
                            send_cmds(
                                fifo=fifo_out,
                                str_cmd=current_app.settings.modes[newDayPeriod],
                                days=current_app.settings.days,
                                period=newDayPeriod,
                            )
                            last_day_period = newDayPeriod
                            # lastDay = newDay
                if timenow > managechecktime:
                    managechecktime = timenow + current_app.settings.management_interval
                    write_log(f"Scheduled management tasks. Next at {managechecktime}")
                    purge_files(
                        current_app.settings.purgevideo_hours,
                        current_app.settings.purgeimage_hours,
                        current_app.settings.purgelapse_hours,
                        current_app.settings.purgespace_level,
                        current_app.settings.purgespace_modeex,
                    )
                    cmd = current_app.settings.management_command
                    if cmd != "":
                        write_log(f"exec_macro: {cmd}")
                        send_cmds(fifo=fifo_out, str_cmd=f"sy {cmd}")
                    delete_log(int(current_app.raspiconfig.log_size))
                if autocapturetime > 0 and (timenow > autocapturetime):
                    autocapturetime = (
                        timenow + current_app.settings.autocapture_interval
                    )
                    write_log("Autocapture request.")
                    autocapture = 1
                if (
                    current_app.settings.autocamera_interval > 0
                    and timenow > autocameratime
                ):
                    autocameratime = timenow + 2
                    modTime = os.path.getmtime(current_app.raspiconfig.status_file)
                    with open(current_app.raspiconfig.status_file, "r") as f:
                        content = f.read()
                        f.close()
                    if content == "halted":
                        if modTime > lastStatusTime:
                            write_log("Autocamera startup")
                            send_cmds(fifo=fifo_out, str_cmd="ru 1")
                    else:
                        if (
                            timenow - modTime
                        ) > current_app.settings.autocamera_interval:
                            write_log("Autocamera shutdown")
                            send_cmds(fifo=fifo_out, str_cmd="md 0;ru 0")
                            lastStatusTime = timenow + 5
                        else:
                            lastStatusTime = timenow


def get_schedule_pid():
    for proc in process_iter():
        if "flask" and "scheduler" in proc.cmdline():
            return proc.pid
    return 0


def wrap_day_period():
    offset = get_time_offset(current_app.settings.gmt_offset)

    sunrise = get_sunrise(
        current_app.settings.latitude, current_app.settings.longitude, offset
    )
    sunset = get_sunset(
        current_app.settings.latitude, current_app.settings.longitude, offset
    )

    local_time = get_current_local_time(offset=offset)

    return day_period(
        local_time=local_time,
        sunrise=sunrise,
        sunset=sunset,
        day_mode=current_app.settings.daymode,
        daw=current_app.settings.dawnstart_minutes,
        day_start=current_app.settings.daystart_minutes,
        dusk=current_app.settings.duskend_minutes,
        day_end=current_app.settings.dayend_minutes,
        times=current_app.settings.times,
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


def purge_files(
    sch_purgevideohours: int,
    sch_purgeimagehours: int,
    sch_purgelapsehours: int,
    sch_purgespacelevel: int,
    sch_purgespacemode: int,
):
    media_path = current_app.raspiconfig.media_path
    purgeCount = 0
    if sch_purgevideohours > 0 or sch_purgeimagehours > 0 or sch_purgelapsehours > 0:
        files = list_folder_files(media_path)
        currentHours = dt.utcnow().timestamp() / 3600
        for file in files:
            if file != "." and file != ".." and is_thumbnail(file):
                fType = get_file_type(file)
                purgeHours = 0
                match fType:
                    case "i":
                        purgeHours = sch_purgeimagehours
                    case "t":
                        purgeHours = sch_purgelapsehours
                    case "v":
                        purgeHours = sch_purgevideohours
                if purgeHours > 0:
                    fModHours = os.path.getmtime(f"{media_path}/{file}").hour()
                    if fModHours > 0 and (currentHours - fModHours) > purgeHours:
                        os.remove(f"{media_path}/{file}")
                        purgeCount += 1
            elif sch_purgevideohours > 0:
                if ".zip" in file:
                    fModHours = os.path.getmtime(f"{media_path}/{file}").hour()
                    if (
                        fModHours > 0
                        and (currentHours - fModHours)  # noqa: W503
                        > sch_purgevideohours  # noqa: W503
                    ):
                        os.remove(f"{media_path}/{file}")
                        write_log("Purged orphan zip file")

    if sch_purgespacemode > 0:
        total, used, free = shutil.disk_usage(f"{media_path}")
        # level = str_replace(
        #     array("%", "G", "B", "g", "b"), "", sch_purgespacelevel
        # )

        match sch_purgespacemode:
            case 1, 2:
                level = min(max(sch_purgespacelevel, 3), 97) * total / 100
            case 3, 4:
                level = level * 1048576.0

        match sch_purgespacemode:
            case 1, 3:
                if free < level:
                    p_files = get_sorted_files(media_path, False)
                    for p_file in p_files:
                        if free < level:
                            free += delete_mediafiles(p_file)
                        purgeCount += 1
            case 2, 4:
                p_files = get_sorted_files(media_path, False)
                for p_file in p_files:
                    del_l = level <= 0
                    level -= delete_mediafiles(p_file, del_l)
                    if del_l:
                        purgeCount += 1

    if purgeCount > 0:
        write_log("Purged purgeCount Files")


def check_motion(pipe):
    if isinstance(pipe, bool):
        return ""
    try:
        ret = os.read(pipe, 0).decode("utf-8")
    except Exception as error:  # noqa: F841
        ret = ""

    return ret


def open_pipe(pipename: str):
    if not os.path.exists(pipename):
        write_log(f"Making Pipe to receive capture commands {pipename}")
        os.popen(f"mkfifo {pipename}")
        os.popen(f"chmod 666 {pipename}")
    else:
        write_log(f"Capture Pipe already exists ({pipename})")

    try:
        pipe = os.open(pipename, os.O_RDONLY | os.O_NONBLOCK)
        return pipe
    except OSError as e:
        write_log(f"Error open pipe {pipename} {str(e)}")


def send_cmds(
    fifo: str, str_cmd: str, days: dict[str, any] | None = None, period: bool = False
):
    if str_cmd and (period is False or is_day_active(days, period)):
        cmds = str_cmd.split(";")
        for cmd in cmds:
            if cmd != "":
                cmd = cmd.strip()
                send_pipe(fifo, cmd)
                time.sleep(0.2)


# functions to find and delete data files
def get_sorted_files(folder, ascending=True):
    scanfiles = list_folder_files(folder)
    files = {}
    for file in scanfiles:
        if file != "." and file != ".." and is_thumbnail(file):
            fDate = os.path.getmtime(f"{folder}/{file}").hour()
            files[file] = fDate
    if ascending:
        files.sort()
    else:
        files.sort(reverse=True)
    return files.keys()


def is_day_active(days, period: int) -> bool:
    if days:
        day = int(dt.now().strftime("%w"))
        return days[str(period)][day] == 1
        # return int(day) in days[str(period)]
    return False