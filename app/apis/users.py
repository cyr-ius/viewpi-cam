"""Blueprint Users API."""

from flask import current_app as ca
from flask_restx import Namespace, Resource, abort
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from ..helpers.decorator import role_required, token_required
from ..models import Users as users_db
from ..models import db
from .models import locale, message, user, users

api = Namespace(
    "users",
    description="Create, update and delete users.",
    decorators=[token_required, role_required("max")],
)
api.add_model("Error", message)
api.add_model("User", user)
api.add_model("Users", users)
api.add_model("Locale", locale)


@api.response(403, "Forbidden", message)
@api.route("/")
class Users(Resource):
    """List users."""

    @api.marshal_with(users, as_list=True)
    def get(self):
        """List users."""
        return users_db.query.all()

    @api.expect(user)
    @api.marshal_with(users)
    @api.response(422, "Error", message)
    def post(self):
        """Create user."""
        try:
            password = api.payload.pop("password")
            api.payload.pop("id", None)
            api.payload["secret"] = generate_password_hash(password)
            user = users_db(**api.payload)
            db.session.add(user)
            db.session.commit()
            return user
        except IntegrityError:
            abort(422, "User name is already exists, please change.")


@api.response(403, "Forbidden", message)
@api.route("/<int:id>")
class User(Resource):
    """User object."""

    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def get(self, id: int):
        """Get user."""
        return db.get_or_404(users_db, id)

    @api.expect(user)
    @api.marshal_with(user)
    @api.response(204, "Success")
    @api.response(404, "Not found", message)
    def put(self, id: int):
        """Set user."""
        if user := db.get_or_404(users_db, id):
            if password := api.payload.pop("password", None):
                api.payload["secret"] = generate_password_hash(password)
            user.update(**api.payload)
            db.session.commit()
            return "", 204
        abort(404, "User not found")

    @api.response(204, "Success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):
        """Delete user."""
        if id == 1:
            abort(403, "Admin account cannot be deleted")

        if user := db.get_or_404(users_db, id):
            db.session.delete(user)
            db.session.commit()
            return "", 204
        abort(404, "User not found")


@api.response(403, "Forbidden", message)
@api.route("/locales")
class Locales(Resource):
    """Language for user."""

    def get(self):
        """Get all languages."""
        return {"locales": ca.config["LOCALES"]}


@api.response(204, "Success")
@api.response(403, "Forbidden", message)
@api.route("/<int:id>/locale")
class Locale(Resource):
    """Language for user."""

    @api.expect(locale)
    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def put(self, id: int):
        """Set language."""
        if user := db.get_or_404(users_db, id):
            user.update(**api.payload)
            db.session.commit()
            return "", 204
        abort(404, "User not found")
