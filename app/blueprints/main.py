"""Blueprint Main."""

import os
import time
import urllib

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    json,
    jsonify,
    make_response,
    render_template,
    request,
    send_file,
)
from flask import current_app as ca
from flask_login import current_user, login_required

from ..apis.logs import get_logs
from ..helpers.decorator import role_required
from ..helpers.motion import MotionError, check_motion, get_motion
from ..helpers.utils import allowed_file, write_log
from ..models import Multiviews as multiviews_db
from ..models import Presets as presets_db
from ..models import Settings as settings_db
from ..models import Ubuttons as ubuttons_db
from ..services.raspiconfig import RaspiConfigError
from .camera import status_mjpeg

bp = Blueprint("main", __name__, template_folder="templates")


@bp.route("/", methods=["GET"])
@login_required
def index():
    """Index page."""
    settings = settings_db.query.first()
    write_log(f"Logged in user: {current_user.name}")
    write_log(f"UserLevel {current_user.right}")
    display_mode = request.cookies.get("display_mode", "On")
    mjpegmode = int(request.cookies.get("mjpegmode", 0))

    mode = 0
    cam_pos = None
    pipan_file = f"{ca.config_folder}/{ca.config['PIPAN_FILE']}"
    if os.path.isfile(pipan_file):
        mode = 1
        with open(pipan_file, encoding="utf-8") as file:
            pipan_sck = file.read().decode("utf-8")
            cam_pos = pipan_sck.split(" ")
            file.close()

    if settings.data.get("servo"):
        mode = 2

    motionconfig = None
    if check_motion():
        try:
            motionconfig = get_motion()
        except MotionError as error:
            flash("Motion config not found (%s)", error)

    presets = presets_db.query.filter_by(mode=settings.data["upreset"]).all()

    return render_template(
        "main.html",
        mode=mode,
        cam_pos=cam_pos,
        user_buttons=ubuttons_db.query.all(),
        raspiconfig=ca.raspiconfig,
        motionconfig=motionconfig,
        display_mode=display_mode,
        mjpegmode=mjpegmode,
        preset=settings.data["upreset"],
        presets=presets,
    )


@bp.route("/log", methods=["GET", "POST"])
@login_required
@role_required(["max"])
def log():
    """Log page (and download if post)."""
    if request.method == "POST":
        return send_file(ca.raspiconfig.log_file, as_attachment=True)
    return render_template("logs.html", log=get_logs(True))


@bp.route("/streamlog", methods=["GET"])
@login_required
@role_required(["max"])
def streamlog():
    """Stream log page."""
    log_file = ca.raspiconfig.log_file

    def generate(log_file):
        if os.path.isfile(log_file):
            with open(log_file, encoding="utf-8") as file:
                first = True
                while True:
                    if first:
                        # Remove first occurrence
                        file.read()
                        first = False
                    yield f"data: {file.read()}\n\n"
                    time.sleep(0.5)

    return Response(generate(log_file), mimetype="text/event-stream")


@bp.route("/debug", methods=["GET"])
@login_required
@role_required(["max"])
def debugcmd():
    """Debug page."""
    return render_template("debug.html", raspiconfig=ca.raspiconfig.__dict__)


@bp.route("/help", methods=["GET"])
def helpcmd():
    """Help page."""
    return render_template("help.html")


@bp.route("/min", methods=["GET"])
@login_required
def minview():
    """Mini view page."""
    return render_template("min.html")


@bp.route("/multiview", methods=["GET"])
@login_required
def multiview():
    """Camera multiview page."""
    multiviews = multiviews_db.query.all()
    return render_template("multiview.html", multiviews=multiviews)


@bp.route("/view", methods=["GET"])
@login_required
def view():
    """Stream camera preview."""
    id = request.args.get(  # pylint: disable=W0622
        "rHost", request.args.get("pHost", 0)
    )

    if (host := multiviews_db.query.get(int(id))) is None:
        abort(404)

    def _gather_img(url, delay):
        while True:
            uri = urllib.request.urlopen(url)
            file_contents = uri.read()
            yield (
                b"--PIderman\r\nContent-Type: image/jpeg\r\n"
                + f"Content-Type: {len(file_contents)}\r\n\r\n".encode()
                + file_contents
                + b"\r\n"
            )
            time.sleep(delay)

    return Response(
        _gather_img(host["url"], host["delay"]),
        mimetype="multipart/x-mixed-replace; boundary=PIderman",
    )


