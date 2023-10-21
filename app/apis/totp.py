"""Blueprint API."""
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required, token_required
from ..helpers.users import User, UserNotFound
from .models import message, otp

api = Namespace(
    "otps",
    description="Manage TOTP token.",
    path="/api",
    decorators=[token_required, role_required("max")],
)
api.add_model("Error", message)
api.add_model("TOTP", otp)


@api.response(403, "Forbidden", message)
@api.route("/totp", doc=False, endpoint="users_totp")
@api.route("/totp/<int:id>")
class Totp(Resource):
    """TOTP."""

    @api.marshal_with(otp)
    @api.response(204, "OTP already enabled")
    @api.response(422, "Error", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get OTP for a user."""
        try:
            user = User(id)
            user.set_secret()
            return user
        except UserNotFound:
            abort(404, "User not found")

    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    def post(self, id: int):  # pylint: disable=W0622
        """Check OTP code."""
        try:
            user = User(id)
            if user.totp is True:
                if user.check_totp(api.payload["secret"]):
                    return "", 204
                abort(422, "OTP incorrect")
            abort(422, "OTP not enable")
        except UserNotFound:
            abort(404, "User not found")

    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    @api.response(422, "Error", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Check and create OTP Code for a user."""
        try:
            user = User(id)
            if user.validate_secret(api.payload["secret"]):
                return "", 204
            abort(422, "OTP incorrect")
        except UserNotFound:
            abort(404, "User not found")

    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete OTP infos for a user."""
        try:
            user = User(id)
            user.delete_secret()
            return "", 204
        except UserNotFound:
            abort(404, "User not found")
