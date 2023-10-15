"""Blueprint Users API."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort
from werkzeug.security import generate_password_hash

from ..helpers.decorator import token_required
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
    @api.marshal_with(user)
    @api.response(422, "Error", message)
    def post(self):
        """Create user."""
        name = api.payload["name"]
        if ca.settings.has_object(attr="users", id=name, key="name"):
            abort(422, "User name is already exists, please change.")
        ids = [user["id"] for user in ca.settings.users]
        api.payload["id"] = 1 if len(ids) == 0 else max(ids) + 1
        api.payload["password"] = generate_password_hash(api.payload["password"])
        ca.settings.users.append(api.payload)
        if len(ca.settings.users) > 0:
            ca.settings.update(users=ca.settings.users)
        return api.payload


@api.response(403, "Forbidden", message)
@api.route("/users/<int:id>")
class User(Resource):
    """User objet."""

    @token_required
    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get user."""
        if dict_user := ca.settings.get_object("users", id):
            return dict_user
        abort(404, "User not found")

    @token_required
    @api.expect(user)
    @api.marshal_with(user)
    @api.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set user."""
        name = api.payload["name"]
        if dict_user := ca.settings.get_object("users", id):
            if dict_user["name"] != name and ca.settings.has_object(
                attr="users", id=name, key="name"
            ):
                abort(422, "User name is already exists, please change.")
            api.payload["id"] = id
            if (pwd := api.payload.get("password")) is None:
                api.payload["password"] = dict_user["password"]
            else:
                api.payload["password"] = generate_password_hash(pwd)
            ca.settings.users.remove(dict_user)
            ca.settings.users.append(api.payload)
            if len(ca.settings.users) > 0:
                ca.settings.update(users=ca.settings.users)
            return api.payload
        abort(404, "User not found")

    @token_required
    @api.response(204, "Actions is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete user."""
        if id == 1:
            abort(403, "Admin account cannot be deleted")
        if dict_user := ca.settings.get_object("users", id):
            ca.settings.users.remove(dict_user)
            ca.settings.update(users=ca.settings.users)
            return "", 204
        abort(404, "User not found")
