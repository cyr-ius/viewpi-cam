import os
import time
from datetime import datetime as dt

from ..const import (
    SCHEDULE_AUTOCAMERAINTERVAL,
    SCHEDULE_AUTOCAPTUREINTERVAL,
    SCHEDULE_CMDPOLL,
    SCHEDULE_COMMANDSOFF,
    SCHEDULE_COMMANDSON,
    SCHEDULE_FIFOIN,
    SCHEDULE_MANAGEMENTCOMMAND,
    SCHEDULE_MANAGEMENTINTERVAL,
    SCHEDULE_MAXCAPTURE,
    SCHEDULE_MODEPOLL,
    SCHEDULE_MODES,
    SCHEDULE_RESET,
    SCHEDULE_START,
    SCHEDULE_STOP,
    SCHEDULE_GMTOFFSET,
    SCHEDULE_LONGITUDE,
    SCHEDULE_LATITUDE,
    SCHEDULE_DAYMODE,
    SCHEDULE_DAYSTARTMINUTES,
    SCHEDULE_DAWNSTARTMINUTES,
    SCHEDULE_DUSKENDMINUTES,
    SCHEDULE_DAYENDMINUTES,
    SCHEDULE_TIMES,
    SCHEDULE_FIFOOUT,
    SCHEDULE_DAYS,
    SCHEDULE_PURGEVIDEOHOURS,
    SCHEDULE_PURGEIMAGEHOURS,
    SCHEDULE_PURGELAPSEHOURS,
    SCHEDULE_PURGESPACELEVEL,
    SCHEDULE_PURGESPACEMODE,
)
from app.helpers.schedule import (
    day_period,
    get_time_offset,
    get_current_local_time,
    get_sunrise,
    get_sunset,
)
from app.helpers.filer import (
    delete_log,
    file_get_content,
    open_pipe,
    purge_files,
    send_cmds,
    write_log,
    check_motion,
    get_log_size,
    get_settings,
    file_exists,
)


def wrap_day_period(settings):
    offset = get_time_offset(settings[SCHEDULE_GMTOFFSET])

    sunrise = get_sunrise(
        settings[SCHEDULE_LATITUDE], settings[SCHEDULE_LONGITUDE], offset
    )
    sunset = get_sunset(
        settings[SCHEDULE_LATITUDE], settings[SCHEDULE_LONGITUDE], offset
    )

    local_time = get_current_local_time(offset=offset)

    return day_period(
        local_time=local_time,
        sunrise=sunrise,
        sunset=sunset,
        day_mode=settings[SCHEDULE_DAYMODE],
        daw=settings[SCHEDULE_DAWNSTARTMINUTES],
        day_start=settings[SCHEDULE_DAYSTARTMINUTES],
        dusk=settings[SCHEDULE_DUSKENDMINUTES],
        day_end=settings[SCHEDULE_DAYENDMINUTES],
        times=settings[SCHEDULE_TIMES],
    )


def scheduler():
    basedir = os.path.abspath(os.path.abspath(os.path.dirname(__file__)))
    settings = get_settings()
    if len(settings) == 0:
        write_log("Setttings for scheduler not found")
        return
    if not file_exists(f"{basedir}/status_mjpeg.txt"):
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
        poll_time = settings[SCHEDULE_CMDPOLL]
        slow_poll = 0
        managechecktime = dt.timestamp(dt.utcnow())
        autocameratime = managechecktime
        modechecktime = managechecktime

        if settings[SCHEDULE_AUTOCAPTUREINTERVAL] > settings[SCHEDULE_MAXCAPTURE]:
            autocapturetime = managechecktime
            autocapture = 2
        else:
            autocapturetime = 0
            autocapture = 0

        lastStatusTime = os.path.getmtime(f"{basedir}/status_mjpeg.txt")
        while timeout_max == 0 or timeout < timeout_max:
            time.sleep(poll_time)
            cmd = check_motion(pipeIn)
            if cmd == SCHEDULE_STOP and autocapture == 0:
                if last_on_cmd >= 0:
                    write_log("Stop capture requested")
                    send = settings[SCHEDULE_COMMANDSOFF][last_on_cmd]
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

                    send = settings[SCHEDULE_COMMANDSON][last_day_period]
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
                    if settings[SCHEDULE_MAXCAPTURE] > 0:
                        if (timenow - capture_start) >= settings[SCHEDULE_MAXCAPTURE]:
                            write_log("Maximum Capture reached. Sending off command")
                            send_cmds(
                                fifo=fifo_out,
                                str_cmd=settings[SCHEDULE_COMMANDSOFF][last_on_cmd],
                            )
                            last_on_cmd = -1
                            autocapture = 0
                            forcePeriodCheck = 1
                if timenow > modechecktime or forcePeriodCheck == 1:
                    modechecktime = timenow + settings[SCHEDULE_MODEPOLL]
                    forcePeriodCheck = 0
                    if last_on_cmd < 0:
                        newDayPeriod = wrap_day_period(settings)
                        # newDay = dt.now().strftime("%w")
                        if newDayPeriod != last_day_period:
                            write_log(f"New period detected {newDayPeriod}")
                            send_cmds(
                                fifo=fifo_out,
                                str_cmd=settings[SCHEDULE_MODES][newDayPeriod],
                                days=settings[SCHEDULE_DAYS],
                                period=newDayPeriod,
                            )
                            last_day_period = newDayPeriod
                            # lastDay = newDay
                if timenow > managechecktime:
                    managechecktime = timenow + settings[SCHEDULE_MANAGEMENTINTERVAL]
                    write_log(f"Scheduled management tasks. Next at {managechecktime}")
                    purge_files(
                        settings[SCHEDULE_PURGEVIDEOHOURS],
                        settings[SCHEDULE_PURGEIMAGEHOURS],
                        settings[SCHEDULE_PURGELAPSEHOURS],
                        settings[SCHEDULE_PURGESPACELEVEL],
                        settings[SCHEDULE_PURGESPACEMODE],
                    )
                    cmd = settings[SCHEDULE_MANAGEMENTCOMMAND]
                    if cmd != "":
                        write_log(f"exec_macro: {cmd}")
                        send_cmds(fifo=fifo_out, str_cmd=f"sy {cmd}")
                    delete_log(get_log_size())
                if autocapturetime > 0 and (timenow > autocapturetime):
                    autocapturetime = timenow + settings[SCHEDULE_AUTOCAPTUREINTERVAL]
                    write_log("Autocapture request.")
                    autocapture = 1
                if (
                    settings[SCHEDULE_AUTOCAMERAINTERVAL] > 0
                ) and timenow > autocameratime:
                    autocameratime = timenow + 2
                    modTime = os.path.getmtime(f"{basedir}/status_mjpeg.txt")
                    if file_get_content(f"{basedir}/status_mjpeg.txt") == "halted":
                        if modTime > lastStatusTime:
                            write_log("Autocamera startup")
                            send_cmds(fifo=fifo_out, str_cmd="ru 1")
                    else:
                        if (timenow - modTime) > settings[SCHEDULE_AUTOCAMERAINTERVAL]:
                            write_log("Autocamera shutdown")
                            send_cmds(fifo=fifo_out, str_cmd="md 0;ru 0")
                            lastStatusTime = timenow + 5
                        else:
                            lastStatusTime = timenow
            slow_poll -= 1
