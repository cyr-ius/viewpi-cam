"""Blueprint Scheduler."""

import os
import shutil
import time
from datetime import datetime as dt
from subprocess import Popen
from typing import Any

from flask import Blueprint
from flask import current_app as ca
from flask.cli import with_appcontext

from ..apis.schedule import dt_now, get_calendar
from ..helpers.database import update_img_db
from ..helpers.fifo import open_pipe, read_pipe
from ..helpers.filer import (
    delete_mediafiles,
    get_file_type,
    get_sorted_files,
    is_thumbnail,
    list_folder_files,
)
from ..helpers.utils import delete_log, get_pid, get_settings, write_log
from ..models import Scheduler as scheduler_db
from ..models import db
from ..services.raspiconfig import RaspiConfigError
from ..services.rsync import rsync

bp = Blueprint("daemon", __name__, url_prefix="/daemon", cli_group="scheduler")

bp.cli.short_help = "Stop/Start scheduler"


@bp.cli.command("stop", short_help="Stop scheduler task")
@with_appcontext
def stop_scheduler() -> None:
    """Stop scheduler."""
    pid = get_pid(["*/flask", "scheduler"])
    Popen(f"kill {pid}", shell=True)


@bp.cli.command("start", short_help="Start scheduler task")
@with_appcontext
def start_scheduler() -> None:
    """Start scheduler."""
    scheduler()


