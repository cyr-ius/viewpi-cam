"""Blueprint Scheduler."""

import os
import time
from datetime import datetime as dt
from subprocess import PIPE, Popen

from flask import Blueprint
from flask import current_app as ca
from flask.cli import with_appcontext

from ..helpers.utils import get_pid, write_log
from ..models import Settings as settings_db

bp = Blueprint(
    "rsync",
    __name__,
    template_folder="templates",
    url_prefix="/rsync",
    cli_group="rsync",
)
bp.cli.short_help = "Stop/Start rsync"


@bp.cli.command("stop", short_help="Stop rsync task")
@with_appcontext
def stop() -> None:
    """Stop rsync."""
    pid = get_pid(["*/flask", "rsync"])
    Popen(f"kill {pid}", shell=True)


@bp.cli.command("start", short_help="Start rsync task")
@with_appcontext
def start() -> None:
    """Start rsync."""
    rsync()


def rsync() -> None:
    """Rsync daemon."""

    write_log("Rsync support started")

    settings = settings_db.query.first()
    poll_time = settings.data["cmd_poll"]
    media_path = ca.raspiconfig.media_path

    if rs_pwd := settings.data.get("rs_pwd"):
        os.environ["RSYNC_PASSWORD"] = rs_pwd
    else:
        write_log("[Rsync] Password not found", "error")
        return

    while settings.data.get("rs_direction") or settings.data.get(
        "rs_remote_module_name"
    ):
        ca.logger.debug("Rsync check")
        if not isinstance(settings.data["rs_options"], list):
            settings.data["rs_options"] = [settings.data["rs_options"]]

        options = " ".join(settings.data["rs_options"])
        if settings.data["rs_mode"] == "SSH":
            cmd = f"rsync -v {options} --no-perms --exclude '*.info' --exclude '*.th.jpg' {media_path}/ -e ssh {settings.data['rs_user']}@{settings.data['rs_remote_host']}:/{settings.data['rs_direction']}"
        else:
            cmd = f"rsync -v {options} --no-perms --exclude '*.info' --exclude '*.th.jpg' {media_path}/ {settings.data['rs_user']}@{settings.data['rs_remote_host']}::{settings.data['rs_remote_module_name']}"

        print_msg(cmd)

        if not get_pid("*/rsync"):
            process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, text="utf-8")
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
                break
            write_log("[RSync] Successful")
        time.sleep(poll_time * 1000)


def print_msg(msg):
    msg = msg.strip()
    str_now = dt.now().strftime("%Y/%m/%d %H:%M:%S,%f")[:-3]
    if msg != "":
        print(f"[{str_now}] [rsync.py] INFO - {msg}")
