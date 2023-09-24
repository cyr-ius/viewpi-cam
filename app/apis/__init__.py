"""Apis viewpicam."""
from flask import Blueprint
from flask_restx import Api

from .users import api as ns1
from .logs import api as ns2
from .captures import api as ns3
from .previews import api as ns4

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
api.add_namespace(ns1, path="/api")
api.add_namespace(ns2, path="/api")
api.add_namespace(ns3, path="/api")
api.add_namespace(ns4, path="/api")
