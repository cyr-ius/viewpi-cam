"""Blueprint API."""

from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..models import Users, db
from .models import message, otp, secret

api = Namespace(
    "otps",
    description="Manage TOTP token.",
    decorators=[role_required("max"), login_required],
)
api.add_model("Otp", otp)
api.add_model("Secret", secret)


@api.response(401, "Unauthorized")
@api.response(403, "Forbidden", message)
@api.response(404, "Not found", message)
@api.route("/<int:id>")
class Totp(Resource):
    """One Time Password."""

    @api.marshal_with(otp)
    @api.response(200, "Success")
    def get(self, id: int):
        """Get OTP for a user."""
        if id == 0:
            abort(403, "System account cannot be modified")
        user = db.get_or_404(Users, id, description="User not found")
        if not user.otp_confirmed:
            user.set_otp_secret()
        return user

    @api.response(204, "Success")
    @api.response(422, "Error", message)
    @api.expect(secret)
    def post(self, id: int):
        """Confirmed OTP code."""
        if id == 0:
            abort(403, "System account cannot be modified")
        user = db.get_or_404(Users, id, description="User not found")
        if user.confirmed_otp_secret(api.payload["secret"]):
            return "", 204
        abort(422, "OTP incorrect")

    @api.response(204, "Success")
    def delete(self, id: int):
        """Delete OTP infos for a user."""
        if id == 0:
            abort(403, "System account cannot be modified")
        user = db.get_or_404(Users, id, description="User not found")
        user.delete_otp_secret()
        return "", 204
