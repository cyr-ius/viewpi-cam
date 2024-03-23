"""Error handler."""

import qrcode
import qrcode.image.svg
from flask import url_for
from flask_restx import Model, fields

from ..config import LOCALES


class PathURI(fields.Raw):
    """Path URI."""

    def format(self, value):
        """Form string."""
        return url_for("static", filename=value)


class UriOTP(fields.Raw):
    """totp SVG."""

    def output(self, key, obj, **kwargs):
        """Display QR Code."""
        if not obj:
            return
        uri = f"otpauth://totp/viewpicam:{obj.name}?secret={obj.otp_secret}&issuer=viewpicam"
        qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
        qr.make(fit=True)
        qr.add_data(uri)
        img = qr.make_image()
        return img.to_string(encoding="unicode")


wild = fields.Wildcard(fields.List(fields.Integer()))
button = Model(
    "Button",
    {
        "display": fields.Boolean(required=True, description="Display"),
        "name": fields.String(required=True, description="Button name"),
        "macro": fields.String(required=True, description="Script name"),
        "css_class": fields.String(required=False, description="Class"),
        "style": fields.String(required=False, description="Style"),
        "other": fields.String(required=False, description="Others options"),
    },
)

buttons = Model(
    "Buttons",
    {
        "id": fields.Integer(required=True, description="Id"),
        **button,
    },
)
command = Model(
    "Command",
    {
        "cmd": fields.String(description="Command", required=True),
        "params": fields.List(
            fields.String(), description="Parameters", required=False
        ),
    },
)
date_time = Model("Datetime", {"datetime": fields.DateTime(dt_format="iso8601")})
day = Model("Day", {"*": wild})
daymode = Model("Daymode", {"daymode": fields.Integer(description="Day mode")})
files = Model(
    "Files",
    {
        "id": fields.String(required=True, description="Id"),
        "file_name": fields.String(required=True, description="File name"),
        "file_type": fields.String(required=True, description="I/T/V"),
        "file_size": fields.Integer(required=True, description="Size"),
        # "file_icon": fields.String(required=False, description="Icon"),
        "file_datetime": fields.DateTime(required=False, description="DateTime"),
        "file_lock": fields.Boolean(
            required=True, description="Read/Write right on disk"
        ),
        "real_file": fields.String(required=True, description="Original name"),
        "file_number": fields.String(required=True, description="Index"),
        "lapse_count": fields.Integer(
            required=False, description="image numbers of timelapse"
        ),
        "duration": fields.Float(
            required=False, description="image numbers of timelapse"
        ),
        "uri": PathURI(attribute="file_name", example="string"),
    },
)
forbidden = Model(
    "Forbidden", {"message": fields.String(default="The provided API key is not valid")}
)
macros = Model(
    "Macros",
    {
        "name": fields.String(required=True, description="Macro name"),
        "command": fields.String(required=True, description="Script execute"),
        "state": fields.Boolean(required=True, description="Enable", default=False),
    },
)
message = Model("Error", {"message": fields.String(required=True)})
period = Model("Period", {"period": fields.String(description="period")})
schedule = Model(
    "Schedule",
    {
        "autocamera_interval": fields.Integer(required=True, description="File name"),
        "autocapture_interval": fields.Integer(required=True, description="I/T/V"),
        "cmd_poll": fields.Float(required=True, description="Size"),
        "command_off": fields.List(fields.String(description="Command")),
        "command_on": fields.List(fields.String(description="Command")),
        "dawnstart_minute": fields.Integer(
            required=True, description="Read/Write right on disk"
        ),
        "daystart_minute": fields.Integer(
            required=True, description="Read/Write right on disk"
        ),
        "dayend_minute": fields.Integer(
            required=True, description="Read/Write right on disk"
        ),
        "daymode": fields.Integer(required=True, description="Original name"),
        "days": fields.Nested(day),
        "gmt_offset": fields.String(
            required=False, description="image numbers of timelapse"
        ),
        "latitude": fields.Float(
            required=False, description="image numbers of timelapse"
        ),
        "longitude": fields.Float(
            required=False, description="image numbers of timelapse"
        ),
        "managment_command": fields.String(
            required=False, description="image numbers of timelapse"
        ),
        "managment_interval": fields.Integer(
            required=True, description="Original name"
        ),
        "max_capture": fields.Integer(required=True, description="Size"),
        "mode_poll": fields.Integer(required=True, description="Size"),
        "modes": fields.List(fields.String(description="mode")),
        "purgeimage_hours": fields.Integer(required=True, description="Size"),
        "purgelapse_hours": fields.Integer(required=True, description="Size"),
        "purgevideo_hours": fields.Integer(required=True, description="Size"),
        "purgespace_level": fields.Integer(required=True, description="Size"),
        "purgespace_modeex": fields.Integer(required=True, description="Size"),
        "times": fields.List(fields.String(description="time")),
    },
)
setting = Model(
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
locale = Model("Locale", {"locale": fields.String(enumerate=LOCALES)})
multiview = Model(
    "Multiview",
    {
        "url": fields.String(
            required=True,
            description="URL Stream MJPEG",
            example="http://192.168.1.1/cam/cam_pic?token=Bxxxxxxxxxxxxx",
        ),
        "delay": fields.Integer(required=True, description="Refresh rate"),
        "state": fields.Boolean(
            required=True, default=False, description="Display camera"
        ),
    },
)
multiviews = Model(
    "Multiviews",
    {
        "id": fields.Integer(required=True, description="Id"),
        **multiview,
    },
)
cam_token = Model("CamToken", {"cam_token": fields.String(required=True)})
api_token = Model("APIToken", {"api_token": fields.String(required=True)})
otp = Model(
    "TOTP",
    {
        "id": fields.Integer(required=True, description="Id"),
        "name": fields.String(required=True, description="The user name"),
        "otp_svg": UriOTP(required=False),
        "otp_confirmed": fields.Boolean(required=False, description="otp status"),
    },
)
user = Model(
    "User",
    {
        "name": fields.String(required=True, description="The user name"),
        "right": fields.Integer(
            required=True, description="The user rights", enum=[1, 2, 4, 8]
        ),
        "otp_confirmed": fields.Boolean(required=False, description="otp status"),
    },
)
users = Model(
    "Users",
    {
        "id": fields.Integer(required=True, description="Id"),
        **user,
    },
)
deletes = Model(
    "Deletes",
    {"thumb_id": fields.List(fields.String(description="id thumb"), default=None)},
)
