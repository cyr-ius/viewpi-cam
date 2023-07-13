import glob
import hashlib
import json
import os
import random
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
    url_for,
)

from ...const import (
    ATTR_DAWNSTARTMINUTES,
    ATTR_DAYENDMINUTES,
    ATTR_DAYMODE,
    ATTR_DAYSTARTMINUTES,
    ATTR_DUSKENDMINUTES,
    SCHEDULE_FIFOIN,
    ATTR_GMTOFFSET,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    SCHEDULE_RESET,
    ATTR_TIMES,
    SCHEDULE_FIFOOUT,
    PRESETS,
)
from viewpicam.helpers.decorator import auth_required
from viewpicam.helpers.filer import (
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
    list_folder_files,
    lock_file,
    maintain_folders,
    send_pipe,
    set_settings,
    write_log,
    gather_img,
    init_settings,
)
from viewpicam.helpers.schedule import (
    day_period,
    get_current_local_time,
    get_schedule_pid,
    get_sunrise,
    get_sunset,
    get_time_offset,
    start_schedule,
    stop_schedule,
)

main_bp = Blueprint("main", __name__, template_folder="templates")


@main_bp.before_app_request
def before_app_request():
    g.config = get_config()
    g.extra = {}
    extra_css_path = f"{current_app.config.root_path}/../static/extrastyles"
    g.extra["files"] = list_folder_files(extra_css_path, "css")
    if extrastyle := request.cookies.get("extrastyle", "Default.css"):
        g.extra["select"] = extrastyle


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    init = False
    error = ""
    if request.method == "POST":
        user = request.form.get("user")
        pwd = request.form.get("password")
        if pwd and (pwd2 := request.form.get("password_2")):
            if pwd != pwd2:
                error = "Password incorrect"
            elif user == get_settings("users").get(user):
                error = "User already exists"
            else:
                hashed = hashlib.pbkdf2_hmac(
                    "sha256", pwd.encode("utf-8"), "mymy".encode("utf-8"), 100000
                )
                set_settings({"users": {user: {"password": hashed.hex(), "rights": 4}}})
        else:
            if login := get_settings("users").get(user):
                hashed = hashlib.pbkdf2_hmac(
                    "sha256", pwd.encode("utf-8"), "mymy".encode("utf-8"), 100000
                )
                if hashed.hex() == login.get("password"):
                    session["valid_access"] = True
                    session["name"] = user
                    session["level"] = login.get("rights")
                    return redirect(url_for("main.index"))
            error = "User or password invalid."

    if get_settings("users") is None:
        init_settings()
        init = True

    return render_template("login.html", init=init, error=error)


@main_bp.route("/logout", methods=["GET", "POST"])
@auth_required
def logout():
    session.clear()
    return redirect(url_for("main.index"))


