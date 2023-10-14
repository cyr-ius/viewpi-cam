"""Blueprint API."""
import random

import pyotp
import qrcode
import qrcode.image.svg
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort, fields
from werkzeug.security import generate_password_hash

from ..helpers.decorator import token_required
from .models import message

users = Namespace("users")
users.add_model("Error", message)

buttons = Namespace("buttons")
buttons.add_model("Error", message)

settings = Namespace("settings")
settings.add_model("Error", message)

otps = Namespace("otps")
otps.add_model("Error", message)


user = users.model(
    "User",
    {
        "name": fields.String(required=True, description="The user name"),
        "password": fields.String(required=False, description="The user password"),
        "rights": fields.Integer(
            required=True, description="The user rights", enum=[2, 4, 6, 8]
        ),
        "totp": fields.Boolean(required=False, description="otp status"),
    },
)

listed_user = buttons.model(
    "Users",
    {
        "id": fields.Integer(required=True, description="Id"),
        **user,
    },
)


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
    def post(self):
        """Create user."""
        if ca.settings.has_username(users.payload["name"]):
            abort(422, "User name is already exists, please change.")
        ids = [user["id"] for user in ca.settings.users]
        users.payload["id"] = 1 if len(ids) == 0 else max(ids) + 1
        users.payload["password"] = generate_password_hash(users.payload["password"])
        ca.settings.users.append(users.payload)
        ca.settings.update(users=ca.settings.users)
        return users.payload


@users.response(403, "Forbidden", message)
@users.route("/users/<int:id>")
class User(Resource):
    """User objet."""

    @token_required
    @users.marshal_with(user)
    @users.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get user."""
        if dict_user := ca.settings.get_user_byid(id):
            return dict_user
        abort(404, "User not found")

    @token_required
    @users.expect(user)
    @users.marshal_with(user)
    @users.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set user."""
        if dict_user := ca.settings.get_user_byid(id):
            if dict_user["name"] != users.payload["name"] and ca.settings.has_username(
                users.payload["name"]
            ):
                abort(422, "User name is already exists, please change.")
            users.payload["id"] = id
            if (pwd := users.payload.get("password")) is None:
                users.payload["password"] = dict_user["password"]
            else:
                users.payload["password"] = generate_password_hash(pwd)
            ca.settings.users.remove(dict_user)
            ca.settings.users.append(users.payload)
            ca.settings.update(users=ca.settings.users)
            return users.payload
        abort(404, "User not found")

    @token_required
    @users.response(204, "Actions is success")
    @users.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete user."""
        if dict_user := ca.settings.get_user_byid(id):
            ca.settings.users.remove(dict_user)
            ca.settings.update(users=ca.settings.users)
            return "", 204
        abort(404, "User not found")


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
    def post(self):
        """Create button."""
        if ca.settings.get("ubuttons") is None:
            ca.settings.ubuttons = []
        ids = [button["id"] for button in ca.settings.ubuttons]
        buttons.payload["id"] = 1 if len(ids) == 0 else max(ids) + 1
        ca.settings.ubuttons.append(buttons.payload)
        ca.settings.update(buttons=ca.settings.ubuttons)
        return buttons.payload


@buttons.response(403, "Forbidden", message)
@buttons.route("/buttons/<int:id>")
class Button(Resource):
    """Button objet."""

    def get_byid(self, id: int):  # pylint: disable=W0622
        """Return button."""
        for button_dict in ca.settings.get("ubuttons", []):
            if button_dict["id"] == id:
                return button_dict

    @token_required
    @buttons.marshal_with(button)
    @buttons.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get button."""
        if button_dict := self.get_byid(id):
            return button_dict
        abort(404, "Button not found")

    @token_required
    @buttons.expect(button)
    @buttons.marshal_with(button)
    @buttons.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set button."""
        if dict_button := self.get_byid(id):
            ca.settings.ubuttons.remove(dict_button)
            buttons.payload["id"] = id
            ca.settings.ubuttons.append(buttons.payload)
            ca.settings.update(ubuttons=ca.settings.ubuttons)
            return buttons.payload
        abort(404, "Button not found")

    @token_required
    @buttons.response(204, "Actions is success")
    @buttons.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete button."""
        if dict_button := self.get_byid(id):
            ca.settings.ubuttons.remove(dict_button)
            ca.settings.update(ubuttons=ca.settings.ubuttons)
            return "", 204
        abort(404, "Button not found")


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
    @settings.response(204, "Action is success")
    def post(self):
        """Set setttings."""
        ca.settings.update(**settings.payload)
        if loglevel := settings.payload.get("loglevel"):
            ca.logger.setLevel(loglevel)
        return "", 204


