"""Blueprint Scheduler."""
import os
import shutil
import time
import zoneinfo
from datetime import datetime as dt
from datetime import timedelta as td
from subprocess import PIPE, Popen

import pytz
from flask import Blueprint
from flask import current_app as ca
from flask import render_template, request
from flask.cli import with_appcontext
from suntime import Sun

from ..const import SCHEDULE_RESET, SCHEDULE_START, SCHEDULE_STOP
from ..helpers.decorator import auth_required
from ..helpers.filer import (delete_log, delete_mediafiles, get_file_type,
                             get_pid, is_thumbnail, list_folder_files,
                             write_log)
from ..helpers.raspiconfig import RaspiConfigError

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
    """Index page."""
    if request.method == "POST" and (action := request.json.pop("action", None)):
        try:
            match action:
                case "start":
                    launch_schedule()
                    message = "Start scheduler"
                case "stop":
                    pid = get_pid("scheduler")
                    Popen(f"kill {pid}", shell=True)
                    message = "Stop scheduler"
                case "save":
                    message = "Saved schedule settings"
                    cur_gmt = ca.settings.gmt_offset
                    ca.settings.update(**request.json)
                    if (timezone := ca.settings.gmt_offset) != cur_gmt:
                        write_log(f"Set timezone {timezone}")
                        Popen(
                            f"ln -fs /usr/share/zoneinfo/{timezone} /etc/localtime",
                            shell=True,
                        )
                    send_motion(SCHEDULE_RESET)
                case "backup":
                    message = "Backed up schedule settings"
                    ca.settings.backup()
                case "restore":
                    message = "Restored up schedule settings"
                    ca.settings.restore()

            write_log(message)
            msg = {"type": "success", "message": message}

        except RaspiConfigError as error:
            write_log(str(error))
            msg = {"type": "error", "message": str(error)}

        return msg

    if request.method == "GET":
        offset = get_time_offset(ca.settings.gmt_offset)

        sunrise = get_sunrise(ca.settings.latitude, ca.settings.longitude, offset)
        sunset = get_sunset(ca.settings.latitude, ca.settings.longitude, offset)

        local_time = get_current_local_time(offset=offset)

        int_period = day_period(
            local_time=local_time,
            sunrise=sunrise,
            sunset=sunset,
            day_mode=ca.settings.daymode,
            daw=ca.settings.dawnstart_minutes,
            day_start=ca.settings.daystart_minutes,
            dusk=ca.settings.duskend_minutes,
            day_end=ca.settings.dayend_minutes,
            times=ca.settings.times,
        )

        return render_template(
            "schedule.html",
            control_file=ca.raspiconfig.control_file,
            current_time=local_time.strftime("%H:%M"),
            motion_pipe=ca.raspiconfig.motion_pipe,
            offset=offset,
            period=int_period,
            schedule_pid=get_pid("scheduler"),
            settings=ca.settings,
            sunrise=sunrise.strftime("%H:%M"),
            sunset=sunset.strftime("%H:%M"),
            timezones=zoneinfo.available_timezones(),
        )


@bp.route("/period", methods=["POST"])
def period():
    offset = get_time_offset(ca.settings.gmt_offset)
    sunrise = get_sunrise(ca.settings.latitude, ca.settings.longitude, offset)
    sunset = get_sunset(ca.settings.latitude, ca.settings.longitude, offset)
    local_time = get_current_local_time(offset=offset)
    return {
        "period": day_period(
            local_time=local_time,
            sunrise=sunrise,
            sunset=sunset,
            day_mode=int(request.json.get("daymode")),
            daw=ca.settings.dawnstart_minutes,
            day_start=ca.settings.daystart_minutes,
            dusk=ca.settings.duskend_minutes,
            day_end=ca.settings.dayend_minutes,
            times=ca.settings.times,
        )
    }


@bp.cli.command("stop", short_help="Stop scheduler task")
@with_appcontext
def stop_scheduler() -> int | None:
    """Stop scheduler."""
    pid = get_pid("scheduler")
    Popen(f"kill {pid}", shell=True)


