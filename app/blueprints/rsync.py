"""Blueprint Scheduler."""

import os
import re
import time
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

    while settings.data.get("rs_direction") or settings.data.get(
        "rs_remote_module_name"
    ):
        if not isinstance(settings.data["rs_options"], list):
            settings.data["rs_options"] = [settings.data["rs_options"]]

        options = " ".join(settings.data["rs_options"])
        if settings.data["rs_mode"] == "SSH":
            cmd = f'rsync -v {options} --no-perms --exclude={{"*.info","*.th.jpg"}} {media_path}/ -e ssh {settings.data["rs_user"]}@{settings.data["rs_remote_host"]}:/{settings.data["rs_direction"]}'
        else:
            cmd = f"rsync -v {options} --no-perms --exclude={{'*.info','*.th.jpg'}} {media_path}/ {settings.data['rs_user']}@{settings.data['rs_remote_host']}::{settings.data['rs_remote_module_name']}"

        if not get_pid(cmd):
            print(cmd)
            process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, text="utf-8")
            if raw := process.stderr.read():
                errorcode = re.findall("rsync error:.* \\(code ([0-9]{1,2})\\).*", raw)
                write_log(f"Rsync failed ({errorcode[0]})")
                print(raw)
                break
            if raw := process.stdout.read():
                print(raw)

        time.sleep(poll_time * 1000)
