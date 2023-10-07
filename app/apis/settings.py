"""Blueprint API."""
import random

from flask import current_app as ca
from flask_restx import Namespace, Resource, abort, fields

from ..helpers.decorator import token_required
from ..helpers.utils import hash_password
from .models import message

users = Namespace("users")
users.add_model("Error", message)

buttons = Namespace("buttons")
buttons.add_model("Error", message)

settings = Namespace("settings")
settings.add_model("Error", message)

user = users.model(
    "User",
    {
        "name": fields.String(required=True, description="The user name"),
        "password": fields.String(required=False, description="The user password"),
        "rights": fields.Integer(
            required=True, description="The user rights", enum=[2, 4, 6, 8]
        ),
    },
)

listed_user = buttons.model(
    "Users",
    {
        "id": fields.Integer(required=True, description="Id"),
        **user,
    },
)


@users.response(422, "Error", message)
@users.response(403, "Forbidden", message)
@users.route("/users")
class Users(Resource):
    """List users."""

    @token_required
    @users.marshal_with(listed_user, as_list=True)
    def get(self):
        """List users."""
        return ca.settings.users

    @token_required
    @users.expect(user)
    @users.response(204, "Actions is success")
    def post(self):
        """Create user."""
        if ca.settings.has_username(users.payload["name"]):
            abort(422, "User name is already exists, please change.")
        ids = [user["id"] for user in ca.settings.users]
        uid = max(ids) + 1
        users.payload["id"] = uid
        users.payload["password"] = hash_password(users.payload["password"])
        ca.settings.users.append(users.payload)
        ca.settings.update(users=ca.settings.users)
        return users.payload


@users.response(422, "Error", message)
@users.response(403, "Forbidden", message)
@users.route("/users/<int:uid>")
class User(Resource):
    """User objet."""

    def get_byid(self, uid: int):
        """Return user."""
        for dict_user in ca.settings.users:
            if dict_user["id"] == uid:
                return dict_user

    @token_required
    @users.marshal_with(user)
    def get(self, uid: int):
        """Get user."""
        if dict_user := self.get_byid(uid):
            return dict_user
        abort(422, "User not found")

    @token_required
    @users.expect(user)
    @users.marshal_with(user)
    def put(self, uid: int):
        """Set user."""
        if ca.settings.has_username(users.payload["name"]):
            abort(422, "User name is already exists, please change.")
        if dict_user := self.get_byid(uid):
            ca.settings.users.remove(dict_user)
            users.payload["id"] = uid
            if (pwd := users.payload.get("password")) is None:
                users.payload["password"] = dict_user["password"]
            else:
                users.payload["password"] = hash_password(pwd)
            ca.settings.users.append(users.payload)
            ca.settings.update(users=ca.settings.users)
            return users.payload
        abort(422, "User not found")

    @token_required
    @users.response(204, "Actions is success")
    def delete(self, uid: int):
        """Delete user."""
        if dict_user := self.get_byid(uid):
            ca.settings.users.remove(dict_user)
            ca.settings.update(users=ca.settings.users)
            return "", 204
        abort(422, "User not found")


button = buttons.model(
    "Button",
    {
        "display": fields.Boolean(required=True, description="Display"),
        "name": fields.String(required=True, description="Button name"),
        "macros": fields.String(required=True, description="Script name"),
        "css_class": fields.String(required=False, description="Class"),
        "style": fields.String(required=False, description="Style"),
        "other": fields.String(required=False, description="Others options"),
    },
)

listed_button = buttons.model(
    "Buttons",
    {
        "id": fields.Integer(required=True, description="Id"),
        **button,
    },
)


@buttons.response(422, "Error", message)
@buttons.response(403, "Forbidden", message)
@buttons.route("/buttons")
class Buttons(Resource):
    """List buttons."""

    @buttons.marshal_with(listed_button, as_list=True)
    @token_required
    def get(self):
        """List buttons."""
        return ca.settings.get("ubuttons", [])

    @buttons.expect(button)
    @token_required
    @buttons.response(204, "Actions is success")
    def post(self):
        """Create button."""
        if ca.settings.get("ubuttons") is None:
            ca.settings.ubuttons = []
        ids = [button["id"] for button in ca.settings.ubuttons]
        uid = 1 if len(ids) == 0 else max(ids) + 1
        buttons.payload["id"] = uid
        ca.settings.ubuttons.append(buttons.payload)
        ca.settings.update(buttons=ca.settings.ubuttons)
        return buttons.payload


