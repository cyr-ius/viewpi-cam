"""Blueprint for Motion (external capture)."""
import os
import time

from flask import Blueprint, json, request

from ..helpers.decorator import auth_required
from ..helpers.utils import get_pid

MOTION_URL = "http://127.0.0.1:6642/0"
MOTION_CONFIGBACKUP = "motionPars.json"
MOTION_PARS = "motionPars"
FILTER_PARS = [
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

bp = Blueprint("motion", __name__, url_prefix="/motion")


@bp.route("/motion", methods=["GET", "POST"])
@auth_required
def motion():
    # motion_ready = check_motion()
    # show_all = False
    # debug = ""

    response = request.get(f"{MOTION_URL}/config/list")
    motion_config = response.read()

    motions = _get_file_config(motion_config)

    if request.method == "POST" and (action := request.json.get("action")):
        match action:
            case "save":
                changed = False
                for key, value in request.json.item():
                    if key in motions:
                        if value != motions[key]:
                            set_motion(key, value)
                            changed = True
                if changed:
                    write_motion()
                    motion_config = restart_motion()
                    motions = _get_file_config(motion_config)

            # case "showAll":
            # show_all = True
            case "backup":
                backup = {}
                backup.setdefault(MOTION_PARS, motions)
                with open(MOTION_CONFIGBACKUP, mode="w", encoding="utf-8") as file:
                    json.dump(backup, file)
            case "restore":
                if os.path.isfile(MOTION_CONFIGBACKUP):
                    with open(MOTION_CONFIGBACKUP, mode="r", encoding="utf-8") as file:
                        restore = json.load(file)
                        motions = restore(MOTION_PARS)
                        for key, value in motions.items():
                            set_motion(key, value)
                            write_motion()
                            restart_motion()


def check_motion():
    return get_pid("motion") is not None


def set_motion(key, value):
    request.get(f"{MOTION_URL}/config/set?{key}={value}")


def write_motion():
    request.get(f"{MOTION_URL}/config/write")


def pause_motion():
    request.get(f"{MOTION_URL}/detection/pause")


def start_motion():
    request.get(f"{MOTION_URL}/detection/start")


def restart_motion():
    request.get(f"{MOTION_URL}/action/restart")
    retry = 20
    while request.status != 200 and retry < 20:
        retry -= 1
        time.sleep(1)
        return request.get(f"{MOTION_URL}/config/list")


def _get_file_config(filename, config: dict[str, any] = None):
    config = {} if not config else config
    if os.path.isfile(filename):
        with open(filename, mode="r", encoding="utf-8") as file:
            for line in file.read().split("\n"):
                if len(line) and line[0:1] != "#":
                    index = line.find(" ")
                    if index >= 0:
                        key = line[0:index]
                        value = line[index + 1 :]  # noqa: E203
                        if value == "true":
                            value = 1
                        if value == "false":
                            value = 0
                        config[key] = value
                    else:
                        config[line] = ""
            file.close()
    return config
