import glob
import json
import os
import time

from flask import (
    Blueprint,
    Response,
    current_app,
    g,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    session,
)

from ...const import SCHEDULE_FIFOOUT, PRESETS
from app.helpers.decorator import auth_required
from app.helpers.filer import (
    check_media_path,
    data_file_ext,
    data_filename,
    delete_mediafiles,
    disk_usage,
    draw_files,
    file_exists,
    file_get_content,
    file_set_content,
    get_file_type,
    get_log,
    get_config,
    get_settings,
    get_shm_cam,
    get_thumbnails,
    get_zip,
    lock_file,
    maintain_folders,
    send_pipe,
    write_log,
    gather_img,
)

bp = Blueprint("main", __name__, template_folder="templates")


@bp.before_app_request
def before_app_request():
    g.config = get_config()


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
    if file_exists(pipan_file):
        pipan = file_get_content(pipan_file)
        cam_pos = pipan.split(" ")
        mode = 1
    if get_settings("servo"):
        mode = 2

    user_buttons = get_settings("user_buttons", [])
    preset = get_settings("preset", "v2")

    return render_template(
        "main.html",
        mode=mode,
        cam_pos=cam_pos,
        user_buttons=user_buttons,
        toggle_button=toggle_button,
        allow_simple=allow_simple,
        simple=simple,
        mjpegmode=mjpegmode,
        stream_button=stream_button,
        preset=preset,
        presets=PRESETS,
    )


@bp.route("/macros", methods=["GET", "POST"])
@auth_required
def macros():
    return render_template("macros.html", macros=current_app.config["MACROS"])


@bp.route("/gallery", methods=["GET", "POST"])
@auth_required
def gallery():
    media_path = get_config("media_path")
    select_all = ""

    preview_size = (
        int(preview_size)
        if (preview_size := request.cookies.get("preview_size"))
        else 640
    )
    thumb_size = (
        int(thumb_size) if (thumb_size := request.cookies.get("thumb_size")) else 96
    )
    sort_order = (
        int(sort_order) if (sort_order := request.cookies.get("sort_order")) else 1
    )
    show_types = (
        int(show_types) if (show_types := request.cookies.get("show_types")) else 1
    )
    time_filter = (
        int(time_filter) if (time_filter := request.cookies.get("time_filter")) else 1
    )

    time_filter_max = 8
    preview_file = ""
    if request.method == "GET" and (thumb_file := request.args.get("preview")):
        preview_file = thumb_file

    if request.method == "POST":
        if time_filter := request.form.get("time_filter"):
            time_filter = int(time_filter)

        if sort_order := request.form.get("sort_order"):
            sort_order = int(sort_order)

        if show_types := request.form.get("show_types"):
            show_types = int(show_types)

        if (delete1 := request.form.get("delete1")) and check_media_path(delete1):
            delete_mediafiles(delete1)
            maintain_folders(media_path, False, False)

        if (download1 := request.form.get("download1")) and check_media_path(download1):
            if get_file_type(download1) != "t":
                dx_file = data_filename(download1)
                if data_file_ext(download1) == "jpg":
                    mimetype = "image/jpeg"
                else:
                    mimetype = "video/mp4"

                return send_file(
                    f"{media_path}/{dx_file}",
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=dx_file,
                )
            else:
                return get_zip([download1])

        if action := request.form.get("action"):
            match action:
                case "deleteAll":
                    maintain_folders(media_path, True, True)
                case "selectAll":
                    select_all = "checked"
                case "selectNone":
                    select_all = ""
                case "deleteSel":
                    for item in request.form.getlist("check_list"):
                        if check_media_path(item):
                            delete_mediafiles(item)
                    maintain_folders(media_path, False, False)
                case "lockSel":
                    for item in request.form.getlist("check_list"):
                        if check_media_path(item):
                            lock_file(item, True)
                case "unlockSel":
                    for item in request.form.getlist("check_list"):
                        if check_media_path(item):
                            lock_file(item, False)
                case "updateSizeOrder":
                    if preview_size := request.form.get("preview_size"):
                        preview_size = max(int(preview_size), 100)
                        preview_size = min(int(preview_size), 1920)
                    if thumb_size := request.form.get("thumb_size"):
                        thumb_size = max(int(thumb_size), 32)
                        thumb_size = min(int(thumb_size), 320)
                case "zipSel":
                    if check_list := request.form.getlist("check_list"):
                        return get_zip(check_list)

    thumb_filenames = get_thumbnails(
        sort_order=sort_order,
        show_types=show_types,
        time_filter=time_filter,
        time_filter_max=time_filter_max,
    )

    thumbnails = draw_files(thumb_filenames)

    response = make_response(
        render_template(
            "gallery.html",
            disk_usage=disk_usage(),
            preview_size=preview_size,
            thumb_size=thumb_size,
            sort_order=sort_order,
            show_types=show_types,
            time_filter=time_filter,
            time_filter_max=time_filter_max,
            preview_file=preview_file,
            thumbnails=thumbnails,
            select_all=select_all,
        )
    )

    if request.method == "POST":
        response.set_cookie("time_filter", str(time_filter))
        response.set_cookie("sort_order", str(sort_order))
        response.set_cookie("show_types", str(show_types))
        response.set_cookie("preview_size", str(preview_size))
        response.set_cookie("thumb_size", str(thumb_size))

    return response


