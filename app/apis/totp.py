"""Blueprint API."""
import pyotp
import qrcode
import qrcode.image.svg
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort, fields

from ..helpers.decorator import token_required
from .models import message

api = Namespace("otps")
api.add_model("Error", message)


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


otp = api.model(
    "TOTP",
    {
        "id": fields.Integer(required=True, description="Id"),
        "name": fields.String(required=True, description="The user name"),
        "otp_svg": UriOTP(required=False),
        "totp": fields.Boolean(required=False),
    },
)


@api.response(403, "Forbidden", message)
@api.route("/totp", doc=False, endpoint="users_totp")
@api.route("/totp/<int:id>")
class Totp(Resource):
    """TOTP."""

    @token_required
    @api.marshal_with(otp)
    @api.response(204, "OTP already enabled")
    @api.response(422, "Error", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get OTP for a user."""
        if dict_user := ca.settings.get_object("users", id):
            if dict_user.get("totp", False) is False:
                ca.settings.users.remove(dict_user)
                dict_user["secret"] = pyotp.random_base32()
                ca.settings.users.append(dict_user)
                if len(ca.settings.users) > 0:
                    ca.settings.update(users=ca.settings.users)
            return dict_user
        abort(404, "User not found")

    @token_required
    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    def post(self, id: int):  # pylint: disable=W0622
        """Check OTP code."""
        if dict_user := ca.settings.get_object("users", id):
            if (secret := dict_user.get("secret")) and dict_user.get("totp", False):
                totp = pyotp.TOTP(secret)
                if totp.verify(api.payload["secret"]):
                    return "", 204
                abort(422, "OTP incorrect")
            abort(422, "OTP not enable")
        abort(404, "User not found")

    @token_required
    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    @api.response(422, "Error", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Check and create OTP Code for a user."""
        if (dict_user := ca.settings.get_object("users", id)) and (
            secret := dict_user.get("secret")
        ):
            totp = pyotp.TOTP(secret)
            if totp.verify(api.payload["secret"]):
                ca.settings.users.remove(dict_user)
                dict_user["totp"] = True
                ca.settings.users.append(dict_user)
                if len(ca.settings.users) > 0:
                    ca.settings.update(users=ca.settings.users)
                return "", 204
            abort(422, "OTP incorrect")
        abort(404, "User or otp code not found")

    @token_required
    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete OTP infos for a user."""
        if dict_user := ca.settings.get_object("users", id):
            ca.settings.users.remove(dict_user)
            dict_user.pop("totp", None)
            dict_user.pop("secret", None)
            ca.settings.users.append(dict_user)
            if len(ca.settings.users) > 0:
                ca.settings.update(users=ca.settings.users)
            return "", 204
        abort(404, "User not found")
