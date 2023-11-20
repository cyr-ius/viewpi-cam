"""Api logs."""
import os

from flask import current_app as ca
from flask import request
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import token_required
from ..helpers.utils import delete_log
from .models import forbidden, message

api = Namespace(
    "logs", path="/api", description="Log management", decorators=[token_required]
)
api.add_model("Error", message)
api.add_model("Forbidden", forbidden)


@api.response(403, "Forbidden", forbidden)
@api.route("/logs")
class Content(Resource):
    """Get log."""

    @api.param("reverse", description="Ordering display (True|False)", _in="query")
    def get(self):
        """List log."""
        reverse = request.args.get("reverse", True) is True
        return get_logs(reverse)

    @api.response(204, "Action is success")
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
        with open(log_file, mode="r", encoding="utf-8") as file:
            lines = file.readlines()
            lines.sort(reverse=reverse)
            for line in lines:
                logs.append(line.replace("\n", ""))
    return logs
