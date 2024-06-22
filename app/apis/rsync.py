"""Api scheduler."""

from subprocess import PIPE, Popen

from flask import current_app as ca
from flask import request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..helpers.exceptions import ViewPiCamException
from ..helpers.utils import execute_cmd, get_pid
from ..models import Settings as settting_db
from ..models import db
from .models import message, rsync

api = Namespace(
    "rsync",
    description="Rsync management",
    decorators=[role_required("max"), login_required],
)
api.add_model("Rsync", rsync)


@api.response(401, "Unauthorized", message)
@api.route("/")
class Rsync(Resource):
    """Rsync settings."""

    @api.marshal_with(rsync)
    def get(self):
        """Get settings."""
        settings = settting_db.query.first()
        return settings.data

    @api.expect(rsync)
    @api.marshal_with(rsync)
    @api.response(204, "Success")
    def post(self):
        """Set settings."""
        settings = settting_db.query.first()
        settings.data.update(**api.payload)
        db.session.commit()
        if loglevel := api.payload.get("loglevel"):
            ca.logger.setLevel(loglevel)
        return "", 204

    @api.expect(rsync)
    @api.response(204, "Success")
    def delete(self):
        """Delete settings."""
        settings = settting_db.query.first()
        params = settings.data.copy()
        for param in api.payload:
            params.pop(param, None)
        settings.data.update(**params)
        return "", 204


@api.route("/stop", endpoint="rsync_stop")
@api.route("/start", endpoint="rsync_start")
@api.response(204, "Success")
@api.response(404, "Not found", message)
@api.response(401, "Unauthorized", message)
class Actions(Resource):
    """Actions."""

    @api.marshal_with(message)
    def post(self):
        """Post action."""
        match request.endpoint:
            case "api.rsync_start":
                if not get_pid(["*/flask", "rsync"]):
                    Popen(["flask", "rsync", "start"], stdout=PIPE)
                return "", 204
            case "api.rsync_stop":
                pid = get_pid(["*/flask", "rsync"])
                try:
                    if pid:
                        execute_cmd(f"kill {pid}")
                except ViewPiCamException as error:
                    return abort(422, error)
                return "", 204
        abort(404, "Action not found")
