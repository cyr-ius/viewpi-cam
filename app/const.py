BTN_START = "Start"
BTN_STOP = "Stop"
BTN_SAVE = "Save Settings"
BTN_BACKUP = "Backup"
BTN_RESTORE = "Restore"
BTN_SHOWLOG = "Show Log"
BTN_DOWNLOADLOG = "Download Log"
BTN_CLEARLOG = "Clear Log"

BTN_DOWNLOAD = "Download"
BTN_DELETE = "Delete"
BTN_DELETE_CONFIRM = "Are you sure you want to delete this file?"
BTN_CONVERT = "Start Convert"
BTN_DELETEALL = "Delete All"
BTN_DELETEALL_CONFIRM = "Are you sure you want to delete all items?"
BTN_DELETESEL = "Delete Selected"
BTN_DELETESEL_CONFIRM = "Are you sure you want to delete selected items?"
BTN_SELECTALL = "Select All"
BTN_SELECTNONE = "Deselect"
BTN_GETZIP = "Get Zip"
BTN_LOCKSEL = "Lock Sel"
BTN_UNLOCKSEL = "Unlock Selected"
BTN_UPDATESIZEORDER = "Update"

LBL_PERIODS = ["AllDay", "Night", "Dawn", "Day", "Dusk"]
LBL_COLUMNS = ["Period", "Days Su-Sa", "Motion Start", "Motion Stop", "Period Start"]
LBL_PARAMETERS = "Parameter", "Value"
LBL_DAYMODES = ["Sun based", "All Day", "Fixed Times"]
LBL_PURGESPACEMODES = [
    "Off",
    "Min Space %",
    "Max Usage %",
    "Min Space GB",
    "Max Usage GB",
]
LBL_DAWN = "Dawn"
LBL_DAY = "Day"
LBL_DUSK = "Dusk"

TXT_PREVIEW = "Preview"
TXT_THUMB = "Thumb"
TXT_FILES = "Files"
CONVERT_CMD = "convertCmd.txt"
CONTROLS_POS = "top"

SCHEDULE_START = "1"
SCHEDULE_STOP = "0"
SCHEDULE_RESET = "9"

SCHEDULE_ALLDAY = "all_days"
ATTR_AUTOCAMERAINTERVAL = "autocamera_interval"
ATTR_AUTOCAPTUREINTERVAL = "autocapture_interval"
ATTR_CMDPOLL = "cmd_poll"
ATTR_COMMANDSOFF = "commands_off"
ATTR_COMMANDSON = "commands_on"
ATTR_DAWNSTARTMINUTES = "dawnstart_minutes"
ATTR_DAYENDMINUTES = "dayend_minutes"
ATTR_DAYMODE = "daymode"
ATTR_DAYS = "days"
ATTR_DAYSTARTMINUTES = "daystart_minutes"
ATTR_DUSKENDMINUTES = "duskend_minutes"
SCHEDULE_FIFOIN = "fifo_in"
SCHEDULE_FIFOOUT = "fifo_out"
SCHEDULE_FIXEDTIMES = "fixed_times"
ATTR_GMTOFFSET = "gmt_offset"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_MGMTCOMMAND = "management_command"
ATTR_MGMTINTERVAL = "management_interval"
ATTR_MAXCAPTURE = "max_capture"
ATTR_MODE_ALLDAY = 1
SCHEDULE_MODE_FIXED = 2
SCHEDULE_MODE_SUN = 0
ATTR_MODE_POLL = "mode_poll"
ATTR_MODES = "modes"
ATTR_PURGEIMAGEHOURS = "purgeimage_hours"
ATTR_PURGELAPSEHOURS = "purgelapse_hours"
ATTR_PURGESPACELEVEL = "purgespace_level"
ATTR_PURGESPACEMODE = "purgespace_modeex"
ATTR_PURGEVIDEOHOURS = "purgevideo_hours"
ATTR_TIMES = "times"
ATTR_TIMES_VALUE = ["09:00"]
ATTR_TIMES_MAX = 12
SCHEDULE_ZENITH = 90.8

ATTR_USERS = "users"
ATTR_USER_BUTTONS = "ubuttons"

PRESETS = {
    "v2": {
        "N-Full HD 1080p 16:9 V2": "1920 1080 30 30 3280 2464",
        "N-Full HD 720p 16:9 V2": "1280 0720 30 30 3280 2464",
        "N-Max View 972p 4:3 V2": "1280 0720 30 30 3280 2464",
        "N-SD TV 576p 4:3 V2": "768 576 30 30 3280 2464",
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
