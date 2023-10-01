"""Error handler."""
from flask_restx import Model, fields

error_m = Model("Error", {"message": fields.String(required=True)})