@bp.route("/pipan", methods=["GET"])
@login_required
def pipan():
    """Pipan page."""
    servo_cmd = "/dev/servoblaster"
    servo_data = f"{ca.config_folder}/{ca.config['SERVO_FILE']}"
    min_pan = 50
    max_pan = 250
    min_tilt = 80
    max_tilt = 220

    servo_data = {
        "x": 165,
        "y": 165,
        "left": "Xplus",
        "right": "Xminus",
        "up": "Yminus",
        "down": "Yplus",
        "XMax": 235,
        "XMin": 95,
        "XStep": 7,
        "YMax": 235,
        "YMin": 95,
        "YStep": 7,
    }

    if (
        (pan := request.args.get("pan"))
        and isinstance(pan, int | float)
        and (tilt := request.args.get("tilt"))
        and isinstance(tilt, int | float)
    ):
        pan = round(min_pan + ((max_pan - min_pan) / 200 * pan))
        tilt = round(min_tilt + ((max_tilt - min_tilt) / 200 * tilt))
        pipe = open("FIFO_pipan", mode="w", encoding="utf-8")
        pipe.write(f"servo {pan} {tilt} ")
        pipe.close()

        with open("pipan_bak.txt", mode="w", encoding="utf-8") as file:
            file.write(f"{pan} {tilt}")

    if (
        (red := request.args.get("red"))
        and isinstance(red, int | float)
        and (green := request.args.get("green"))
        and isinstance(green, int | float)
        and (blue := request.args.get("blue"))
        and isinstance(blue, int | float)
    ):
        pipe = open("FIFO_pipan", mode="w", encoding="utf-8")
        pipe.write(f"led {red} {green} {blue} ")
        pipe.close()

    if action := request.args.get("action"):
        try:
            with open(servo_data, encoding="utf-8") as file:
                servo_file = json.load(file)

                for key in servo_data:
                    if key in servo_file.keys():
                        servo_data[key] = servo_file[key]

        except Exception as error:  # pylint: disable=W0718
            write_log(f"error for load {servo_data} ({str(error)})")

        if action in servo_data:
            action = servo_data[action]

        servo = None
        match action:
            case "Xplus":
                servo_data["x"] += servo_data["XStep"]
                servo_data["x"] = min(servo_data["x"], servo_data["XMax"])
                servo = f"1={servo_data['x']}\n"
            case "Xminus":
                servo_data["x"] -= servo_data["XStep"]
                servo_data["x"] = max(servo_data["x"], servo_data["XMin"])
                servo = f"1={servo_data['x']}\n"
            case "Yminus":
                servo_data["y"] -= servo_data["YStep"]
                servo_data["y"] = max(servo_data["y"], servo_data["YMin"])
                servo = f"0={servo_data['y']}\n"
            case "Yplus":
                servo_data["y"] += servo_data["YStep"]
                servo_data["y"] = min(servo_data["y"], servo_data["YMax"])
                servo = f"0={servo_data['y']}\n"

        if servo:
            with open(servo_cmd, mode="w", encoding="utf-8") as file:
                file.write(servo)
                file.close()

        with open(servo_data, mode="w", encoding="utf-8") as file:
            json.dump(servo_data, file, sort_keys=True, indent=4)
            file.close()

    return status_mjpeg()


@bp.route("/mask", methods=["POST"])
@login_required
def image_mask():
    """Load image mask."""
    if "file" not in request.files:
        return make_response(jsonify({"message": "No file part"}), 422)
    file = request.files["file"]
    if file.filename == "":
        return make_response(jsonify({"message": "No selected file"}), 422)
    if file and allowed_file(file.filename):
        file_path = os.path.join(ca.config_folder, ca.config["MASK_FILENAME"])
        file.save(file_path)
        try:
            ca.raspiconfig.send(f"mi {file_path}")
        except RaspiConfigError as error:
            return make_response(jsonify({"message": error.args[0].strerror}), 422)
        return "", 204
    return make_response(jsonify({"message": "Format is incorrect"}), 422)
