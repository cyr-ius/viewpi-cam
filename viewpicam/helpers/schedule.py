import os
from datetime import datetime as dt
from datetime import timedelta as td
from psutil import process_iter

import pytz
from suntime import Sun


def get_schedule_pid():
    for proc in process_iter():
        if "flask" and "scheduler" in proc.cmdline():
            return proc.pid
    return 0


def start_schedule():
    ret = os.popen("python -m flask scheduler >/dev/null &")
    return ret


def stop_schedule(pid):
    os.popen(f"kill {pid}")


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


def is_day_active(days, period: int) -> bool:
    if days:
        day = dt.now().strftime("%w")
        return int(day) in days[str(period)]
    return False


def check_motion(pipe):
    if isinstance(pipe, bool):
        return ""
    try:
        ret = pipe.read(1)
    except Exception:
        ret = ""
    return ret
