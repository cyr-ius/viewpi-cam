"""Constants."""
from flask_babel import lazy_gettext as _

LBL_PERIODS = [_("AllDay"), _("Night"), _("Dawn"), _("Day"), _("Dusk")]

TXT_MSG_1 = _("User or password is empty.")
TXT_MSG_2 = _("User or password invalid.")
TXT_MSG_3 = _("Access id denied.")

SCHEDULE_RESET = "9"
SCHEDULE_START = "1"
SCHEDULE_STOP = "0"

USERLEVEL_MIN = 1
USERLEVEL_MINP = 2
USERLEVEL_MEDIUM = 4
USERLEVEL_MAX = 8

LEVELS = {
    "min": USERLEVEL_MIN,
    "preview": USERLEVEL_MINP,
    "medium": USERLEVEL_MEDIUM,
    "max": USERLEVEL_MAX,
}

PRESETS = {
    "v2": {
        "Full HD 1080p 16:9 V2": "1920 1080 30 30 3280 2464",
        "Full HD 720p 16:9 V2": "1280 0720 30 30 3280 2464",
        "Max View 972p 4:3 V2": "1296 972 30 30 3280 2464",
        "SD TV 576p 4:3 V2": "768 576 30 30 3280 2464",
        "Full HD Timelapse (x30) 1080p 16:9 V2": "1920 1080 01 30 3280 2464",
    },
    "P-OV5647": {
        "N-OV5647-30fps-Full HD 1080p 16:9": "1920 1080 25 25 2592 1944",
        "N-OV5647-15fps-Full Chip 2959 X 1944 4:3": "2592 1944 15 15 2592 1944",
        "N-OV5647-42fps-Max View 1296 X 972 4:3": "1296 972 42 42 2592 1944",
        "N-OV5647-42fps-Max View 1296 X 730 16:9": "1296 730 49 49 2592 1944",
        "N-OV5647-90fps-SD TV 640 X 480 4:3": "640 480 90 90 2592 1944",
        "Full HD Timelapse (x30) 1080p 16:9": "1920 1080 01 30 2592 1944",
    },
    "P-IMX219": {
        "P-IMX219-25fps-Full HD 1080p 16:9": "1920 1080 25 25 3280 2464",
        "P-IMX219-15fps-Full Chip 2959 X 1944 4:3": "3280 2464 15 15 3280 2464",
        "P-IMX219-40fps-Max View 1640 X 1232 4:3": "1640 1232 40 40 3280 2464",
        "P-IMX219-40fps-Max View 1640 X 922 16:9": "1640 922 40 40 3280 2464",
        "P-IMX219-90fps-HD 720p 16:9": "1280 720 90 90 3280 2464",
        "P-IMX219-90fps-SD TV 640p 4:3": "640 480 90 90 3280 2464",
        "Full HD Timelapse (x30) 1080p 16:9": "1920 1080 01 30 3280 2464",
    },
    "N-OV5647": {
        "N-OV5647-30fps-Full HD 1080p 16:9": "1920 1080 30 30 2592 1944",
        "N-OV5647-15fps-Full Chip 2959 X 1944 4:3": "2592 1944 15 15 2592 1944",
        "N-OV5647-42fps-Max View 1296 X 972 4:3": "1296 972 42 42 2592 1944",
        "N-OV5647-42fps-Max View 1296 X 730 16:9": "1296 730 49 49 2592 1944",
        "N-OV5647-90fps-SD TV 640 X 480 4:3": "640 480 90 90 2592 1944",
        "Full HD Timelapse (x30) 1080p 16:9": "1920 1080 01 30 2592 1944",
    },
    "N-IMX219": {
        "N-IMX219-30fps-Full HD 1080p 16:9": "1920 1080 30 30 3280 2464",
        "N-IMX219-15fps-Full Chip 2959 X 1944 4:3": "3280 2464 15 15 3280 2464",
        "N-IMX219-40fps-Max View 1640 X 1232 4:3": "1640 1232 40 40 3280 2464",
        "N-IMX219-40fps-Max View 1640 X 922 16:9": "1640 922 40 40 3280 2464",
        "N-IMX219-90fps-HD 720p 16:9": "1280 720 90 90 3280 2464",
        "N-IMX219-90fps-SD TV 640p 4:3": "640 480 90 90 3280 2464",
        "Full HD Timelapse (x30) 1080p 16:9": "1920 1080 01 30 3280 2464",
    },
}
