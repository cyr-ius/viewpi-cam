"""Apis viewpicam."""
from flask import Blueprint
from flask_restx import Api

from .captures import api as ns3
from .logs import api as ns2
from .multiview import api as ns7
from .previews import api as ns4
from .schedule import api as ns5
from .settings import api as ns1
from .system import api as ns6
from .totp import api as ns8
from .users import api as ns9

bp = Blueprint("api", __name__)

api = Api(
    app=bp,
    title="APIS ViewPi Cam",
    version="1.0",
    description="Apis for Viewpi Cam",
    doc="/swagger",
    authorizations={
        "apikey": {"type": "apiKey", "in": "header", "name": "Authorization"}
    },
    security="apikey",
)
api.add_namespace(ns1)
api.add_namespace(ns2)
api.add_namespace(ns3)
api.add_namespace(ns4)
api.add_namespace(ns5)
api.add_namespace(ns6)
api.add_namespace(ns7)
api.add_namespace(ns8)
api.add_namespace(ns9)
