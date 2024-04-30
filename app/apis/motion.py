"""Blueprint Motion Settings API."""

import requests
from flask import abort
from flask_login import login_required
from flask_restx import Namespace, Resource

from ..helpers.decorator import role_required
from ..helpers.motion import (
    get_motion,
    parse_ini,
    restart_motion,
    set_motion,
    write_motion,
)
from .models import message

api = Namespace(
    "motion",
    description="Motion settings",
    decorators=[role_required("max"), login_required],
)


@api.response(401, "Unauthorized", message)
@api.response(422, "Error", message)
@api.route("/")
class Settings(Resource):
    """Settings."""

    def get(self):
        """Get settings."""
        try:
            return get_motion()
        except (ValueError, requests.RequestException) as error:
            abort(422, str(error))

    @api.response(204, "Success")
    def put(self):
        """Set settings."""
        try:
            is_changed = False

            for key, value in api.payload.items():
                set_motion(key, value)
                is_changed = True

            if is_changed:
                write_motion()
                rsp = restart_motion()
                return parse_ini(rsp.text())
        except (ValueError, requests.RequestException) as error:
            abort(422, str(error))

        return "", 204
