"""Blueprint Authorize API."""
from datetime import datetime as dt
from flask import make_response
from flask_restx import Namespace, Resource, abort
from sqlalchemy import func

from ..models import Users, db
from .models import login, secret

api = Namespace("idp", description="Authenticate endpoint.")
api.add_model("Login", login)
api.add_model("Secret", secret)


@api.route("/authorize")
@api.response(200, "Success")
@api.response(202, "OTP Required")
@api.response(401, "Unauthorized")
class Authorize(Resource):
    """Login class."""

    @api.expect(login)
    @api.doc(security=None)
    def post(self):
        """Check login"""
        if not (
            (
                user := db.session.scalars(
                    db.select(Users).filter_by(name=api.payload["username"])
                ).first()
            )
            and user.check_password(api.payload["password"])
        ):
            abort(401, "User or password incorrect")

        if user.otp_confirmed and api.payload.get("otp_code") is None:
            return "", 202
        elif (
            user.otp_confirmed
            and user.check_otp_secret(api.payload.get("otp_code")) is False
        ):
            abort(401, "OTP Failed")

        jwtoken, expires_in = user.generate_jwt()  # Generate JWT token
        resp = make_response(
            {"access_token": jwtoken, "token_type": "Bearer", "expires_in": int(expires_in.timestamp() - dt.now().timestamp() )},
            200,
        )
        # Add Token in secure cookie
        resp.set_cookie(
            "x-api-key",
            jwtoken,
            secure=True,
            httponly=True,
            samesite="strict",
            expires=expires_in,
        )
        return resp


@api.response(202, "Already Enrollment")
@api.response(204, "Success")
@api.route("/firstenrollment")
class FirstEnrollment(Resource):
    """First enrollment."""

    def get(self):
        users_count = db.session.execute(
            db.select(func.count("*")).select_from(Users)
        ).scalar()
        if users_count != 1:
            return "", 202
        return "", 204
