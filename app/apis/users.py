"""Blueprint Users API."""

from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required, token_required
from ..helpers.usrmgmt import UserNameExists
from .models import locale, message, user, users

api = Namespace(
    "users",
    description="Create, update and delete users.",
    path="/api",
    decorators=[token_required, role_required("max")],
)
api.add_model("Error", message)
api.add_model("User", user)
api.add_model("Users", users)
api.add_model("Locale", locale)


@api.response(403, "Forbidden", message)
@api.route("/users")
class Users(Resource):
    """List users."""

    @api.marshal_with(users, as_list=True)
    def get(self):
        """List users."""
        return ca.usrmgmt.get_users()

    @api.expect(user)
    @api.marshal_with(users)
    @api.response(422, "Error", message)
    def post(self):
        """Create user."""
        try:
            return ca.usrmgmt.create(**api.payload)
        except UserNameExists:
            abort(422, "User name is already exists, please change.")


@api.response(403, "Forbidden", message)
@api.route("/users/<int:id>")
class User(Resource):
    """User object."""

    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get user."""
        return ca.usrmgmt.get_user(id)

    @api.expect(user)
    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set user."""
        try:
            if user := ca.usrmgmt.get(id):  # pylint: disable=W0621
                return user.update(**api.payload)
            abort(404, "User not found")
        except UserNameExists:
            abort(422, "User name is already exists, please change.")

    @api.response(204, "Actions is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete user."""
        if id == 1:
            abort(403, "Admin account cannot be deleted")

        ca.usrmgmt.delete(id)  # pylint: disable=W0621
        return "", 204


@api.response(403, "Forbidden", message)
@api.route("/locales")
class Locales(Resource):
    """Language for user."""

    def get(self):  # pylint: disable=W0622
        """Get all languages."""
        return {"locales": ca.config["LOCALES"]}


@api.response(403, "Forbidden", message)
@api.route("/users/<int:id>/locale")
class Locale(Resource):
    """Language for user."""

    @api.expect(locale)
    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set language."""
        try:
            if user := ca.usrmgmt.get(id):  # pylint: disable=W0621
                return user.update(**api.payload)
            abort(404, "User not found")
        except UserNameExists:
            abort(422, "User name is already exists, please change.")
