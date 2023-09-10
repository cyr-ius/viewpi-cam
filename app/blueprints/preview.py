"""Blueprint preview."""
import os
import shutil
import time
import zipfile
from datetime import datetime as dt
from io import BytesIO

from flask import (
    Blueprint,
    current_app,
    make_response,
    render_template,
    request,
    send_file,
)

from ..helpers.decorator import auth_required
from ..helpers.filer import (
    data_file_ext,
    data_filename,
    delete_mediafiles,
    disk_usage,
    find_lapse_files,
    get_file_index,
    get_file_size,
    get_file_type,
    list_folder_files,
    write_log,
)

bp = Blueprint("preview", __name__, template_folder="templates", url_prefix="/preview")


@bp.route("/", methods=["GET", "POST"])
@auth_required
def index():
    """Index page."""
    media_path = current_app.raspiconfig.media_path
    time_filter_max = 8
    select_all = ""

    preview_size = int(request.cookies.get("preview_size", 640))
    thumb_size = int(request.cookies.get("thumb_size", 96))
    sort_order = int(request.cookies.get("sort_order", 1))
    show_types = int(request.cookies.get("show_types", 1))
    time_filter = int(request.cookies.get("time_filter", 1))
    preview_file = request.args.get("preview", "")

    if request.method == "POST":
        time_filter = int(request.json.get("time_filter", time_filter))
        sort_order = int(request.json.get("sort_order", sort_order))
        show_types = int(request.json.get("show_types", show_types))

        if action := request.json.get("action"):
            match action:
                case "delete":
                    if (filename := request.json.get("filename")) and check_media_path(
                        filename
                    ):
                        delete_mediafiles(filename)
                        maintain_folders(media_path, False, False)
                        return {"message": "Delete successful"}
                case "download":
                    if (filename := request.json.get("filename")) and check_media_path(
                        filename
                    ):
                        if get_file_type(filename) != "t":
                            dx_file = data_filename(filename)
                            if data_file_ext(filename) == "jpg":
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
                            return get_zip([filename])
                case "deleteAll":
                    maintain_folders(media_path, True, True)
                    return {"message": "Delete successful"}
                case "selectAll":
                    select_all = "checked"
                case "selectNone":
                    select_all = ""
                case "deleteSel":
                    check_list = request.json.get("check_list", [])
                    if isinstance(check_list, str):
                        check_list = [request.json["check_list"]]
                    for item in check_list:
                        if check_media_path(item):
                            delete_mediafiles(item)
                    maintain_folders(media_path, False, False)
                    return {"message": "Delete successful"}
                case "lockSel":
                    check_list = request.json.get("check_list", [])
                    if isinstance(check_list, str):
                        check_list = [request.json["check_list"]]
                    for item in check_list:
                        if check_media_path(item):
                            lock_file(item, True)
                    return {"message": "Lock successful"}
                case "unlockSel":
                    check_list = request.json.get("check_list", [])
                    if isinstance(check_list, str):
                        check_list = [request.json["check_list"]]
                    for item in check_list:
                        if check_media_path(item):
                            lock_file(item, False)
                    return {"message": "Unlock successful"}
                case "updateSizeOrder":
                    if preview_size := request.json.get("preview_size"):
                        preview_size = max(int(preview_size), 100)
                        preview_size = min(int(preview_size), 1920)
                    if thumb_size := request.json.get("thumb_size"):
                        thumb_size = max(int(thumb_size), 32)
                        thumb_size = min(int(thumb_size), 320)
                case "zipSel":
                    check_list = request.json.get("check_list", [])
                    if isinstance(check_list, str):
                        check_list = [request.json["check_list"]]
                    if check_list:
                        return get_zip(check_list)
                case "convert":
                    video_convert(request.json.get("filename"))

    thumb_filenames = get_thumbnails(
        sort_order=sort_order,
        show_types=show_types,
        time_filter=time_filter,
        time_filter_max=time_filter_max,
    )

    thumbnails = draw_files(thumb_filenames)

    response = make_response(
        render_template(
            "preview.html",
            raspiconfig=current_app.raspiconfig,
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


# function to lock or unlock all files associated with a thumb name
def lock_file(filename: str, lock: bool):
    """Lock file (remove w via chmod)."""
    media_path = current_app.raspiconfig.media_path
    if lock == 1:
        attr = "0444"
    else:
        attr = "0644"
    file_type = get_file_type(filename)
    if file_type == "t":
        #  For time lapse lock all from this batch
        files = find_lapse_files(filename)
        for file in files:
            os.popen(f"chmod {attr} {file}")
    else:
        thumb_file = data_filename(filename)
        if os.path.isfile(f"{media_path}/{thumb_file}"):
            os.popen(f"chmod {attr} {media_path}/{thumb_file}")
        if file_type == "v" and os.path.isfile(f"{media_path}/{thumb_file}.dat"):
            os.popen(f"chmod {attr} {media_path}/{thumb_file}.dat")
        if file_type == "v" and os.path.isfile(f"{media_path}/{thumb_file}.h264"):
            os.popen(f"chmod {attr} {media_path}/{thumb_file}.h264")

    os.popen(f"chmod {attr} {media_path}/{filename}")


def get_zip(files: list):
    """Zip files."""
    media_path = current_app.raspiconfig.media_path
    date_str = dt.now().strftime("%Y%m%d_%H%M%S")
    zipname = f"cam_{date_str}.zip"

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, "a") as zip_file:
        for file in files:
            file_name = data_filename(file)
            try:
                data = zipfile.ZipInfo(file_name)
                data.date_time = time.localtime(time.time())[:6]
                data.compress_type = zipfile.ZIP_DEFLATED
                # zf.writestr(data, f"{media_path}/{data_filename(individualFile)}")
                zip_file.write(
                    f"{media_path}/{file_name}", file_name, data.compress_type
                )
            except FileNotFoundError:
                continue
    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zipname,
    )


