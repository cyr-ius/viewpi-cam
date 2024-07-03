"""Confilg file."""

import os

# GENERAL SETTINGS
SITE_NAME = "ViewPI Camera"
VERSION = os.getenv("VERSION", "0.0.0")

# BASIC APP CONFIG
SECRET_KEY = os.getenv("SECRET_KEY", "12345678900987654321")
SESSION_TYPE = "filesystem"

# COOKIE SECURE
# SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Allowed extension for mask file
ALLOWED_EXTENSIONS = ["pgm", "zip"]
MASK_FILENAME = "motionmask.pgm"

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
RSYNC_BINARY = "/usr/bin/rsync"
MEDIA_FOLDER = "media"

# Character used to flatten file paths
THUMBNAIL_EXT = ".th.jpg"

# Select size metho 0=python , 1=stats
FILESIZE_METHOD = 0

# File for settings
SERVO_FILE = "servo"
PIPAN_FILE = "pipan"

# Convert command
CONVERT_CMD = "/usr/bin/ffmpeg -f image2 -i i_%05d.jpg"

# Userlevel
USERLEVEL_MIN = 1
USERLEVEL_MINP = 2
USERLEVEL_MEDIUM = 4
USERLEVEL_MAX = 8
USERLEVEL = {
    "min": USERLEVEL_MIN,
    "preview": USERLEVEL_MINP,
    "medium": USERLEVEL_MEDIUM,
    "max": USERLEVEL_MAX,
}

# Locales
LOCALES = ["en", "fr"]

# Macros name files
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

# Filter number
TIME_FILTER_MAX = 8

# Starts services
SVC_RASPIMJPEG = os.getenv("SVC_RASPIMJPEG", "1")
SVC_SCHEDULER = os.getenv("SVC_SCHEDULER", "1")

# API Swagger documentation
SWAGGER_UI_DOC_EXPANSION = "list"
SWAGGER_UI_OPERATION_ID = True
SWAGGER_UI_REQUEST_DURATION = True
RESTX_MASK_SWAGGER = False
RESTX_ERROR_404_HELP = False

# Schedule state
SCHEDULE_RESET = "9"
SCHEDULE_UPDATE = "8"
SCHEDULE_START = "1"
SCHEDULE_STOP = "0"

# Motion
MOTION_URL = "http://127.0.0.1:6642/0/"
MOTION_CONFIGBACKUP = "motionPars.json"
MOTION_PARS = "motionPars"
MOLTION_FILTER = [
    "switchfilter",
    "threshold",
    "threshold_tune",
    "noise_level",
    "noise_tune",
    "despeckle",
    "despeckle_filter",
    "area_detect",
    "mask_file",
    "smart_mask_speed",
    "lightswitch",
    "minimum_motion_frames",
    "framerate",
    "minimum_frame_time",
    "netcam_url",
    "netcam_userpass",
    "gap",
    "event_gap",
    "on_event_start",
    "on_event_end",
    "on_motion_detected",
    "on_area_detected",
]