@bp.cli.command("start", short_help="Start scheduler task")
@with_appcontext
def start_scheduler() -> int | None:
    """Start scheduler."""
    scheduler()


def launch_schedule():
    """Run scheduler."""
    if not get_pid("scheduler"):
        Popen(["flask", "scheduler", "start"], stdout=PIPE)


def scheduler():
    """Scheduler."""

    def dt_now():
        offset = get_time_offset(ca.settings.gmt_offset)
        return get_current_local_time(offset=offset)

    if not os.path.isfile(ca.raspiconfig.status_file):
        write_log("Status mjpeg not found")
        return

    write_log("RaspiCam support started")

    motion_fifo_in = open_pipe(ca.raspiconfig.motion_pipe)

    capture_start = 0
    timeout = 0
    timeout_max = 0
    while timeout_max == 0 or timeout < timeout_max:
        write_log("Scheduler loop is started")
        last_on_cmd = -1
        last_day_period = -1
        poll_time = ca.settings.cmd_poll
        slow_poll = 0
        managechecktime = dt.timestamp(dt_now())
        autocameratime = managechecktime
        modechecktime = managechecktime

        if ca.settings.autocapture_interval > ca.settings.max_capture:
            autocapturetime = managechecktime
            autocapture = 2
        else:
            autocapturetime = 0
            autocapture = 0

        last_status_time = os.path.getmtime(ca.raspiconfig.status_file)
        while timeout_max == 0 or timeout < timeout_max:
            time.sleep(poll_time)
            cmd = check_motion(motion_fifo_in)
            if cmd == SCHEDULE_STOP and autocapture == 0:
                if last_on_cmd >= 0:
                    write_log("Stop capture requested")
                    send = ca.settings.commands_off[last_on_cmd]
                    if send:
                        send_cmds(str_cmd=send, days=last_day_period)
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

                    send = ca.settings.commands_on[last_day_period]
                    if send:
                        send_cmds(str_cmd=send, days=last_day_period)
                        last_on_cmd = last_day_period
                        capture_start = dt.timestamp(dt_now())
                else:
                    write_log(
                        "Start capture request ignored, day period not initialised yet"
                    )
            elif cmd == SCHEDULE_RESET:
                write_log("Reload parameters command requested")
                break
            elif cmd != "":
                write_log(f"Ignore FIFO char {cmd}")

            slow_poll -= 1
            if slow_poll < 0:
                slow_poll = 10
                timenow = dt.timestamp(dt_now())
                force_period_check = 0
                if last_on_cmd >= 0:
                    if ca.settings.max_capture > 0:
                        if (timenow - capture_start) >= ca.settings.max_capture:
                            write_log("Maximum Capture reached. Sending off command")
                            send_cmds(str_cmd=ca.settings.commands_off[last_on_cmd])
                            last_on_cmd = -1
                            autocapture = 0
                            force_period_check = 1
                if timenow > modechecktime or force_period_check == 1:
                    modechecktime = timenow + ca.settings.mode_poll
                    force_period_check = 0
                    if last_on_cmd < 0:
                        new_day_period = wrap_day_period()
                        if new_day_period != last_day_period:
                            write_log(f"New period detected {new_day_period}")
                            send_cmds(
                                str_cmd=ca.settings.modes[new_day_period],
                                days=ca.settings.days,
                                bool_period=new_day_period,
                            )
                            last_day_period = new_day_period
                if timenow > managechecktime:
                    managechecktime = timenow + ca.settings.management_interval
                    write_log(
                        f"Scheduled management tasks. Next at {time.ctime(managechecktime)}"
                    )
                    purge_files(
                        ca.settings.purgevideo_hours,
                        ca.settings.purgeimage_hours,
                        ca.settings.purgelapse_hours,
                        ca.settings.purgespace_level,
                        ca.settings.purgespace_modeex,
                    )
                    cmd = ca.settings.management_command
                    if cmd != "":
                        write_log(f"exec_macro: {cmd}")
                        send_cmds(str_cmd=f"sy {cmd}")
                    delete_log(int(ca.raspiconfig.log_size))
                if autocapturetime > 0 and (timenow > autocapturetime):
                    autocapturetime = timenow + ca.settings.autocapture_interval
                    write_log("Autocapture request.")
                    autocapture = 1
                if ca.settings.autocamera_interval > 0 and timenow > autocameratime:
                    autocameratime = timenow + 2
                    mod_time = os.path.getmtime(ca.raspiconfig.status_file)
                    with open(
                        ca.raspiconfig.status_file, mode="r", encoding="utf-8"
                    ) as file:
                        content = file.read()
                        file.close()
                    if content == "halted":
                        if mod_time > last_status_time:
                            write_log("Autocamera startup")
                            send_cmds(str_cmd="ru 1")
                    else:
                        if (timenow - mod_time) > ca.settings.autocamera_interval:
                            write_log("Autocamera shutdown")
                            send_cmds(str_cmd="md 0;ru 0")
                            last_status_time = timenow + 5
                        else:
                            last_status_time = timenow