def video_convert(filename: str):
    media_path = current_app.raspiconfig.media_path

    if check_media_path(filename):
        file_type = get_file_type(filename)
        file_index = get_file_index(filename)

        if file_type == "t" and isinstance(int(file_index), int):
            thumb_files = find_lapse_files(filename)
            tmp = f"{media_path}/{file_type}{file_index}"
            if not os.path.isdir(tmp):
                os.makedirs(tmp, 0o744, True)

            i = 0
            for thumb in thumb_files:
                os.symlink(thumb, f"{tmp}/i_{i:05d}.jpg")
                i += 1

            i = 0
            video_file = f"{data_filename(filename)[:-4]}.mp4"
            cmd = current_app.config["CONVERT_CMD"]
            rst = cmd.replace(f"i_{i:05d}", f"tmp/i_{i:05d}")
            cmd = f"({rst} {media_path}/{video_file}; rm -rf {tmp};) >/dev/null 2>&1 &"
            write_log(f"start lapse convert: {cmd}")
            os.popen(cmd)
            shutil.copy(
                src=f"{media_path}/{filename}",
                dst=f"{media_path}/{video_file}.v{file_index}{current_app.config['THUMBNAIL_EXT']}",
            )
            write_log("Convert finished")


def maintain_folders(path, delete_main_files, delete_sub_files, root: bool = True):
    """Sanatize media folders."""
    empty = True
    for folder in list_folder_files(path):
        if os.path.isdir(folder):
            if not maintain_folders(folder, delete_main_files, delete_sub_files, False):
                empty = False
        else:
            if (delete_sub_files and not root) or (delete_main_files and root):
                os.remove(folder)
            else:
                empty = False
    return empty and not root and os.rmdir(path)


def get_thumbnails(sort_order, show_types, time_filter, time_filter_max):
    """Return files."""
    media_path = current_app.raspiconfig.media_path
    files = list_folder_files(media_path)
    thumbnails = {}
    for file in files:
        file_timestamp = os.path.getmtime(f"{media_path}/{file}")
        if time_filter == 1:
            include = True
        else:
            time_delta = dt.now().timestamp() - file_timestamp
            if time_filter == time_filter_max:
                include = time_delta >= (86400 * (time_filter - 2))
            else:
                include = time_delta >= (86400 * (time_filter - 2)) and (
                    time_delta < ((time_filter - 1) * 86400)
                )
        if include:
            file_type = get_file_type(file)
            if (
                show_types == 1
                or (  # noqa: W503
                    show_types == 2 and (file_type == "i" or file_type == "t")
                )
                or (show_types == 3 and file_type == "v")  # noqa: W503
            ):
                thumbnails[file] = f"{file_type}_{file_timestamp}"

    if sort_order == 1:
        thumbnails = dict(sorted(thumbnails.items()))
    else:
        thumbnails = dict(sorted(thumbnails.items(), reverse=True))

    return list(thumbnails.keys())


def draw_files(filesnames: list):
    """Return thumbnails and extra informations."""
    media_path = current_app.raspiconfig.media_path
    thumbnails = []
    for file in filesnames:
        file_type = get_file_type(file)
        real_file = data_filename(file)
        f_number = get_file_index(file)
        lapse_count = 0
        match file_type:
            case "v":
                file_icon = "bi-camera-reels"
            case "t":
                file_icon = "bi-images"
                lapse_count = len(find_lapse_files(file))
            case "i":
                file_icon = "bi-camera"
            case _:
                file_icon = "bi-camera"
        duration = 0
        if os.path.isfile(f"{media_path}/{real_file}"):
            file_size = round(get_file_size(f"{media_path}/{real_file}") / 1024)
            file_timestamp = os.path.getmtime(f"{media_path}/{real_file}")
            try:
                file_right = os.access(f"{media_path}/{real_file}", os.W_OK)
                current_app.logger.debug(f"File Right {file_right}")
            except UnboundLocalError:
                file_right = 0
            if file_type == "v":
                duration = os.path.getmtime(f"{media_path}/{file}") - file_timestamp
        else:
            file_size = 0
            file_timestamp = os.path.getmtime(f"{media_path}/{file}")

        if file_type:
            file_datetime = dt.fromtimestamp(file_timestamp)
            thumbnails.append(
                {
                    "file_name": file,
                    "file_type": file_type,
                    "file_size": file_size,
                    "file_icon": file_icon,
                    "file_datetime": file_datetime,
                    "file_right": file_right,
                    "real_file": real_file,
                    "file_number": f_number,
                    "lapse_count": lapse_count,
                    "duration": round(duration),
                }
            )

    current_app.logger.debug(f"Thumbnails: {thumbnails}")
    return thumbnails


def check_media_path(filename):
    """Check file if existe media path."""
    media_path = current_app.raspiconfig.media_path
    if os.path.realpath(
        os.path.dirname(f"{media_path}/{filename}")
    ) == os.path.realpath(media_path):
        return os.path.isfile(f"{media_path}/{filename}")
