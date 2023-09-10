"""Blueprint Main."""
import os
import time

from flask import (
    Blueprint,
    Response,
    current_app,
    g,
    render_template,
    request,
    send_file,
    session,
    json,
)

from ..const import PRESETS
from ..helpers.decorator import auth_required, ViewPiCamException
from ..helpers.filer import send_pipe, write_log, delete_log
from .camera import status_mjpeg

bp = Blueprint("main", __name__, template_folder="templates")


@bp.before_app_request
def before_app_request():
    g.motion_pipe = current_app.raspiconfig.motion_pipe
    g.control_file = current_app.raspiconfig.control_file
    g.macros = {
        item: getattr(current_app.raspiconfig, item)
        for item in current_app.config["MACROS"]
    }
    g.motion_external = current_app.raspiconfig.motion_external


@bp.route("/", methods=["GET"])
@auth_required
def index():
    write_log(f"Logged in user: {session['user_id']}:")
    write_log(f"UserLevel {session['user_level']}")
    display_mode = request.cookies.get("display_mode", "On")
    mjpegmode = int(request.cookies.get("mjpegmode", 0))

    mode = 0
    cam_pos = None
    pipan_file = current_app.config["PIPAN_FILE"]
    if os.path.isfile(pipan_file):
        mode = 1
        with open(pipan_file, mode="r", encoding="utf-8") as file:
            pipan_sck = file.read().decode("utf-8")
            cam_pos = pipan_sck.split(" ")
            file.close()
    if current_app.settings.servo:
        mode = 2

    return render_template(
        "main.html",
        mode=mode,
        cam_pos=cam_pos,
        user_buttons=current_app.settings.ubuttons,
        raspiconfig=current_app.raspiconfig,
        display_mode=display_mode,
        mjpegmode=mjpegmode,
        preset=current_app.settings.upreset,
        presets=PRESETS,
    )


@bp.route("/log", methods=["GET", "POST"])
@auth_required
def log():
    if request.method == "POST" and (action := request.json.get("action")):
        match action:
            case "downloadlog":
                filename = current_app.raspiconfig.log_file
                return send_file(filename, as_attachment=True)
            case "clearlog":
                filename = current_app.raspiconfig.log_file
                delete_log(1)

    log_file = current_app.raspiconfig.log_file
    logs = []
    if os.path.isfile(log_file):
        with open(log_file, mode="r", encoding="utf-8") as file:
            lines = file.readlines()
            lines.sort(reverse=True)
            for line in lines:
                logs.append(line.replace("\n", ""))

    return render_template("logs.html", log=logs)


@bp.route("/streamlog", methods=["GET"])
@auth_required
def streamlog():
    log_file = current_app.raspiconfig.log_file

    def generate(log_file):
        if os.path.isfile(log_file):
            with open(log_file, mode="r", encoding="utf-8") as file:
                while True:
                    yield f"data: {file.read()}\n\n"
                    time.sleep(0.5)

    return Response(generate(log_file), mimetype="text/event-stream")


@bp.route("/debug", methods=["GET"])
@auth_required
def debugcmd():
    return render_template("debug.html", raspiconfig=current_app.raspiconfig.__dict__)


@bp.route("/help", methods=["GET"])
def helpcmd():
    return render_template("help.html")


@bp.route("/min", methods=["GET"])
@auth_required
def minview():
    return render_template("min.html")


@bp.route("/system/<cmd>", methods=["GET"])
@auth_required
def sys_cmd(cmd):
    """Execute system command."""
    try:
        if cmd == "restart":
            os.popen("echo b > /proc/sysrq-trigger")
        if cmd == "shutdown":
            os.popen("echo o > /proc/sysrq-trigger")
        if cmd == "restart_app":
            os.popen("killall gunicorn")
        if cmd == "settime" and (timestr := request.args.get("timestr")):
            os.popen(f'sudo date -s "{timestr}')
    except Exception as error:
        raise ViewPiCamException(f"System command failed ({error})") from error


@bp.route("/command", methods=["POST"])
@auth_required
def send_cmd():
    """Send command to control fifo."""
    if (cmd := request.json.get("cmd")) and (values := request.json.get("values", [])):
        values = " ".join(values)
        full_cmd = f"{cmd} {values}"
        msg = send_pipe(current_app.raspiconfig.control_file, full_cmd)
        return msg
    return {
        "type": "error",
        "message": "Command not found, {'cmd':'xxx', values:['xx','yy']}",
    }


@bp.route("/pipan", methods=["GET"])
@auth_required
def pipan():
    servo_cmd = "/dev/servoblaster"
    servo_data = current_app.config["SERVO_FILE"]
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
            with open(servo_data, mode="r", encoding="utf-8") as file:
                servo_file = json.load(file)

                for key in servo_data:
                    if key in servo_file.keys():
                        servo_data[key] = servo_file[key]

        except Exception as error:  # pylint: disable=W0718
            write_log(f"error for load {servo_data} ({str(error)})")

        if action in servo_data:
            action = servo_data[action]

        servo = None
        match (action):
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
