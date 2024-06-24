"""Blueprint for Camera."""

import glob
import os
import time

from flask import Blueprint, Response, request
from flask import current_app as ca
from flask_login import login_required

bp = Blueprint("camera", __name__, url_prefix="/cam")


@bp.route("/cam_pic", methods=["GET"])
@login_required
def cam_pic():
    delay = float(request.args.get("delay", 100)) / 1000  # Unit (ms)
    cam_jpg = _get_shm_cam()
    time.sleep(delay)
    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "image/jpeg"}
    return Response(cam_jpg, headers=headers)


@bp.route("/cam_picLatestTL", methods=["GET"])
@login_required
def cam_pictl():
    media_path = ca.raspiconfig.media_path
    list_of_files = filter(os.path.isfile, glob.glob(media_path + "*"))
    list_of_files = sorted(list_of_files, key=lambda x: os.stat(x).st_ctime)
    last_element = list_of_files[-1]
    last_jpeg = open(f"{media_path}/{last_element}", "rb").read()
    return Response(last_jpeg, headers={"Content-Type": "image/jpeg"})


@bp.route("/cam_get", methods=["GET"])
@login_required
def cam_get():
    os.popen(f"touch {ca.config.root_path}/status_mjpeg.txt")
    cam_jpg = _get_shm_cam()
    return Response(cam_jpg, headers={"Content-Type": "image/jpeg"})


@bp.route("/cam_pic_new", methods=["GET"])
@login_required
def cam_pic_new():
    delay = float(request.args.get("delay", 100)) / 1000  # Unit (ms)
    preview_path = ca.raspiconfig.preview_path
    return Response(
        _gather_img(preview_path, delay),
        mimetype="multipart/x-mixed-replace; boundary=PIderman",
    )


@bp.route("/status_mjpeg", methods=["GET"])
@login_required
def status_mjpeg():
    """Return status_mjpeg."""
    file_content = ""
    for _ in range(0, 30):
        with open(ca.raspiconfig.status_file, encoding="utf-8") as file:
            file_content = file.read()
            if file_content != request.args.get("last"):
                break
            time.sleep(0.1)
            file.close()
    os.popen(f"touch {ca.raspiconfig.status_file}")
    return Response(file_content)


def _get_shm_cam(preview_path=None):
    """Return binary data from cam.jpg."""
    preview_path = ca.raspiconfig.preview_path if preview_path is None else preview_path

    display_path = (
        preview_path
        if os.path.isfile(preview_path)
        else "app/resources/img/unavailable.jpg"
    )

    with open(display_path, "rb") as file:
        return file.read()


def _gather_img(preview_path, delay=0.1):
    """Stream image."""
    while True:
        yield (
            b"--PIderman\r\nContent-Type: image/jpeg\r\n\r\n"
            + _get_shm_cam(preview_path)
            + b"\r\n"
        )
        time.sleep(delay)
