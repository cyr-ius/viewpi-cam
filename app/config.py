"""Confilg file."""
import os

from .const import (
    ATTR_AUTOCAMERAINTERVAL,
    ATTR_AUTOCAPTUREINTERVAL,
    ATTR_CMDPOLL,
    ATTR_COMMANDSOFF,
    ATTR_COMMANDSON,
    ATTR_DAWNSTARTMINUTES,
    ATTR_DAYENDMINUTES,
    ATTR_DAYMODE,
    ATTR_DAYS,
    ATTR_DAYSTARTMINUTES,
    ATTR_DUSKENDMINUTES,
    ATTR_GMTOFFSET,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_MAXCAPTURE,
    ATTR_MGMTCOMMAND,
    ATTR_MGMTINTERVAL,
    ATTR_MODE_ALLDAY,
    ATTR_MODE_POLL,
    ATTR_MODES,
    ATTR_PILIGHT,
    ATTR_PIPAN,
    ATTR_PRESET,
    ATTR_PURGEIMAGEHOURS,
    ATTR_PURGELAPSEHOURS,
    ATTR_PURGESPACELEVEL,
    ATTR_PURGESPACEMODE,
    ATTR_PURGEVIDEOHOURS,
    ATTR_SERVO,
    ATTR_TIMES,
    ATTR_USER_BUTTONS,
    ATTR_USERS,
    SCHEDULE_TIMES_MAX,
)

basedir = os.path.abspath(os.path.abspath(os.path.dirname(__file__)))

# GENERAL SETTINGS
SITE_NAME = "ViewPI Camera"
VERSION = os.getenv("VERSION", "v0.0.0")

# BASIC APP CONFIG
SECRET_KEY = os.getenv("SECRET_KEY", "12345678900987654321")
SESSION_TYPE = "filesystem"

# DEFAULT ACCOUNT
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin")
APP_MAIL = os.getenv("APP_MAIL", "please_change_me@localhost")

# The host running the application
HOSTNAME = os.uname()[1]
# Name of this camera
CAM_NAME = "mycam"
# Unique camera string build from application name, camera name, host name
CAM_STRING = f"{SITE_NAME} {VERSION}: {CAM_NAME}@{HOSTNAME}"
# File where default settings
RASPI_CONFIG = "/etc/raspimjpeg"
RASPI_BINARY = "/usr/bin/raspimjpeg"
# File where user specific settings changes are stored
MEDIA = "media"
# Character used to flatten file paths
THUMBNAIL_EXT = ".th.jpg"
# File where a debug file is stored
LOGFILE_DEBUG = "debug.log"
# Select size metho 0=python , 1=stats
FILESIZE_METHOD = 0
# File for settings
FILE_SETTINGS = f"{basedir}/../system/settings.json"
SERVO_FILE = f"{basedir}/../system/servo"
PIPAN_FILE = f"{basedir}/../system/pipan"
# Convert command
CONVERT_CMD = "/usr/bin/ffmpeg -f image2 -i i_%05d.jpg"

# USER LEVEL
USERLEVEL_MIN = 1
USERLEVEL_MINP = 2  # minimum+preview
USERLEVEL_MEDIUM = 4
USERLEVEL_MAX = 8

# MACROS
MACROS = [
    "error_soft",
    "error_hard",
    "start_img",
    "end_img",
    "start_vid",
    "end_vid",
    "end_box",
    "do_cmd",
    "motion_event",
    "startstop",
]

# API Swagger documentation
SWAGGER_UI_DOC_EXPANSION = "list"
SWAGGER_UI_OPERATION_ID = True
SWAGGER_UI_REQUEST_DURATION = True
RESTX_MASK_SWAGGER = False

# Default settings
DEFAULT_INIT = {
    ATTR_USERS: {},
    ATTR_USER_BUTTONS: {},
    ATTR_AUTOCAMERAINTERVAL: 0,
    ATTR_AUTOCAPTUREINTERVAL: 0,
    ATTR_CMDPOLL: 0.03,
    ATTR_COMMANDSOFF: ["ca 0", "", "", "ca 0", "", "", "", "", "", "", ""],
    ATTR_COMMANDSON: ["ca 1", "", "", "ca 1", "", "", "", "", "", "", ""],
    ATTR_DAWNSTARTMINUTES: -180,
    ATTR_DAYENDMINUTES: 0,
    ATTR_DAYMODE: ATTR_MODE_ALLDAY,
    ATTR_DAYS: {
        f"{i}": [1, 1, 1, 1, 1, 1, 1] for i in range(0, SCHEDULE_TIMES_MAX + 5)
    },
    ATTR_DAYSTARTMINUTES: 0,
    ATTR_DUSKENDMINUTES: 180,
    ATTR_GMTOFFSET: "Etc/UTC",
    ATTR_LATITUDE: 52.00,
    ATTR_LONGITUDE: 0.00,
    ATTR_MGMTCOMMAND: "",
    ATTR_MGMTINTERVAL: 3600,
    ATTR_MAXCAPTURE: 0,
    ATTR_MODES: [
        "",
        "em night",
        "md 1;em night",
        "em auto",
        "md 0;em night",
        "",
        "",
        "",
        "",
        "",
        "",
    ],
    ATTR_MODE_POLL: 10,
    ATTR_PURGEIMAGEHOURS: 0,
    ATTR_PURGELAPSEHOURS: 0,
    ATTR_PURGESPACELEVEL: 10,
    ATTR_PURGESPACEMODE: 0,
    ATTR_PURGEVIDEOHOURS: 0,
    ATTR_TIMES: [f"{i + 9:02d}:00" for i in range(0, SCHEDULE_TIMES_MAX)],
    ATTR_PIPAN: 0,
    ATTR_SERVO: 0,
    ATTR_PILIGHT: 0,
    ATTR_PRESET: "v2",
}
