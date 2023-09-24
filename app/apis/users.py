"""Blueprint API."""
from hashlib import pbkdf2_hmac

from flask import current_app as cp
from flask_restx import Namespace, Resource, fields

from ..helpers.decorator import token_required

api = Namespace("Users")

user_m = api.model(
    "User",
    {
        "password": fields.String(required=False, description="The user password"),
        "rights": fields.Integer(
            required=True, description="The user rights", enum=[2, 4, 6, 8]
        ),
    },
)

users_m = api.model(
    "Users",
    {
        "uid": fields.String(required=True, description="The user name"),
        "password": fields.String(required=True, description="The user password"),
        "rights": fields.Integer(required=True, description="The user rights"),
    },
)

error_m = api.model("Error", {"message": fields.String(required=True)})


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/users")
class Users(Resource):
    """List users."""

    @api.doc("list_users")
    @api.marshal_with(users_m, as_list=True)
    @token_required
    def get(self):
        """List users."""
        return [{"uid": uid, **content} for uid, content in cp.settings.users.items()]

    @api.expect(users_m)
    @token_required
    @api.response(204, "User created")
    def post(self):
        """Create user."""
        uid = api.payload.pop("uid")
        if cp.settings.users.get(uid):
            api.abort(422, "User already exsists")

        api.payload["password"] = _hash_password(api.payload["password"])

        cp.settings.users.update({uid: api.payload})
        cp.settings.update(users=cp.settings.users)

        return "", 204


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/users/<string:uid>")
@api.param("uid", "Username")
class User(Resource):
    """User objet.

    :raises FakeException: In case exception
    """

    @api.marshal_with(user_m)
    def get(self, uid: str = None):
        """Return user."""
        return cp.settings.users.get(uid)

    @api.expect(user_m)
    @api.marshal_with(user_m)
    def put(self, uid: str):
        """Set user."""
        try:
            user = cp.settings.users.pop(uid)
        except Exception as error:  # pylint: disable=W0718
            api.abort(422, f"User not found ({error})")
        else:
            if (pwd := api.payload.get("password")) is None:
                api.payload["password"] = user["password"]
            else:
                api.payload["password"] = _hash_password(pwd)

            cp.settings.users.update({uid: api.payload})
            cp.settings.update(users=cp.settings.users)
        return cp.settings.users.get(uid)

    @api.response(204, "User deleted")
    def delete(self, uid: str):
        """Delete user."""
        try:
            cp.settings.users.pop(uid)
        except Exception as error:  # pylint: disable=W0718
            api.abort(422, f"User not found ({error})")
        else:
            cp.settings.update(users=cp.settings.users)
        return "", 204


def _hash_password(password: str) -> bool:
    salt = cp.config["SECRET_KEY"]
    hashed = pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return hashed.hex()
