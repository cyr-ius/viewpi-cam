"""Api logs."""

import os
from json.decoder import JSONDecodeError

from flask import current_app as ca
from flask import json, request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.utils import delete_log
from .models import message

api = Namespace("logs", description="Log management", decorators=[login_required])


@api.response(401, "Unauthorized", message)
@api.route("/")
class Content(Resource):
    """Get log."""

    @api.param("reverse", description="Ordering display (True|False)", _in="query")
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


def get_logs(reverse: bool) -> list[str]:
    """Get log."""
    log_file = ca.raspiconfig.log_file
    logs = []
    if os.path.isfile(log_file):
        with open(log_file, encoding="utf-8") as file:
            lines = file.readlines()
            lines.sort(reverse=reverse)
            for line in lines:
                line = line.replace("\n", "")
                try:
                    line = json.loads(line)
                except JSONDecodeError:
                    pass
                logs.append(line)
    return logs
