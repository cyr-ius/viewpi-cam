"""Confilg file."""
import os

from .const import LBL_PERIODS, LEVELS

basedir = os.path.abspath(os.path.abspath(os.path.dirname(__file__)))

# GENERAL SETTINGS
SITE_NAME = "ViewPI Camera"
VERSION = os.getenv("VERSION", "v0.0.0")

# BASIC APP CONFIG
SECRET_KEY = os.getenv("SECRET_KEY", "12345678900987654321")
SESSION_TYPE = "filesystem"

# COOKIE SECURE
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# The host running the application
HOSTNAME = os.uname()[1]
# Url and timeout to fetch version from github
GIT_URL = "https://api.github.com/repos/cyr-ius/viewpi-cam/releases/latest"
TIMEOUT = 10
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
# Select size metho 0=python , 1=stats
FILESIZE_METHOD = 0
# File for settings
FILE_SETTINGS = f"{basedir}/../system/settings.json"
SERVO_FILE = f"{basedir}/../system/servo"
PIPAN_FILE = f"{basedir}/../system/pipan"
# Convert command
CONVERT_CMD = "/usr/bin/ffmpeg -f image2 -i i_%05d.jpg"
# Userlevel
USERLEVEL = LEVELS
# Locales
LOCALES = ["en", "fr"]

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
PERIODS = LBL_PERIODS
TIME_FILTER_MAX = 8
SCHEDULE_TIMES_MAX = 12

# API Swagger documentation
SWAGGER_UI_DOC_EXPANSION = "list"
SWAGGER_UI_OPERATION_ID = True
SWAGGER_UI_REQUEST_DURATION = True
RESTX_MASK_SWAGGER = False

# Default settings
DEFAULT_INIT = {
    "autocamera_interval": 0,
    "autocapture_interval": 0,
    "cmd_poll": 0.03,
    "commands_off": ["ca 0", "", "", "ca 0", "", "", "", "", "", "", ""],
    "commands_on": ["ca 1", "", "", "ca 1", "", "", "", "", "", "", ""],
    "dawnstart_minutes": -180,
    "dayend_minutes": 0,
    "daymode": 1,
    "days": {f"{i}": [1, 1, 1, 1, 1, 1, 1] for i in range(0, SCHEDULE_TIMES_MAX + 5)},
    "daystart_minutes": 0,
    "duskend_minutes": 180,
    "gmt_offset": "Etc/UTC",
    "latitude": 52.00,
    "longitude": 0.00,
    "management_command": "",
    "management_interval": 3600,
    "max_capture": 0,
    "modes": [
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
    "mode_poll": 10,
    "purgeimage_hours": 0,
    "purgelapse_hours": 0,
    "purgespace_level": 10,
    "purgespace_modeex": 0,
    "purgevideo_hours": 0,
    "times": [f"{i + 9:02d}:00" for i in range(0, SCHEDULE_TIMES_MAX)],
    "pipan": 0,
    "servo": 0,
    "pilight": 0,
    "upreset": "v2",
}
