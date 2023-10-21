"""Blueprint Users API."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import token_required
from ..helpers.users import User as usr
from ..helpers.users import UserAlreadyExists, UserNotFound
from ..helpers.users import Users as usrs
from ..helpers.users import UsersException
from .models import message, user, users

api = Namespace("users", description="Create, update and delete users.", path="/api")
api.add_model("Error", message)
api.add_model("User", user)
api.add_model("Users", users)


@api.response(403, "Forbidden", message)
@api.route("/users")
class Users(Resource):
    """List users."""

    @token_required
    @api.marshal_with(users, as_list=True)
    def get(self):
        """List users."""
        return ca.settings.users

    @token_required
    @api.expect(user)
    @api.marshal_with(users)
    @api.response(422, "Error", message)
    def post(self):
        """Create user."""
        try:
            obj_user = usrs()
            return obj_user.set(**api.payload)
        except UserAlreadyExists:
            abort(422, "User name is already exists, please change.")


@api.response(403, "Forbidden", message)
@api.route("/users/<int:id>")
class User(Resource):
    """User objet."""

    @token_required
    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get user."""
        try:
            return usr(id)
        except UserNotFound:
            abort(404, "User not found")

    @token_required
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

    @token_required
    @api.response(204, "Actions is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete user."""
        if id == 1:
            abort(403, "Admin account cannot be deleted")
        try:
            usrmgmt = usrs()
            usrmgmt.delete(id)
        except UsersException:
            abort(404, "User not found")
        else:
            return "", 204
