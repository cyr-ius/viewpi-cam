"""Apis viewpicam."""

from flask import Blueprint
from flask_restx import Api

bp = Blueprint("api", __name__)

api = Api(
    app=bp,
    title="APIS ViewPi Cam",
    version="1.0",
    description="Apis for Viewpi Cam",
    doc="/doc",
    authorizations={
        "api_token": {"type": "apiKey", "in": "header", "name": "X-API-KEY"}
    },
    security="api_token",
)