@main_bp.route("/", methods=["GET", "POST"])
@auth_required
def index():
    write_log(f"Logged in user: {session['name']}:")
    write_log(f"UserLevel {session['level']}")
    extrastyle = "Default"
    if request.method == "POST":
        extrastyle = request.form.get("extrastyle", "Default.css")

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

    response = make_response(
        render_template(
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
    )

    response.set_cookie("extrastyle", extrastyle)

    return response


@main_bp.route("/macros", methods=["GET", "POST"])
@auth_required
def macros():
    return render_template("macros.html", macros=current_app.config["MACROS"])


@main_bp.route("/gallery", methods=["GET", "POST"])
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


@main_bp.route("/log", methods=["GET", "POST"])
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


@main_bp.route("/schedule", methods=["GET", "POST"])
@auth_required
def schedule():
    bk_config = f"{current_app.config['FILE_SETTINGS']}.backup"
    schedule_pid = get_schedule_pid()
    if request.method == "POST" and (action := request.form.get("action")):
        match action:
            case "start":
                start_schedule()
                schedule_pid = get_schedule_pid()
            case "stop":
                stop_schedule(schedule_pid)
                schedule_pid = get_schedule_pid()
            case "save":
                write_log("Saved schedule settings")
                set_settings(request.form)
                write_log("Send Schedule reset")
                settings = get_settings()
                send_pipe(
                    settings.get(SCHEDULE_FIFOIN),
                    SCHEDULE_RESET,
                )
            case "backup":
                write_log("Backed up schedule settings")
                settings = get_settings()
                set_settings(settings, bk_config)
            case "restore":
                write_log("Restored up schedule settings")
                settings = get_settings(path_file=bk_config)
                set_settings(settings)

    settings = get_settings()

    offset = get_time_offset(settings.get(ATTR_GMTOFFSET))

    sunrise = get_sunrise(
        settings.get(ATTR_LATITUDE),
        settings.get(ATTR_LONGITUDE),
        offset,
    )
    sunset = get_sunset(
        settings.get(ATTR_LATITUDE),
        settings.get(ATTR_LONGITUDE),
        offset,
    )

    local_time = get_current_local_time(offset=offset)

    period = day_period(
        local_time=local_time,
        sunrise=sunrise,
        sunset=sunset,
        day_mode=settings.get(ATTR_DAYMODE),
        daw=settings.get(ATTR_DAWNSTARTMINUTES),
        day_start=settings.get(ATTR_DAYSTARTMINUTES),
        dusk=settings.get(ATTR_DUSKENDMINUTES),
        day_end=settings.get(ATTR_DAYENDMINUTES),
        times=settings.get(ATTR_TIMES),
    )

    return render_template(
        "schedule.html",
        settings=get_settings(),
        schedule_pid=schedule_pid,
        day_period=period,
        offset=offset,
        sunrise=sunrise.strftime("%H:%M"),
        sunset=sunset.strftime("%H:%M"),
        current_time=local_time.strftime("%H:%M"),
    )


@main_bp.route("/help", methods=["GET"])
@auth_required
def help():
    return render_template("help.html")


@main_bp.route("/settings", methods=["GET", "POST"])
@auth_required
def settings():
    if request.method == "POST":
        settings = {
            "servo": int(request.form.get("servo", 0)),
            "pipan": int(request.form.get("pipan", 0)),
            "pilight": int(request.form.get("pilight", 0)),
            "upreset": request.form.get("upreset", "v2"),
        }

        if request.form.get("token") == "generate":
            token = random.getrandbits(256)
            settings.update({"token": f"B{token}"})

        if request.form.get("token") == "reset":
            settings.update({"token": ""})

        if names := request.form.getlist("name"):
            macro = request.form.getlist("macro")
            sclass = request.form.getlist("class")
            style = request.form.getlist("style")
            other = request.form.getlist("other")
            pos = 0
            user_buttons = []
            for name in names:
                if name != "":
                    user_buttons.append(
                        {
                            "name": name,
                            "macro": macro[pos],
                            "class": sclass[pos],
                            "style": style[pos],
                            "other": other[pos],
                        }
                    )
                pos += 1
            settings.update({"user_buttons": user_buttons})

        users_settings = {}
        if users := request.form.getlist("user"):
            rights = request.form.getlist("rights")
            pwds = request.form.getlist("password")
            pos = 0
            for user in users:
                if user:
                    if pwds[pos] != "":
                        hashed = hashlib.pbkdf2_hmac(
                            "sha256",
                            pwds[pos].encode("utf-8"),
                            "mymy".encode("utf-8"),
                            100000,
                        )
                        password = hashed.hex()
                    else:
                        password = get_settings("users.user.password")

                    users_settings.update(
                        {user: {"password": password, "rights": int(rights[pos])}}
                    )
                pos += 1
            settings.update({"users": users_settings})

        set_settings(settings)
        return get_settings()

    return render_template("settings.html", settings=get_settings())


@main_bp.route("/preview", methods=["POST"])
@auth_required
def preview():
    return render_template("gallery.html")


@main_bp.route("/min", methods=["GET"])
@auth_required
def minview():
    return render_template("min.html")


@main_bp.route("/cam_pic", methods=["GET"])
@auth_required
def cam_pic():
    pDelay = float(request.args.get("pDelay", 1.0)) / 1000000
    cam_jpg = get_shm_cam()
    time.sleep(pDelay)
    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "image/jpeg"}
    return Response(cam_jpg, headers=headers)


@main_bp.route("/cam_picLatestTL", methods=["GET"])
@auth_required
def cam_pictl():
    media = current_app.config["MEDIA"]
    media_folder = f"{current_app.config.root_path}/{media}"
    list_of_files = filter(os.path.isfile, glob.glob(media_folder + "*"))
    list_of_files = sorted(list_of_files, key=lambda x: os.stat(x).st_ctime)
    last_element = list_of_files[-1]
    last_jpeg = open(f"{media_folder}/{last_element}", "rb").read()
    return Response(last_jpeg, headers={"Content-Type": "image/jpeg"})


@main_bp.route("/cam_get", methods=["GET"])
@auth_required
def cam_get():
    os.popen(f"touch {current_app.config.root_path}/status_mjpeg.txt")
    cam_jpg = get_shm_cam()
    return Response(cam_jpg, headers={"Content-Type": "image/jpeg"})


@main_bp.route("/cam_pic_new", methods=["GET"])
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


@main_bp.route("/system/<cmd>", methods=["GET"])
@auth_required
def sys_cmd(cmd):
    if cmd == "reboot":
        os.popen("sudo shutdown -r now")
    if cmd == "shutdown":
        os.popen("sudo shutdown -h now")
    if cmd == "settime" and (timestr := request.args.get("timestr")):
        os.popen(f'sudo date -s "{timestr}')

    return redirect(request.url)


@main_bp.route("/cmd_pipe/<cmd>", methods=["GET"])
@auth_required
def pipe_cmd(cmd):
    settings = get_settings()
    send_pipe(settings[SCHEDULE_FIFOOUT], cmd)
    return {}


@main_bp.route("/status_mjpeg", methods=["GET"])
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


@main_bp.route("/pipan", methods=["GET"])
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
