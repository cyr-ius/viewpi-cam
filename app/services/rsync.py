"""Rsync service."""

import os
from datetime import datetime as dt
from subprocess import PIPE, Popen

from flask import current_app as ca

from ..helpers.utils import get_pid, write_log
from ..models import Settings as settings_db


def rsync() -> None:
    """Rsync execute."""

    write_log("Rsync support started")
    settings = settings_db.query.first()
    media_path = ca.raspiconfig.media_path
    binary = ca.config["RSYNC_BINARY"]
    options = settings.data.get("rs_options", [])
    pwd = settings.data.get("rs_pwd")
    mode = settings.data.get("rs_mode")
    user = settings.data.get("rs_user")
    host = settings.data.get("rs_remote_host")
    direction = settings.data.get("rs_direction")

    if pwd is None:
        write_log("[Rsync] Password not found", "error")
        return False

    if not isinstance(options, list):
        options = [options]

    options = " ".join(options)

    if mode == "SSH":
        ssh = "-e ssh"
        shee = "/"
    else:
        ssh = ""
        shee = ":"

    cmd = f"{binary} -v {options} --no-perms --exclude '*.info' --exclude '*.th.jpg' {ssh} {media_path}/ {user}@{host}:{shee}{direction}"
    print_msg(cmd)

    if not get_pid("/usr/bin/rsync"):
        process = Popen(
            cmd,
            shell=True,
            stdout=PIPE,
            stderr=PIPE,
            text="utf-8",
            env=dict(os.environ, RSYNC_PASSWORD=pwd),
        )
        for stdout_line in iter(process.stdout.readline, ""):
            print_msg(stdout_line)
        process.stdout.close()
        for stderr_line in iter(process.stderr.readline, ""):
            print_msg(stderr_line)
            write_log(stderr_line, "error")
        process.stderr.close()
        return_code = process.wait()
        if return_code > 0:
            msg = f"[RSync] Error {return_code}"
            print_msg(msg)
            write_log(msg, "error")
            return False
        write_log("[RSync] Successful")
    return True


def print_msg(msg):
    msg = msg.strip()
    str_now = dt.now().strftime("%Y/%m/%d %H:%M:%S,%f")[:-3]
    if msg != "":
        print(f"[{str_now}] [rsync.py] INFO - {msg}")
