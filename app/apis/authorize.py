"""Blueprint Authorize API."""

from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from ..models import Users as users_db
from ..models import db
from .models import login, secret

api = Namespace("idp", description="Authenticate endpoint.")
api.add_model("Login", login)
api.add_model("Secret", secret)


@api.route("/authorize")
@api.response(401, "Unauthorized")
@api.response(412, "OTP Required")
class Authorize(Resource):
    """Login class."""

    @api.expect(login, code=201)
    @api.doc(security=None)
    def post(self):
        """Check login"""
        if not (
            (
                user := db.session.scalars(
                    db.select(users_db).filter_by(name=api.payload["username"])
                ).first()
            )
            and user.check_password(api.payload["password"])
        ):
            abort(401, "User or password incorrect")

        if user.otp_confirmed and api.payload.get("otp_code") is None:
            abort(412, "OTP Required")
        elif (
            user.otp_confirmed
            and user.check_otp_secret(api.payload.get("otp_code")) is False
        ):
            abort(401, "OTP Failed")

        return {
            "access_token": user.generate_jwt(),
            "token_type": "Bearer",
            "expires_in": int(ca.config["PERMANENT_SESSION_LIFETIME"].total_seconds()),
        }
