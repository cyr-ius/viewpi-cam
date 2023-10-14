"""Apis viewpicam."""
from flask import Blueprint
from flask_restx import Api

from .captures import api as ns3
from .logs import api as ns2
from .previews import api as ns4
from .schedule import api as ns5
from .settings import buttons, otps, settings, users
from .system import api as ns6

bp = Blueprint("api", __name__)

api = Api(
    app=bp,
    title="APIS ViewPi Cam",
    version="1.0",
    description="Apis for Viewpi Cam",
    doc="/swagger",
    authorizations={"apikey": {"type": "apiKey", "in": "header", "name": "X-API-KEY"}},
    security="apikey",
)
api.add_namespace(users, path="/api")
api.add_namespace(buttons, path="/api")
api.add_namespace(settings, path="/api")
api.add_namespace(otps, path="/api")
api.add_namespace(ns2, path="/api")
api.add_namespace(ns3, path="/api")
api.add_namespace(ns4, path="/api")
api.add_namespace(ns5, path="/api")
api.add_namespace(ns6, path="/api")
