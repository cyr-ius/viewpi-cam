"""Utils functions."""
import hashlib
import os
import shutil
from datetime import datetime as dt
from subprocess import PIPE, Popen

from flask import current_app as ca
from psutil import process_iter


def get_pid(pid_type):
    """Return process id."""
    for proc in process_iter():
        if pid_type == "scheduler":
            if "flask" and "scheduler" in proc.cmdline():
                return proc.pid
        if pid_type in proc.cmdline():
            return proc.pid
    return 0


def execute_cmd(cmd):
    """Execute shell command."""
    return Popen(cmd, stdout=PIPE, shell=True)


def write_log(msg: str) -> None:
    """Write log."""
    log_file = ca.raspiconfig.log_file
    str_now = dt.now().strftime("%Y/%m/%d %H:%M:%S")
    ca.logger.info(msg)

    mode = "w" if not os.path.isfile(log_file) else "a"
    with open(log_file, mode=mode, encoding="utf-8") as file:
        file.write(f"{{{str_now}}} {msg}\n")


def delete_log(log_size: int) -> None:
    """Delete log."""
    log_file = ca.raspiconfig.log_file
    if os.path.isfile(log_file):
        log_lines = open(log_file, mode="r", encoding="utf-8").readlines()
        if len(log_lines) > log_size:
            with open(log_file, mode="w", encoding="utf-8") as file:
                file.write(log_lines[:log_size])
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


def hash_password(password: str) -> str:
    """Hash string text."""
    salt = ca.config["SECRET_KEY"]
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return hashed.hex()