@buttons.response(422, "Error", message)
@buttons.response(403, "Forbidden", message)
@buttons.route("/buttons/<int:uid>")
class Button(Resource):
    """Button objet."""

    def get_byid(self, uid: int):
        """Return button."""
        for button_dict in ca.settings.get("ubuttons", []):
            if button_dict["id"] == uid:
                return button_dict

    @token_required
    @buttons.marshal_with(button)
    def get(self, uid: int):
        """Get button."""
        if button_dict := self.get_byid(uid):
            return button_dict
        abort(422, "Button not found")

    @token_required
    @buttons.expect(button)
    @buttons.marshal_with(button)
    def put(self, uid: int):
        """Set button."""
        if dict_button := self.get_byid(uid):
            ca.settings.ubuttons.remove(dict_button)
            buttons.payload["id"] = uid
            ca.settings.ubuttons.append(buttons.payload)
            ca.settings.update(ubuttons=ca.settings.ubuttons)
            return buttons.payload
        abort(422, "Button not found")

    @token_required
    @buttons.response(204, "Actions is success")
    def delete(self, uid: int):
        """Delete button."""
        if dict_button := self.get_byid(uid):
            ca.settings.ubuttons.remove(dict_button)
            ca.settings.update(ubuttons=ca.settings.ubuttons)
            return "", 204
        abort(422, "Button not found")


setting = settings.model(
    "Set",
    {
        "servo": fields.Boolean(required=False, description="Servo", default=False),
        "pipan": fields.Boolean(required=False, description="Pipan", default=False),
        "pilight": fields.Boolean(
            required=False, description="Pi Light", default=False
        ),
        "upreset": fields.String(
            default="v2",
            required=False,
            description="Class",
            enum=["v2", "N-IMX219", "P-IMX219", "N-OV5647", "P-OV5647"],
        ),
        "loglevel": fields.String(
            default="INFO",
            required=False,
            description="Log level",
            enum=["INFO", "WARNING", "ERROR", "DEBUG"],
        ),
    },
)


@settings.response(422, "Error", message)
@settings.response(403, "Forbidden", message)
@settings.route("/settings")
class Sets(Resource):
    """Settings."""

    @token_required
    @settings.marshal_with(setting)
    def get(self):
        """Get settings."""
        return ca.settings

    @token_required
    @buttons.expect(setting)
    @settings.marshal_with(setting)
    def post(self):
        """Set setttings."""
        ca.settings.update(**settings.payload)
        if loglevel := settings.payload.get("loglevel"):
            ca.logger.setLevel(loglevel)
        return "", 204


@settings.response(422, "Error", message)
@settings.response(403, "Forbidden", message)
@settings.route("/token")
class Token(Resource):
    """Token."""

    @token_required
    def get(self):
        """Get token."""
        return ca.settings.get("token")

    @token_required
    def post(self):
        """Create token."""
        token = f"B{random.getrandbits(256)}"
        ca.settings.update(token=token)
        return {"token": token}

    @token_required
    @buttons.response(204, "Actions is success")
    def delete(self):
        """Delete token."""
        del ca.settings.token
        ca.settings.update(token=None)
        return "", 204


macros = settings.model(
    "Macro",
    {
        "name": fields.String(required=True, description="Macro name"),
        "command": fields.String(required=True, description="Script execute"),
        "state": fields.Boolean(required=True, description="Enable", default=False),
    },
)


@settings.response(422, "Error", message)
@settings.response(403, "Forbidden", message)
@settings.route("/macros")
class Macros(Resource):
    """Macros."""

    @staticmethod
    def get_config():
        """Return config."""
        return {item: getattr(ca.raspiconfig, item) for item in ca.config["MACROS"]}

    @token_required
    @settings.marshal_with(macros, as_list=True)
    def get(self):
        """Get macros."""
        list_macros = []
        for key, value in Macros().get_config().items():
            state = True
            if value[:1] == "-":
                value = value[1:]
                state = False
            list_macros.append({"name": key, "command": value, "state": state})

        return list_macros

    @token_required
    @buttons.expect(macros)
    @settings.marshal_with(macros)
    def post(self):
        """Set macro."""
        if settings.payload:
            name = settings.payload["name"]
            command = settings.payload["command"]
            if not settings.payload["state"]:
                command = f"-{command}"
            ca.raspiconfig.set_config({name: command})
        return "", 204