@bp.route("/log", methods=["GET", "POST"])
@auth_required
def log():
    if request.method == "POST" and (action := request.form.get("action")):
        match action:
            case "downloadlog":
                filename = get_config("log_file")
                return send_file(filename, as_attachment=True)
            case "clearlog":
                filename = get_config("log_file")
                os.remove(filename)

    return render_template("logs.html", log=get_log())


@bp.route("/help", methods=["GET"])
def help():
    return render_template("help.html")


@bp.route("/min", methods=["GET"])
@auth_required
def minview():
    return render_template("min.html")


@bp.route("/cam_pic", methods=["GET"])
@auth_required
def cam_pic():
    pDelay = float(request.args.get("pDelay", 1.0)) / 1000000
    cam_jpg = get_shm_cam()
    time.sleep(pDelay)
    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "image/jpeg"}
    return Response(cam_jpg, headers=headers)


@bp.route("/cam_picLatestTL", methods=["GET"])
@auth_required
def cam_pictl():
    media_path = get_config("media_path")
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
    pDelay = float(request.args.get("pDelay", 1.0)) / 100
    headers = {
        "Content-type": "multipart/x-mixed-replace; boundary=PIderman",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "close",
    }
    return Response(gather_img(pDelay), headers=headers)


@bp.route("/system/<cmd>", methods=["GET"])
@auth_required
def sys_cmd(cmd):
    if cmd == "reboot":
        os.popen("sudo shutdown -r now")
    if cmd == "shutdown":
        os.popen("sudo shutdown -h now")
    if cmd == "settime" and (timestr := request.args.get("timestr")):
        os.popen(f'sudo date -s "{timestr}')

    return redirect(request.url)


@bp.route("/cmd_pipe/<cmd>", methods=["GET"])
@auth_required
def pipe_cmd(cmd):
    send_pipe(get_settings(SCHEDULE_FIFOOUT), cmd)
    return {}


@bp.route("/status_mjpeg", methods=["GET"])
@auth_required
def status_mjpeg():
    file_content = ""
    for i in range(0, 30):
        file_content = file_get_content(get_config("status_file"))
        if file_content != request.args.get("last"):
            break
        time.sleep(0.1)
    os.popen(f"touch {get_config('status_file')}")
    return Response(file_content)


@bp.route("/pipan", methods=["GET"])
@auth_required
def pipan():
    SERVO_CMD = "/dev/servoblaster"
    SERVO_DATA = current_app.config["SERVO_FILE"]
    min_pan = 50
    max_pan = 250
    min_tilt = 80
    max_tilt = 220

    servoData = {
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
        and isinstance(pan, int | float)  # noqa:W503
        and (tilt := request.args.get("tilt"))  # noqa:W503
        and isinstance(tilt, int | float)  # noqa:W503
    ):
        pan = round(min_pan + ((max_pan - min_pan) / 200 * pan))
        tilt = round(min_tilt + ((max_tilt - min_tilt) / 200 * tilt))
        pipe = open("FIFO_pipan", "w")
        pipe.write(f"servo {pan} {tilt} ")
        pipe.close()
        file_set_content("pipan_bak.txt", f"{pan} {tilt}")

    if (
        (red := request.args.get("red"))
        and isinstance(red, int | float)  # noqa:W503
        and (green := request.args.get("green"))  # noqa:W503
        and isinstance(green, int | float)  # noqa:W503
        and (blue := request.args.get("blue"))  # noqa:W503
        and isinstance(blue, int | float)  # noqa:W503
    ):
        pipe = open("FIFO_pipan", "w")
        pipe.write(f"led {red} {green} {blue} ")
        pipe.close()

    if action := request.args.get("action"):
        try:
            input = json.loads(file_get_content(SERVO_DATA))
            for key, value in servoData:
                if key in input.keys():
                    servoData[key] = input[key]
        except Exception as e:
            write_log(f"error for load {SERVO_DATA} ({str(e)})")

        if action in servoData.keys():
            action = servoData[action]

        servo = None
        match (action):
            case "Xplus":
                servoData["x"] += servoData["XStep"]
                servoData["x"] = min(servoData["x"], servoData["XMax"])
                servo = f"1={servoData['x']}\n"
            case "Xminus":
                servoData["x"] -= servoData["XStep"]
                servoData["x"] = max(servoData["x"], servoData["XMin"])
                servo = f"1={servoData['x']}\n"
            case "Yminus":
                servoData["y"] -= servoData["YStep"]
                servoData["y"] = max(servoData["y"], servoData["YMin"])
                servo = f"0={servoData['y']}\n"
            case "Yplus":
                servoData["y"] += servoData["YStep"]
                servoData["y"] = min(servoData["y"], servoData["YMax"])
                servo = f"0={servoData['y']}\n"

        if servo:
            fs = open(SERVO_CMD, "w")
            fs.write(servo)
            fs.close()

        file_set_content(SERVO_DATA, json.dumps(servoData))

    return status_mjpeg()