@settings.response(403, "Forbidden", message)
@settings.route("/token")
class Token(Resource):
    """Token."""

    @token_required
    @settings.marshal_with(settings.model("Token", {"token": fields.String()}))
    def get(self):
        """Get token."""
        return {"token": ca.settings.get("token")}

    @token_required
    @settings.marshal_with(settings.model("Token", {"token": fields.String()}))
    def post(self):
        """Create token."""
        token = f"B{random.getrandbits(256)}"
        ca.settings.update(token=token)
        return {"token": token}

    @token_required
    @settings.response(204, "Actions is success")
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
    @settings.expect(macros)
    @settings.marshal_with(macros)
    @settings.response(204, "Action is success")
    def post(self):
        """Set macro."""
        if settings.payload:
            name = settings.payload["name"]
            command = settings.payload["command"]
            if not settings.payload["state"]:
                command = f"-{command}"
            ca.raspiconfig.set_config({name: command})
        return "", 204


class UriOTP(fields.Raw):
    """totp SVG."""

    def output(self, key, obj, **kwargs):
        if not obj:
            return
        name = obj["name"]
        secret = obj["secret"]
        uri = f"otpauth://totp/viewpicam:{name}?secret={secret}&issuer=viewpicam"
        qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
        qr.make(fit=True)
        qr.add_data(uri)
        img = qr.make_image()
        return img.to_string(encoding="unicode")


otp = users.model(
    "TOTP",
    {
        "id": fields.Integer(required=True, description="Id"),
        "name": fields.String(required=True, description="The user name"),
        "otp_svg": UriOTP(required=False),
        "totp": fields.Boolean(required=False),
    },
)


@otps.response(403, "Forbidden", message)
@otps.route("/totp", doc=False, endpoint="users_totp")
@otps.route("/totp/<int:id>")
class Totp(Resource):
    """TOTP."""

    @token_required
    @otps.marshal_with(otp)
    @otps.response(204, "OTP already enabled")
    @otps.response(422, "Error", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get OTP for a user."""
        if dict_user := ca.settings.get_user_byid(id):
            if dict_user.get("totp", False) is False:
                ca.settings.users.remove(dict_user)
                dict_user["secret"] = pyotp.random_base32()
                ca.settings.users.append(dict_user)
                ca.settings.update(users=ca.settings.users)
            return dict_user
        abort(404, "User not found")

    @token_required
    @otps.response(204, "Action is success")
    @otps.response(404, "Not found", message)
    def post(self, id: int):  # pylint: disable=W0622
        """Check OTP code."""
        if dict_user := ca.settings.get_user_byid(id):
            if (secret := dict_user.get("secret")) and dict_user.get("totp", False):
                totp = pyotp.TOTP(secret)
                if totp.verify(otps.payload["secret"]):
                    return "", 204
                abort(422, "OTP incorrect")
            abort(422, "OTP not enable")
        abort(404, "User not found")

    @token_required
    @otps.response(204, "Action is success")
    @otps.response(404, "Not found", message)
    @otps.response(422, "Error", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Check and create OTP Code for a user."""
        if (dict_user := ca.settings.get_user_byid(id)) and (
            secret := dict_user.get("secret")
        ):
            totp = pyotp.TOTP(secret)
            if totp.verify(otps.payload["secret"]):
                ca.settings.users.remove(dict_user)
                dict_user["totp"] = True
                ca.settings.users.append(dict_user)
                ca.settings.update(users=ca.settings.users)
                return "", 204
            abort(422, "OTP incorrect")
        abort(404, "User or otp code not found")

    @token_required
    @otps.response(204, "Action is success")
    @otps.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete OTP infos for a user."""
        if dict_user := ca.settings.get_user_byid(id):
            ca.settings.users.remove(dict_user)
            dict_user.pop("totp", None)
            dict_user.pop("secret", None)
            ca.settings.users.append(dict_user)
            ca.settings.update(users=ca.settings.users)
            return "", 204
        abort(404, "User not found")
