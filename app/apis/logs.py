"""Api logs."""

import os
from datetime import datetime as dt
from json.decoder import JSONDecodeError

from flask import current_app as ca
from flask import json, request, send_file
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..helpers.utils import delete_log
from .models import log, message

api = Namespace(
    "logs",
    description="Log management",
    decorators=[role_required("max"), login_required],
)  # noqa: F821
api.add_model("Log", log)


@api.response(401, "Unauthorized")
@api.route("/")
class Content(Resource):
    """Get log."""

    @api.param("reverse", description="Ordering display (True|False)", _in="query")
    @api.marshal_with(log, as_list=True)
    def get(self):
        """List log."""
        reverse = request.args.get("reverse", True) is True
        return get_logs(reverse)

    @api.response(204, "Success")
    @api.response(422, "Error", message)
    def delete(self):
        """Delete log."""
        try:
            delete_log(1)
            return "", 204
        except Exception as error:  # pylint: disable=W0718
            abort(422, error)


@api.response(200, "Success")
@api.response(401, "Unauthorized")
@api.route("/download")
class Download(Resource):
    """Download log."""

    def get(self):
        """Log."""
        date_str = dt.now().strftime("%Y%m%d_%H%M%S")
        logname = f"viewpicam_{date_str}.log"

        response = send_file(
            path_or_file=ca.raspiconfig.log_file,
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=logname,
        )
        return response


def get_logs(reverse: bool) -> list[str]:
    """Get log."""
    log_file = ca.raspiconfig.log_file
    logs = []
    if os.path.isfile(log_file):
        with open(log_file, encoding="utf-8") as file:
            lines = file.readlines()
            file.close()

        for line in lines:
            line = line.replace("\n", "")
            try:
                line = json.loads(line)
            except JSONDecodeError:
                pass
            logs.append(line)

        logs.reverse()
    return logs