def wrap_day_period():
    """Wrap day period."""
    offset = get_time_offset(ca.settings.gmt_offset)

    sunrise = get_sunrise(ca.settings.latitude, ca.settings.longitude, offset)
    sunset = get_sunset(ca.settings.latitude, ca.settings.longitude, offset)

    local_time = get_current_local_time(offset=offset)

    return day_period(
        local_time=local_time,
        sunrise=sunrise,
        sunset=sunset,
        day_mode=ca.settings.daymode,
        daw=ca.settings.dawnstart_minutes,
        day_start=ca.settings.daystart_minutes,
        dusk=ca.settings.duskend_minutes,
        day_end=ca.settings.dayend_minutes,
        times=ca.settings.times,
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
    """Get day period."""
    match day_mode:
        case 0:
            if local_time < (sunrise + td(minutes=daw)).replace(tzinfo=None):
                d_period = 1
            elif local_time < (sunrise + td(minutes=day_start)).replace(tzinfo=None):
                d_period = 2
            elif local_time > (sunset + td(minutes=dusk)).replace(tzinfo=None):
                d_period = 1
            elif local_time > (sunset + td(minutes=day_end)).replace(tzinfo=None):
                d_period = 4
            else:
                d_period = 3
        case 1:
            d_period = 0
        case 2:
            d_period = find_fixed_time_period(times, local_time)

    return d_period


def get_current_local_time(minute: bool = False, offset: td = None) -> dt | int:
    """Get current local time."""
    now = dt.utcnow()
    if offset:
        now = now + offset
    if minute:
        return now.hour * 60 + now.minute
    return now


def get_sunrise(latitude, longitude, offset: td) -> dt:
    """Get sunrise time."""
    sun = Sun(latitude, longitude)
    day_sunrise: dt = sun.get_sunrise_time()
    return day_sunrise + offset


def get_sunset(latitude, longitude, offset: td) -> dt:
    """Get sunset time."""
    sun = Sun(latitude, longitude)
    day_sunset: dt = sun.get_sunset_time()
    return day_sunset + offset


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


def find_fixed_time_period(times, c_mins: dt) -> int:
    int_period = len(times) - 1
    max_less_v = -1
    for str_time in times:
        f_mins = dt.strptime(str_time, "%H:%M")
        if (
            f_mins.time() < c_mins.time()
            and (f_mins.hour * 60 + f_mins.minute) > max_less_v
        ):
            max_less_v = f_mins.hour * 60 + f_mins.minute
            int_period = times.index(str_time)

    return int_period + 5


def purge_files(
    sch_purgevideohours: int,
    sch_purgeimagehours: int,
    sch_purgelapsehours: int,
    sch_purgespacelevel: int,
    sch_purgespacemode: int,
):
    """Purge files."""
    media_path = ca.raspiconfig.media_path
    purge_count = 0
    if sch_purgevideohours > 0 or sch_purgeimagehours > 0 or sch_purgelapsehours > 0:
        files = list_folder_files(media_path)
        current_hours = dt.utcnow().timestamp() / 3600
        for file in files:
            if file != "." and file != ".." and is_thumbnail(file):
                f_type = get_file_type(file)
                purge_hours = 0
                match f_type:
                    case "i":
                        purge_hours = sch_purgeimagehours
                    case "t":
                        purge_hours = sch_purgelapsehours
                    case "v":
                        purge_hours = sch_purgevideohours
                if purge_hours > 0:
                    f_mod_hours = os.path.getmtime(f"{media_path}/{file}").hour()
                    if f_mod_hours > 0 and (current_hours - f_mod_hours) > purge_hours:
                        os.remove(f"{media_path}/{file}")
                        purge_count += 1
            elif sch_purgevideohours > 0:
                if ".zip" in file:
                    f_mod_hours = os.path.getmtime(f"{media_path}/{file}").hour()
                    if (
                        f_mod_hours > 0
                        and (current_hours - f_mod_hours)  # noqa: W503
                        > sch_purgevideohours  # noqa: W503
                    ):
                        os.remove(f"{media_path}/{file}")
                        write_log("Purged orphan zip file")

    if sch_purgespacemode > 0:
        total, _, free = shutil.disk_usage(f"{media_path}")

        match sch_purgespacemode:
            case 1 | 2:
                level = min(max(sch_purgespacelevel, 3), 97) * total / 100
            case 3 | 4:
                level = sch_purgespacelevel * 1048576.0

        match sch_purgespacemode:
            case 1 | 3:
                if free < level:
                    p_files = get_sorted_files(media_path, False)
                    for p_file in p_files:
                        if free < level:
                            free += delete_mediafiles(p_file)
                        purge_count += 1
            case 2 | 4:
                p_files = get_sorted_files(media_path, False)
                for p_file in p_files:
                    del_l = level <= 0
                    level -= delete_mediafiles(p_file, del_l)
                    if del_l:
                        purge_count += 1

    if purge_count > 0:
        write_log("Purged purge_count Files")


def check_motion(pipe):
    if isinstance(pipe, bool):
        return ""
    try:
        ret = os.read(pipe, 1).decode("utf-8").replace("\n", "")
    except Exception:  # pylint: disable=W0718
        ret = ""
    return ret


def open_pipe(pipename: str):
    if not os.path.exists(pipename):
        write_log(f"Making Pipe to receive capture commands {pipename}")
        Popen(f"mkfifo {pipename}", shell=True)
        Popen(f"chmod 666 {pipename}", shell=True)
    else:
        write_log(f"Capture Pipe already exists ({pipename})")

    try:
        pipe = os.open(pipename, os.O_RDONLY | os.O_NONBLOCK)
        return pipe
    except OSError as error:
        write_log(f"Error open pipe {pipename} {str(error)}")


def send_motion(cmd: str) -> None:
    """Send command to pipe."""
    try:
        pipe = os.open(ca.raspiconfig.motion_pipe, os.O_WRONLY | os.O_NONBLOCK)
        os.write(pipe, f"{cmd}\n".encode("utf-8"))
        os.close(pipe)
        write_log(f"Motion - Send {cmd}")
    except Exception as error:  # pylint: disable=W0718
        write_log(str(error))


def send_cmds(
    str_cmd: str, days: dict[str, any] | None = None, bool_period: bool = False
):
    """Send multiple commands to FIFO."""
    if str_cmd and (bool_period is False or is_day_active(days, bool_period)):
        cmds = str_cmd.split(";")
        for cmd in cmds:
            if cmd != "":
                cmd = cmd.strip()
                ca.raspiconfig.send(cmd)
                time.sleep(0.2)


# functions to find and delete data files
def get_sorted_files(folder: str, ascending: bool = True) -> list:
    scanfiles = list_folder_files(folder)
    files = {}
    for file in scanfiles:
        if file != "." and file != ".." and is_thumbnail(file):
            f_date = os.path.getmtime(f"{folder}/{file}")
            files[file] = f_date

    return sorted(files, reverse=ascending is False)


def is_day_active(days, bool_period: int) -> bool:
    if days:
        day = int(dt.now().strftime("%w"))
        return days[str(bool_period)][day] == 1
    return False
