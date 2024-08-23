"""Blueprint Authorize API."""

from datetime import datetime as dt

import jwt
from flask import current_app as ca
from flask import make_response, request, url_for
from flask_restx import Namespace, Resource, abort
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from ..models import Users, db
from .models import login, secret, user

api = Namespace("idp", description="Authenticate endpoint.")
api.add_model("Login", login)
api.add_model("Secret", secret)
api.add_model("User", user)


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
            {
                "access_token": jwtoken,
                "token_type": "Bearer",
                "expires_in": int(expires_in.timestamp() - dt.now().timestamp()),
            },
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

    @api.doc(security=None)
    def get(self):
        users_count = db.session.execute(
            db.select(func.count("*")).select_from(Users)
        ).scalar()
        if users_count != 1:
            return "", 202
        return "", 204


@api.response(202, "Already Enrollment")
@api.response(204, "Success")
@api.response(422, "Error")
@api.route("/register")
class Register(Resource):
    """Register first account."""

    @api.expect(user.copy().pop("id"))
    @api.doc(security=None)
    @api.response(204, "Success")
    def post(self):
        """Create Admin account."""

        users_count = db.session.execute(
            db.select(func.count("*")).select_from(Users)
        ).scalar()

        if users_count != 1:
            abort(422, "Registration already done !")

        if (password := api.payload.get("password")) != api.payload.get("password_2"):
            abort(422, "Password mismatch.")

        try:
            password = api.payload.pop("password")
            user = Users(
                name=api.payload.pop("username"),
                secret=generate_password_hash(password),
                right=ca.config["USERLEVEL"]["max"],
            )
            user.create_user()
            return (
                "",
                204,
                {"Location": url_for("api.users_user", id=user.id)},
            )
        except IntegrityError:
            abort(422, "User name is already exists, please change.")


@api.response(200, "Success")
@api.response(422, "Error")
@api.route("/userinfo")
class UserInfo(Resource):
    """First enrollment."""

    @login_required
    @api.marshal_with(user)
    def get(self):
        jwtoken = request.cookies.get("x-api-key")
        toks = request.headers.get("Authorization", "").split("Bearer ")
        if toks.count == 2:
            jwtoken = toks[1]

        try:
            jwt_content = jwt.decode(
                jwtoken, ca.config["SECRET_KEY"], algorithms=["HS256"]
            )
        except jwt.PyJWTError:
            abort(422, "Error to decode JWToken")

        if user := db.session.get(Users, jwt_content.get("id")):
            return user

        return "", 204


@api.response(200, "Success")
@api.response(422, "Error")
@api.route("/logout")
class Logout(Resource):
    """First enrollment."""

    @login_required
    def get(self):
        resp = make_response("", 200)
        resp.set_cookie("x-api-key", "", expires=0)
        return resp

    @login_required
    def post(self):
        resp = make_response("", 200)
        resp.set_cookie("x-api-key", "", expires=0)
        return resp
