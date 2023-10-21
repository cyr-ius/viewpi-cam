"""Blueprint Users API."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required, token_required
from ..helpers.users import User as usr
from ..helpers.users import UserAlreadyExists, UserNotFound, UsersException
from .models import message, user, users

api = Namespace(
    "users",
    description="Create, update and delete users.",
    path="/api",
    decorators=[token_required, role_required("max")],
)
api.add_model("Error", message)
api.add_model("User", user)
api.add_model("Users", users)


@api.response(403, "Forbidden", message)
@api.route("/users")
class Users(Resource):
    """List users."""

    @api.marshal_with(users, as_list=True)
    def get(self):
        """List users."""
        return ca.settings.users

    @api.expect(user)
    @api.marshal_with(users)
    @api.response(422, "Error", message)
    def post(self):
        """Create user."""
        try:
            return usr.create(**api.payload)
        except UserAlreadyExists:
            abort(422, "User name is already exists, please change.")


@api.response(403, "Forbidden", message)
@api.route("/users/<int:id>")
class User(Resource):
    """User objet."""

    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get user."""
        try:
            return usr(id)
        except UserNotFound:
            abort(404, "User not found")

    @api.expect(user)
    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set user."""
        try:
            user = usr(id)  # pylint: disable=W0621
            return user.update(**api.payload)
        except UserNotFound:
            abort(404, "User not found")
        except UserAlreadyExists:
            abort(422, "User name is already exists, please change.")

    @api.response(204, "Actions is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete user."""
        if id == 1:
            abort(403, "Admin account cannot be deleted")
        try:
            user = usr(id)  # pylint: disable=W0621
            user.delete()
        except UsersException:
            abort(404, "User not found")
        else:
            return "", 204
