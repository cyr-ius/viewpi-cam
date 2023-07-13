import os
import time
from datetime import datetime as dt

from ..const import (
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
    SCHEDULE_FIFOIN,
    SCHEDULE_FIFOOUT,
    ATTR_GMTOFFSET,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_MGMTCOMMAND,
    ATTR_MGMTINTERVAL,
    ATTR_MAXCAPTURE,
    ATTR_MODE_POLL,
    ATTR_MODES,
    ATTR_PURGEIMAGEHOURS,
    ATTR_PURGELAPSEHOURS,
    ATTR_PURGESPACELEVEL,
    ATTR_PURGESPACEMODE,
    ATTR_PURGEVIDEOHOURS,
    SCHEDULE_RESET,
    SCHEDULE_START,
    SCHEDULE_STOP,
    ATTR_TIMES,
)
from ..helpers.filer import (
    check_motion,
    delete_log,
    file_exists,
    file_get_content,
    get_log_size,
    get_settings,
    open_pipe,
    purge_files,
    send_cmds,
    write_log,
    get_config,
)
from ..helpers.schedule import (
    day_period,
    get_current_local_time,
    get_sunrise,
    get_sunset,
    get_time_offset,
)


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
