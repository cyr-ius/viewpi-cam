"""Blueprint Users API."""

from flask import url_for
from flask_login import login_required
from flask_restx import Namespace, Resource, abort, fields
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from ..config import LOCALES
from ..helpers.decorator import role_required
from ..models import Users as users_db
from ..models import db
from .models import api_token, cam_token, login, message, user

api = Namespace(
    "users",
    description="Create, update and delete users.",
    decorators=[role_required("max"), login_required],
)
api.add_model("User", user)
api.add_model("CamToken", cam_token)
api.add_model("APIToken", api_token)
api.add_model("Login", login)


@api.response(401, "Unauthorized")
@api.route("/")
class Users(Resource):
    """List users."""

    @api.marshal_with(user, as_list=True)
    def get(self):
        """List users."""
        return db.session.scalars(db.select(users_db).filter(users_db.id > 0)).all()

    @api.expect(user.copy().pop("id"))
    @api.response(204, "Success")
    def post(self):
        """Create user."""
        try:
            password = api.payload.pop("password")
            api.payload.pop("id", None)
            api.payload["secret"] = generate_password_hash(password)
            user = users_db(**api.payload)
            user.create_user()
            return (
                "",
                204,
                {"Location": url_for("api.users_user", id=user.id)},
            )
        except IntegrityError:
            abort(422, "User name is already exists, please change.")


@api.response(401, "Unauthorized")
@api.route("/<int:id>")
class User(Resource):
    """User object."""

    @api.marshal_with(user)
    @api.response(403, "Forbidden", message)
    @api.response(404, "Not found", message)
    def get(self, id: int):
        """Get user."""
        if id == 0:
            abort(403, "System account cannot be read")
        return db.get_or_404(users_db, id, description="User not found")

    @api.expect(user)
    @api.response(204, "Success")
    @api.response(403, "Forbidden", message)
    @api.response(404, "Not found", message)
    def put(self, id: int):
        """Set user."""
        if id == 0:
            abort(403, "System account cannot be modified")
        if password := api.payload.pop("password", None):
            api.payload["secret"] = generate_password_hash(password)
        db.session.execute(update(users_db), [api.payload])
        db.session.commit()
        return "", 204

    @api.response(204, "Success")
    @api.response(403, "Forbidden", message)
    @api.response(404, "Not found", message)
    def delete(self, id: int):
        """Delete user."""
        if id in [0, 1]:
            abort(403, "Admin account cannot be deleted")

        user = db.get_or_404(users_db, id, description="User not found")
        db.session.delete(user)
        db.session.commit()
        return "", 204


@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(403, "Forbidden", message)
@api.response(404, "Not found", message)
@api.route("/<int:id>/locale")
class Locale(Resource):
    """Language for user."""

    @api.expect(api.model("Resource", {"locale": fields.String(enum=LOCALES)}))
    def put(self, id: int):
        """Set language."""
        if id == 0:
            abort(403, "System account cannot be modified")

        user = db.get_or_404(users_db, id, description="User not found")
        user.locale = api.payload.get("locale")
        db.session.commit()
        return "", 204


@api.response(401, "Unauthorized")
@api.route("/ctoken")
class Token(Resource):
    """Camera Token."""

    @api.marshal_with(cam_token)
    def get(self):
        """Get camera token."""
        user = db.get_or_404(users_db, 0, description="User not found")
        return {"cam_token": user.cam_token}

    @api.marshal_with(cam_token, code=201)
    def post(self):
        """Create camera token."""
        user = db.get_or_404(users_db, 0, description="User not found")
        user.set_camera_token()
        return "", 204

    @api.response(204, "Success")
    def delete(self):
        """Delete camera token."""
        user = db.get_or_404(users_db, 0, description="User not found")
        user.delete_camera_token()
        return "", 204


@api.response(401, "Unauthorized")
@api.route("/token")
class APIToken(Resource):
    """Token."""

    @api.marshal_with(api_token)
    def get(self):
        """Get token."""
        user = db.get_or_404(users_db, 0, description="User not found")
        api_token = user.set_api_token()
        return {"api_token": api_token}

    @api.marshal_with(api_token, code=201)
    def post(self):
        """Create token."""
        user = db.get_or_404(users_db, 0, description="User not found")
        user.set_api_token()
        return "", 204

    @api.response(204, "Success")
    def delete(self):
        """Delete token."""
        user = db.get_or_404(users_db, 0, description="User not found")
        user.delete_api_token()
        return "", 204
