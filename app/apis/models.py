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


class Days(fields.Raw):
    def output(self, key, obj, **kwargs):
        calendar = {}
        for idx, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            for item in obj.calendars:
                if item.name == day:
                    calendar.update({int(idx): 1})
                    break
            else:
                calendar.update({int(idx): 0})

        return calendar


class DayMode(fields.Raw):
    def output(self, key, obj, **kwargs):
        return obj.daysmode_id


api_token = Model("APIToken", {"api_token": fields.String(required=True)})
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
    "Buttons", {"id": fields.Integer(required=True, description="Id"), **button}
)
cam_token = Model("CamToken", {"cam_token": fields.String(required=True)})
calendar = Model(
    "Calendar",
    {"id": fields.Integer(required=True), "name": fields.String(required=True)},
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
daymode = Model("Daymode", {"daymode": fields.Integer(description="Day mode")})
daysmode = Model(
    "Daysmode",
    {"id": fields.Integer(required=True), "name": fields.String(required=True)},
)
deletes = Model(
    "Deletes",
    {"thumb_id": fields.List(fields.String(description="id thumb"), default=None)},
)
files = Model(
    "Files",
    {
        "id": fields.String(required=True, description="Id"),
        "name": fields.String(required=True, description="File name"),
        "type": fields.String(required=True, description="I/T/V"),
        "size": fields.Integer(required=True, description="Size"),
        # "file_icon": fields.String(required=False, description="Icon"),
        "datetime": fields.DateTime(required=False, description="DateTime"),
        "lock": fields.Boolean(
            required=True, description="Read/Write right on disk", default=False
        ),
        "realname": fields.String(required=True, description="Original name"),
        "number": fields.String(required=True, description="Index"),
        "lcount": fields.Integer(
            required=False, description="image numbers of timelapse"
        ),
        "duration": fields.Float(
            required=False, description="image numbers of timelapse"
        ),
        "uri": PathURI(attribute="name", example="string"),
    },
)
locales = Model("Locales", {"locales": fields.List(fields.String(enumerate=LOCALES))})
lock_mode = Model(
    "LockMode",
    {
        "mode": fields.Boolean(required=True, description="Locked is true"),
        "ids": fields.List(fields.String()),
    },
)
log = Model(
    "Log",
    {
        "datetime": fields.String(required=True),
        "level": fields.String(required=True),
        "msg": fields.String(required=True),
    },
)
macro = Model(
    "Macro",
    {
        "name": fields.String(required=True, description="Macro name"),
        "command": fields.String(required=True, description="Script execute"),
        "state": fields.Boolean(required=True, description="Enable", default=False),
    },
)
message = Model("Msg", {"message": fields.String(required=True)})
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
    "Multiviews", {"id": fields.Integer(required=True, description="Id"), **multiview}
)
otp = Model(
    "Otp",
    {
        "id": fields.Integer(required=True, description="Id"),
        "name": fields.String(required=True, description="The user name"),
        "otp_svg": UriOTP(required=False),
        "otp_confirmed": fields.Boolean(required=False, description="otp status"),
    },
)
period = Model("Period", {"period": fields.String(description="period")})
schedule = Model(
    "Schedule",
    {
        "autocamera_interval": fields.Integer(required=True),
        "autocapture_interval": fields.Integer(required=True),
        "cmd_poll": fields.Float(required=True),
        "dawnstart_minutes": fields.Integer(required=True),
        "dayend_minutes": fields.Integer(required=True),
        "daymode": fields.Integer(required=True),
        "daystart_minutes": fields.Integer(required=True),
        "duskend_minutes": fields.Integer(required=True),
        "gmt_offset": fields.String(required=False),
        "latitude": fields.Float(required=False),
        "longitude": fields.Float(required=False),
        "managment_command": fields.String(required=False),
        "managment_interval": fields.Integer(required=True),
        "max_capture": fields.Integer(required=True),
        "mode_poll": fields.Integer(required=True),
        "purgeimage_hours": fields.Integer(required=True),
        "purgelapse_hours": fields.Integer(required=True),
        "purgevideo_hours": fields.Integer(required=True),
        "purgespace_level": fields.Integer(required=True),
        "purgespace_modeex": fields.Integer(required=True),
    },
)
scheduler = Model(
    "Scheduler",
    {
        "id": fields.Integer(required=True),
        "command_on": fields.String(),
        "command_off": fields.String(),
        "daysmode": fields.Nested(daysmode),
        "daysmode_id": fields.Integer(),
        "daymode": DayMode(required=True),
        "enabled": fields.Boolean(required=True),
        "mode": fields.String(),
        "period": fields.String(required=True),
        "days": Days(),
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
rsync = Model(
    "Rsync",
    {
        "rs_enabled": fields.String(required=True, default=False),
        "rs_user": fields.String(required=True, default=""),
        "rs_pwd": fields.String(required=True, default=""),
        "rs_direction": fields.String(required=True, default=""),
        "rs_mode": fields.String(required=True, default="Module"),
        "rs_remote_host": fields.String(required=True, default=""),
        "rs_options": fields.List(fields.String(default=None), default=["-a", "-z"]),
    },
)
secret = Model(
    "Secret", {"secret": fields.String(required=True, description="OTP code")}
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
users = Model("Users", {"id": fields.Integer(required=True, description="Id"), **user})
