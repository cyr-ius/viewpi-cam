"""Blueprint Main."""
import glob
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

from app.const import PRESETS
from app.helpers.decorator import auth_required, ViewPiCamException
from app.helpers.filer import send_pipe, write_log, delete_log

bp = Blueprint("main", __name__, template_folder="templates")


@bp.before_app_request
def before_app_request():
    # current_app.raspiconfig.refresh()
    g.raspiconfig = current_app.raspiconfig


@bp.route("/", methods=["GET", "POST"])
@auth_required
def index():
    write_log(f"Logged in user: {session['user_id']}:")
    write_log(f"UserLevel {session['user_level']}")
    display_mode = request.cookies.get("display_mode", "")
    if display_mode == "Full":
        allow_simple = "SimpleOff"
        toggle_button = "Simple"
        simple = 2
    elif display_mode == "Simple":
        allow_simple = "SimpleOff"
        toggle_button = "Full"
        simple = 1
    else:
        allow_simple = "SimpleOn"
        toggle_button = "Off"
        simple = 0

    stream_mode = request.cookies.get("stream_mode")
    if stream_mode == "MJPEG-Stream":
        stream_button = "Default-Stream"
        mjpegmode = 1
    else:
        stream_button = "MJPEG-Stream"
        mjpegmode = 0

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
        toggle_button=toggle_button,
        allow_simple=allow_simple,
        simple=simple,
        mjpegmode=mjpegmode,
        stream_button=stream_button,
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
                    yield file.read()
                    time.sleep(0.5)

    return Response(generate(log_file), mimetype="text/plain")


@bp.route("/debug", methods=["GET"])
def debugcmd():
    return render_template("debug.html", raspiconfig=current_app.raspiconfig.__dict__)


@bp.route("/help", methods=["GET"])
def helpcmd():
    return render_template("help.html")


@bp.route("/min", methods=["GET"])
@auth_required
def minview():
    return render_template("min.html")


@bp.route("/cam_pic", methods=["GET"])
@auth_required
def cam_pic():
    delay = float(request.args.get("pDelay", 1.0)) / 1000000
    cam_jpg = get_shm_cam()
    time.sleep(delay)
    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "image/jpeg"}
    return Response(cam_jpg, headers=headers)


@bp.route("/cam_picLatestTL", methods=["GET"])
@auth_required
def cam_pictl():
    media_path = current_app.raspiconfig.media_path
    list_of_files = filter(os.path.isfile, glob.glob(media_path + "*"))
    list_of_files = sorted(list_of_files, key=lambda x: os.stat(x).st_ctime)
    last_element = list_of_files[-1]
    last_jpeg = open(f"{media_path}/{last_element}", "rb").read()
    return Response(last_jpeg, headers={"Content-Type": "image/jpeg"})


@bp.route("/cam_get", methods=["GET"])
@auth_required
def cam_get():
    os.popen(f"touch {current_app.config.root_path}/status_mjpeg.txt")
    cam_jpg = get_shm_cam()
    return Response(cam_jpg, headers={"Content-Type": "image/jpeg"})


@bp.route("/cam_pic_new", methods=["GET"])
@auth_required
def cam_pic_new():
    delay = float(request.args.get("pDelay", 1.0)) / 100
    preview_path = current_app.raspiconfig.preview_path
    headers = {
        "Content-type": "multipart/x-mixed-replace; boundary=PIderman",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "close",
    }
    return Response(gather_img(preview_path, delay), headers=headers)


@bp.route("/system/<cmd>", methods=["GET"])
@auth_required
def sys_cmd(cmd):
    """Execute system command."""
    try:
        if cmd == "reboot":
            os.popen("sudo shutdown -r now")
        if cmd == "shutdown":
            os.popen("sudo shutdown -h now")
        if cmd == "settime" and (timestr := request.args.get("timestr")):
            os.popen(f'sudo date -s "{timestr}')
    except Exception as error:
        raise ViewPiCamException(f"System command failed ({error})") from error


@bp.route("/pipe_cmd", methods=["POST"])
@auth_required
def pipe_cmd():
    """Send command to control fifo."""
    if cmd := request.json.get("cmd"):
        msg = send_pipe(current_app.raspiconfig.control_file, cmd)
        return msg
    return {"type": "error", "message": "Command not found"}


@bp.route("/status_mjpeg", methods=["GET"])
@auth_required
def status_mjpeg():
    """Return status_mjpeg."""
    file_content = ""
    for _ in range(0, 30):
        with open(
            current_app.raspiconfig.status_file, mode="r", encoding="utf-8"
        ) as file:
            file_content = file.read()
            if file_content != request.args.get("last"):
                break
            time.sleep(0.1)
            file.close()
    os.popen(f"touch {current_app.raspiconfig.status_file}")
    return Response(file_content)


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


def get_shm_cam(preview_path=None):
    """Return binary data from cam.jpg."""
    preview_path = (
        current_app.raspiconfig.preview_path if preview_path is None else preview_path
    )
    if os.path.isfile(preview_path):
        return open(preview_path, "rb").read()


def gather_img(preview_path, delay=0.1):
    """Stream image."""
    while True:
        yield (
            b"--PIderman\r\nContent-Type: image/jpeg\r\n\r\n"
            + get_shm_cam(preview_path)
            + b"\r\n"
        )
        time.sleep(delay)
