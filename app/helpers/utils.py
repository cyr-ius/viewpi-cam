"""Utils functions."""

import fnmatch
import json
import os
import re
import shutil
from datetime import datetime as dt
from subprocess import PIPE, Popen
from typing import Any

from flask import current_app as ca
from flask import request
from flask_login import current_user
from psutil import ZombieProcess, process_iter

from ..models import Settings, db
from .exceptions import ViewPiCamException


def reverse(url: str) -> bool:
    """Check url exists in url_map."""
    url = url.replace(request.host_url, "/")
    for rule in ca.url_map.iter_rules():
        url_rule = re.sub("<.*>", "[^/]*", rule.rule)
        p = re.compile(rf"^{url_rule}$")
        if check := bool(p.match(url)):
            return check
    return False


def get_pid(pid_type: str | list[str]) -> int:
    """Return process id."""
    if not isinstance(pid_type, list):
        pid_type = [pid_type]

    for proc in process_iter():
        try:
            cmdline = proc.cmdline()
        except ZombieProcess:
            cmdline = []
        else:
            if all(fnmatch.filter(cmdline, item) for item in pid_type):
                return proc.pid
    return 0


def execute_cmd(cmd: str) -> None:
    """Execute shell command."""
    process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    output, error = process.communicate()
    if process.returncode != 0:
        err = error.decode("utf-8").replace("\n", "")
        raise ViewPiCamException(f"Error execute command ({err})")
    return output.decode("utf-8")


def write_log(msg: str, level: str = "info") -> None:
    """Write log."""
    log_file = ca.raspiconfig.log_file
    str_now = dt.now().strftime("%Y/%m/%d %H:%M:%S")
    getattr(ca.logger, level)(msg)

    mode = "w" if not os.path.isfile(log_file) else "a"
    try:
        with open(log_file, mode=mode, encoding="utf-8") as file:
            line = json.dumps(
                {"datetime": str_now, "level": level.upper(), "msg": msg},
                separators=(",", ":"),
            )
            file.write(line + "\n")
    except FileNotFoundError as error:
        ca.logger.error(error)


def delete_log(log_size: int) -> None:
    """Delete log."""
    log_file = ca.raspiconfig.log_file
    if os.path.isfile(log_file):
        log_lines = open(log_file, encoding="utf-8").readlines()
        if len(log_lines) > log_size:
            with open(log_file, mode="w", encoding="utf-8") as file:
                file.writelines(log_lines[:log_size])
                file.close()


def disk_usage() -> tuple[int, int, int, int, str]:
    """Disk usage."""
    media_path = ca.raspiconfig.media_path
    total, used, free = shutil.disk_usage(f"{media_path}")
    percent_used = round(used / total * 100)
    if percent_used > 98:
        colour = "Red"
    elif percent_used > 90:
        colour = "Orange"
    else:
        colour = "LightGreen"

    return (
        round(total / 1048576),
        round(used / 1048576),
        round(free / 1048576),
        int(percent_used),
        colour,
    )


def get_settings(attr: str = None, default: Any = None) -> dict[str, Any] | None:
    """Return data setting."""
    settings = db.session.scalars(db.select(Settings)).first()
    if getattr(settings, "data", None) and attr:
        return settings.data.get(attr, default)
    if getattr(settings, "data", None):
        return settings.data
    return None


def get_locale() -> str | list[str]:
    """Get locale."""
    if current_user.is_authenticated:
        return current_user.locale
    return request.accept_languages.best_match(["de", "fr", "en"])


def get_timezone() -> str | list[str]:
    """Get timezone."""
    return get_settings("gmt_offset")


def launch_module(module: str, action: str = "start") -> None:
    """Run scheduler."""
    if not get_pid(["*/flask", module]):
        Popen(["flask", module, action])


def allowed_file(filename):
    """Check allowed file extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ca.config["ALLOWED_EXTENSIONS"]
    )


def set_timezone(timezone: str) -> None:
    """Set localtime and timezone."""
    try:
        write_log(f"Set timezone {timezone}")
        execute_cmd(f"copy -f /usr/share/zoneinfo/{timezone} /etc/localtime")
    except Exception as error:
        ca.logger.error(error)
