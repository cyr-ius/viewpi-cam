"""Apis viewpicam."""

from flask import Blueprint
from flask_restx import Api

bp = Blueprint("api", __name__)

api = Api(
    app=bp,
    title="Viewpi-Cam API",
    version="1.0",
    description="Apis for Viewpi-Cam",
    doc="/doc",
    authorizations={
        "apikey": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token",
        }
    },
    security="apikey",
)