def scheduler() -> None:
    """Scheduler."""
    if not os.path.isfile(ca.raspiconfig.status_file):
        write_log("[Raspimjpeg] Status mjpeg not found", "error")
        return

    write_log("RaspiCam support started")

    motion_fifo_in = open_pipe(ca.raspiconfig.motion_pipe)

    capture_start = 0
    timeout = 0
    timeout_max = 0
    while timeout_max == 0 or timeout < timeout_max:
        write_log("Scheduler loop is started")
        db.session.remove()
        settings = get_settings()
        last_on_cmd = None
        last_day_period = None
        poll_time = settings["cmd_poll"]
        slow_poll = 0
        managechecktime = dt.timestamp(dt_now())
        autocameratime = managechecktime
        modechecktime = managechecktime

        if settings["autocapture_interval"] > settings["max_capture"]:
            autocapturetime = managechecktime
            autocapture = 2
        else:
            autocapturetime = 0
            autocapture = 0

        last_status_time = os.path.getmtime(ca.raspiconfig.status_file)
        while timeout_max == 0 or timeout < timeout_max:
            time.sleep(poll_time)
            cmd = read_pipe(motion_fifo_in)
            if cmd == ca.config["SCHEDULE_STOP"] and autocapture == 0:
                if last_on_cmd:
                    write_log("Stop capture requested")
                    schedule = db.session.scalars(
                        db.select(scheduler_db).filter_by(period=last_day_period)
                    ).one()
                    send = schedule.command_off
                    settings["last_detection_stop"] = str(dt_now())
                    db.session.commit()
                    if send:
                        send_cmds(str_cmd=send, days=schedule.calendars)
                        last_on_cmd = None
                else:
                    write_log("Stop capture request ignored, already stopped")
            elif cmd == ca.config["SCHEDULE_START"] or autocapture == 1:
                if last_day_period:
                    if autocapture == 1:
                        autocapture = 2
                        write_log("Start triggered by autocapture")
                    else:
                        write_log("Start capture requested from Pipe")
                        settings["last_detection_start"] = str(dt_now())
                        db.session.commit()
                    schedule = db.session.scalars(
                        db.select(scheduler_db).filter_by(period=last_day_period)
                    ).one()
                    send = schedule.command_on
                    if send:
                        send_cmds(str_cmd=send, days=schedule.calendars)
                        last_on_cmd = last_day_period
                        capture_start = dt.timestamp(dt_now())
                else:
                    write_log(
                        "Start capture request ignored, day period not initialised yet"
                    )
            elif cmd == ca.config["SCHEDULE_RESET"]:
                write_log("Reload parameters command requested")
                break
            elif cmd in [
                ca.config["SCHEDULE_UPDATE_VID"],
                ca.config["SCHEDULE_UPDATE_IMG"],
            ]:
                update_img_db()
                if settings.get("rs_enabled"):
                    rsync()
            elif cmd != "":
                write_log(f"Ignore FIFO char {cmd}")

            slow_poll -= 1
            if slow_poll < 0:
                slow_poll = 10
                timenow = dt.timestamp(dt_now())
                force_period_check = 0
                if last_on_cmd:
                    if settings["max_capture"] > 0:
                        if (timenow - capture_start) >= settings["max_capture"]:
                            write_log("Maximum Capture reached. Sending off command")
                            schedule = db.session.scalars(
                                db.select(scheduler_db).filter_by(
                                    period=last_day_period
                                )
                            ).one()
                            send_cmds(str_cmd=schedule.command_off)
                            last_on_cmd = None
                            autocapture = 0
                            force_period_check = 1
                if timenow > modechecktime or force_period_check == 1:
                    modechecktime = timenow + settings["mode_poll"]
                    force_period_check = 0
                    if last_on_cmd is None:
                        new_day_period = get_calendar(settings["daymode"])
                        if new_day_period != last_day_period:
                            write_log(f"New period detected {new_day_period}")
                            schedule = db.session.scalars(
                                db.select(scheduler_db).filter_by(period=new_day_period)
                            ).one()
                            send_cmds(str_cmd=schedule.mode, days=schedule.calendars)
                            last_day_period = new_day_period
                if timenow > managechecktime:
                    managechecktime = timenow + settings["management_interval"]
                    write_log(f"Scheduled tasks. Next at {time.ctime(managechecktime)}")
                    purge_files(
                        settings["purgevideo_hours"],
                        settings["purgeimage_hours"],
                        settings["purgelapse_hours"],
                        settings["purgespace_level"],
                        settings["purgespace_modeex"],
                    )
                    cmd = settings.get("management_command")
                    if cmd and cmd != "":
                        write_log(f"exec_macro: {cmd}")
                        send_cmds(str_cmd=f"sy {cmd}")
                    delete_log(int(ca.raspiconfig.log_size))
                if autocapturetime > 0 and (timenow > autocapturetime):
                    autocapturetime = timenow + settings["autocapture_interval"]
                    write_log("Autocapture request.")
                    autocapture = 1
                if settings["autocamera_interval"] > 0 and timenow > autocameratime:
                    autocameratime = timenow + 2
                    mod_time = os.path.getmtime(ca.raspiconfig.status_file)
                    with open(ca.raspiconfig.status_file, encoding="utf-8") as file:
                        content = file.read()
                        file.close()
                    if content == "halted":
                        if mod_time > last_status_time:
                            write_log("Autocamera startup")
                            send_cmds(str_cmd="ru 1")
                    else:
                        if (timenow - mod_time) > settings["autocamera_interval"]:
                            write_log("Autocamera shutdown")
                            send_cmds(str_cmd="md 0;ru 0")
                            last_status_time = timenow + 5
                        else:
                            last_status_time = timenow


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
        timenow = dt.timestamp(dt_now())
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
                    f_mod_hours: dt = os.path.getmtime(f"{media_path}/{file}")
                    diff_hours: dt = dt.fromtimestamp(timenow - f_mod_hours).hour
                    if f_mod_hours > 0 and diff_hours > purge_hours:
                        os.remove(f"{media_path}/{file}")
                        purge_count += 1
            elif sch_purgevideohours > 0:
                if ".zip" in file:
                    f_mod_hours = os.path.getmtime(f"{media_path}/{file}")
                    diff_hours: dt = dt.fromtimestamp(timenow - f_mod_hours).hour
                    if f_mod_hours > 0 and diff_hours > sch_purgevideohours:
                        os.remove(f"{media_path}/{file}")
                        write_log("Purged orphan zip file")

    if sch_purgespacemode > 0:
        total, _, free = shutil.disk_usage(f"{media_path}")

        match sch_purgespacemode:
            case 1 | 2:
                level: float = min(max(sch_purgespacelevel, 3), 97) * total / 100
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


def send_cmds(str_cmd: str, days: dict[str, Any] | None = None) -> None:
    """Send multiple commands to FIFO."""
    if str_cmd and (is_day_active(days) or days is None):
        cmds = str_cmd.split(";")
        for cmd in cmds:
            if cmd != "":
                cmd = cmd.strip()
                try:
                    ca.raspiconfig.send(cmd)
                except RaspiConfigError as error:
                    write_log(f"[Scheduler] Error while send command {error}")
                time.sleep(0.2)


def is_day_active(days: dict[str, Any] | None) -> bool:
    """Return boolean if active day."""
    if days:
        now_day: str = dt_now().strftime("%a")
        for day in days:
            if day.name == now_day:
                return True
    return False
