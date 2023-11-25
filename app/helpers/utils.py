"""Utils functions."""
import os
import re
import shutil
from datetime import datetime as dt
from subprocess import PIPE, Popen

from flask import current_app as ca
from flask import request, session
from psutil import process_iter

from ..services.handle import ViewPiCamException


def reverse(url: str) -> bool:
    """Check url exists in url_map."""
    url = url.replace(request.host_url, "/")
    for rule in ca.url_map.iter_rules():
        url_rule = re.sub("<.*>", "[^/]*", rule.rule)
        p = re.compile(rf"^{url_rule}$")
        if check := bool(p.match(url)):
            return check
    return False


def get_pid(pid_type: str) -> int:
    """Return process id."""
    for proc in process_iter():
        if pid_type == "scheduler":
            if "flask" and "scheduler" in proc.cmdline():
                return proc.pid
        if pid_type in proc.cmdline():
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


def write_log(msg: str) -> None:
    """Write log."""
    log_file = ca.raspiconfig.log_file
    str_now = dt.now().strftime("%Y/%m/%d %H:%M:%S")
    ca.logger.info(msg)

    mode = "w" if not os.path.isfile(log_file) else "a"
    with open(log_file, mode=mode, encoding="utf-8") as file:
        file.write(f'{{"datetime":{str_now},"msg":"{msg}"}}\n')


def delete_log(log_size: int) -> None:
    """Delete log."""
    log_file = ca.raspiconfig.log_file
    if os.path.isfile(log_file):
        log_lines = open(log_file, mode="r", encoding="utf-8").readlines()
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


def get_locale() -> str | list[str]:
    if (user := ca.usrmgmt.get(id=session.get("id"))) and hasattr(user, "locale"):
        session["locale"] = user.locale
        return user.locale
    return request.accept_languages.best_match(["de", "fr", "en"])


def get_timezone() -> str | list[str]:
    return ca.settings.gmt_offset
