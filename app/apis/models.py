"""Error handler."""
from flask_restx import Model, fields

message = Model("Error", {"message": fields.String(required=True)})
