"""Blueprint Scheduler."""

import os
import time
from subprocess import Popen

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
bp.cli.short_help = "Stop/Start scheduler"


@bp.cli.command("stop", short_help="Stop rsync task")
@with_appcontext
def stop_scheduler() -> None:
    """Stop rsync."""
    pid = get_pid("rsync")
    Popen(f"kill {pid}", shell=True)


@bp.cli.command("start", short_help="Start rsync task")
@with_appcontext
def start_scheduler() -> None:
    """Start rsync."""
    rsync()


def rsync() -> None:
    """Rsync daemon."""

    write_log("Rsync support started")
    settings = settings_db.query.first()
    os.environ["RSYNC_PASSWORD"] = settings.data["rs_pwd"]
    poll_time = settings.data["cmd_poll"]
    media_path = ca.raspiconfig.media_path

    while settings.data["rs_enabled"]:
        options = " ".join(settings.data["rs_options"])
        if settings.data["rs_mode"] == "SSH":
            cmd = f'rsync {options} --exclude={{"*.info","*.th.jpg"}} {media_path} -e ssh {settings.data["rs_user"]}@{settings.data["rs_remote_host"]}:/{settings.data["rs_direction"]}'
        else:
            cmd = f"rsync {options} --exclude={{'*.info','*.th.jpg'}} {media_path} {settings.data['rs_user']}@{settings.data['rs_remote_host']}::{settings.data['rs_remote_module_name']}"

        write_log(cmd)
        if not get_pid(cmd):
            Popen(cmd, shell=True)

        time.sleep(poll_time * 1000)
