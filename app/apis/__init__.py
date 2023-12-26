"""Apis viewpicam."""
from flask import Blueprint
from flask_restx import Api

from .captures import api as captures
from .logs import api as logs
from .multiview import api as multiview
from .previews import api as previews
from .schedule import api as schedule
from .settings import api as settings
from .system import api as system
from .totp import api as totp
from .users import api as users

bp = Blueprint("api", __name__)

api = Api(
    app=bp,
    title="APIS ViewPi Cam",
    version="1.0",
    description="Apis for Viewpi Cam",
    doc="/api/doc",
    authorizations={
        "apikey": {"type": "apiKey", "in": "header", "name": "Authorization"}
    },
    security="apikey",
)
api.add_namespace(captures)
api.add_namespace(logs)
api.add_namespace(multiview)
api.add_namespace(previews)
api.add_namespace(schedule)
api.add_namespace(settings)
api.add_namespace(system)
api.add_namespace(totp)
api.add_namespace(users)
