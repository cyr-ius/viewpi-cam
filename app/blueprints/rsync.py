"""Blueprint Scheduler."""

from subprocess import Popen

from flask import Blueprint
from flask.cli import with_appcontext

from ..helpers.utils import get_pid
from ..models import Settings as settings_db
from ..services.rsync import rsync

bp = Blueprint("rsync", __name__, url_prefix="/rsync", cli_group="rsync")
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
    settings = settings_db.query.first()
    if settings.data.get("rs_enabled"):
        rsync()
