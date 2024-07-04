"""Api scheduler."""

from subprocess import PIPE, Popen

from flask import request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort
from sqlalchemy import update

from ..helpers.decorator import role_required
from ..helpers.exceptions import ViewPiCamException
from ..helpers.utils import execute_cmd, get_pid
from ..models import Settings, db
from .models import message, rsync

api = Namespace(
    "rsync",
    description="Rsync management",
    decorators=[role_required("max"), login_required],
)
api.add_model("Rsync", rsync)


@api.response(401, "Unauthorized")
@api.route("/")
class Rsync(Resource):
    """Rsync settings."""

    @api.marshal_with(rsync)
    def get(self):
        """Get settings."""
        settings = db.first_or_404(db.select(Settings))
        return settings.data

    @api.expect(rsync)
    @api.response(204, "Success")
    def post(self):
        """Set settings."""
        settings = db.first_or_404(db.select(Settings))
        settings.data.update(api.payload)
        db.session.execute(update(Settings), settings.__dict__)
        db.session.commit()
        return "", 204

    @api.expect(rsync)
    @api.response(204, "Success")
    def delete(self):
        """Delete settings."""
        settings = db.first_or_404(db.select(Settings))
        settings.delete(**api.payload)
        return "", 204


@api.route("/stop", endpoint="rsync_stop", doc={"description": "Stop rsync"})
@api.route("/start", endpoint="rsync_start", doc={"description": "Start rsync"})
@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(422, "Error", message)
class Actions(Resource):
    """Actions."""

    def post(self):
        """Post action."""
        match request.endpoint:
            case "api.rsync_start":
                if not get_pid(["*/flask", "rsync"]):
                    process = Popen(
                        ["flask", "rsync", "start"], stderr=PIPE, text="utf-8"
                    )
                    if (errors := process.stderr.readlines()) and len(errors) > 0:
                        abort(422, errors[-1])
                return "", 204
            case "api.rsync_stop":
                pid = get_pid(["*/flask", "rsync"])
                try:
                    if pid:
                        execute_cmd(f"kill {pid}")
                except ViewPiCamException as error:
                    return abort(422, error)
                return "", 204
