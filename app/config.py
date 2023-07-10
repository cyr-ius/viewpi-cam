import os

basedir = os.path.abspath(os.path.abspath(os.path.dirname(__file__)))

# GENERAL SETTINGS
SITE_NAME = "ViewPI Camera"
VERSION = "v0.0.5"

# BASIC APP CONFIG
SALT = os.getenv("SALT", "ViewPICamera")
SECRET_KEY = os.getenv("SECRET_KEY", "12345678900987654321")
FILESYSTEM_SESSIONS_ENABLED = os.getenv("FILESYSTEM_SESSIONS_ENABLED", True)
SESSION_TYPE = "filesystem"

# MAIL
MAIL_SERVER = os.getenv("MAIL_SERVER", None)
MAIL_PORT = os.getenv("MAIL_PORT", 25)
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", False)
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", False)
MAIL_USERNAME = os.getenv("MAIL_USERNAME", None)
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", None)
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", None)
MAIL_MAX_EMAILS = os.getenv("MAIL_MAX_EMAILS", None)
MAIL_ASCII_ATTACHMENTS = os.getenv("MAIL_ASCII_ATTACHMENTS", False)

# DEFAULT ACCOUNT
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin")
APP_MAIL = os.getenv("APP_MAIL", "please_change_me@localhost")

# SETTINGS

# the host running the application
HOSTNAME = os.uname()[1]
# name of this camera
CAM_NAME = "mycam"
# unique camera string build from application name, camera name, host name
CAM_STRING = f"{SITE_NAME} {VERSION}: {CAM_NAME}@{HOSTNAME}"
# file where default settings changes are stored
CONFIG_FILE1 = "raspimjpeg"
# file where user specific settings changes are stored
CONFIG_FILE2 = "uconfig"
# file where user specific settings changes are stored
MEDIA = "media"
# Media full qualified path
MEDIA_PATH = f"{basedir}/{MEDIA}"
# character used to flatten file paths
SUBDIR_CHAR = "@"
# character used to flatten file paths
THUMBNAIL_EXT = ".th.jpg"
# file where a debug file is stored
LOGFILE_DEBUG = "debugLog.txt"
# file where schedule log is stored
LOGFILE_SCHEDULE = "scheduleLog.txt"
# control how filesize is extracted, 0 is fast and works for files up to 4GB, 1 is slower
FILESIZE_METHOD = 0
# User Buttons
USER_BUTTONS = "user_buttons.json"
# file for settings
FILE_SETTINGS = "settings.json"

# USER LEVEL
USERLEVEL_FILE = "userLevel"
USERLEVEL_MIN = 0
USERLEVEL_MINP = 1  # minimum+preview
USERLEVEL_MEDIUM = 2
USERLEVEL_MAX = 4

# SCHEDULER
SCHEDULE_CONFIG = "schedule.json"
SCHEDULE_CONFIGBACKUP = "schedule_backup.json"

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
