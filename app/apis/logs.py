"""Api logs."""
import os

from flask import current_app as ca
from flask import request
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import token_required
from ..helpers.utils import delete_log
from .models import error_m


api = Namespace("logs")
api.add_model("Error", error_m)


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/logs")
class Content(Resource):
    """Get log."""

    @api.param("reverse", description="Ordering display (True|False)", _in="query")
    @token_required
    def get(self):
        """List log."""
        reverse = request.args.get("reverse", True) is True
        log_file = ca.raspiconfig.log_file
        logs = []
        if os.path.isfile(log_file):
            with open(log_file, mode="r", encoding="utf-8") as file:
                lines = file.readlines()
                lines.sort(reverse=reverse)
                for line in lines:
                    logs.append(line.replace("\n", ""))
        return logs

    @token_required
    def delete(self):
        """Delete log."""
        try:
            delete_log(1)
        except Exception as error:  # pylint: disable=W0718
            abort(422, error)
