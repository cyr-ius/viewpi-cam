"""Error handler."""
from flask_restx import Model, fields

message = Model("Error", {"message": fields.String(required=True)})
forbidden = Model(
    "Forbidden", {"message": fields.String(default="The provided API key is not valid")}
)
date_time = Model("Datetime", {"datetime": fields.DateTime(dt_format="iso8601")})
