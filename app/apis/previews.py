"""Api gallery."""
from typing import Any

from flask import current_app as ca
from flask import request, url_for
from flask_restx import Namespace, Resource, abort, fields

from ..blueprints.preview import draw_files, get_thumbnails, video_convert
from ..helpers.decorator import token_required
from ..helpers.filer import delete_mediafiles, lock_file, maintain_folders
from .models import forbidden, message

api = Namespace("previews")
api.add_model("Error", message)
api.add_model("Forbidden", forbidden)


class PathURI(fields.Raw):
    """Path URI."""

    def format(self, value):
        return url_for("static", filename=value)


files = api.model(
    "Files",
    {
        "id": fields.String(required=True, description="Id"),
        "file_name": fields.String(required=True, description="File name"),
        "file_type": fields.String(required=True, description="I/T/V"),
        "file_size": fields.Integer(required=True, description="Size"),
        # "file_icon": fields.String(required=False, description="Icon"),
        "file_datetime": fields.DateTime(required=False, description="DateTime"),
        "file_right": fields.Boolean(
            required=True, description="Read/Write right on disk"
        ),
        "real_file": fields.String(required=True, description="Original name"),
        "file_number": fields.String(required=True, description="Index"),
        "lapse_count": fields.Integer(
            required=False, description="image numbers of timelapse"
        ),
        "duration": fields.Float(
            required=False, description="image numbers of timelapse"
        ),
        "uri": PathURI(attribute="file_name", example="string"),
    },
)


@api.response(422, "Error", message)
@api.response(403, "Forbidden", forbidden)
@api.route("/previews")
class Previews(Resource):
    """Previews."""

    @token_required
    @api.marshal_list_with(files)
    @api.param("order", "Ordering thumbnail (True/False)")
    @api.response(200, "Success")
    def get(self):
        """Get all media files."""
        sort_order = request.args.get("sort_order", True) is True
        return thumbs(sort_order)

    @api.expect(
        api.model("Deletes", {"ids": fields.List(fields.String(description="id"))})
    )
    @token_required
    @api.response(204, "Action is successful")
    def delete(self):
        """Delete all media files."""
        maintain_folders(ca.raspiconfig.media_path, True, True)
        return "", 204


@api.route("/previews/<string:id>")
@api.response(422, "Error", message)
@api.response(403, "Forbidden", forbidden)
class Preview(Resource):
    """Preview."""

    @token_required
    @api.marshal_with(files)
    @api.response(200, "Success")
    def get(self, id):
        """Get file information."""
        return get_thumbinfo(id)

    @token_required
    @api.doc(description="Delete file")
    @api.response(204, "Action is successful")
    def delete(self, id):
        """Delete file."""
        if thumb := get_thumbinfo(id):
            delete_mediafiles(thumb["file_name"])
            maintain_folders(ca.raspiconfig.media_path, False, False)
            return "", 204
        abort(422, f"Thumb not found ({id})")


@api.route(
    "/previews/<string:id>/lock",
    endpoint="previews_lock",
    doc={"description": "Lock file"},
)
@api.route(
    "/previews/<string:id>/unlock",
    endpoint="previews_unlock",
    doc={"description": "Unlock file"},
)
@api.route(
    "/previews/<string:id>/convert",
    endpoint="previews_convert",
    doc={"description": "Convert timelapse file to mp4"},
)
@api.response(204, "Action is successful")
@api.response(422, "Error", message)
@api.response(403, "Forbidden", forbidden)
class Actions(Resource):
    """Actions."""

    @token_required
    def post(self, id):
        """Post action."""
        if request.endpoint in ["api.previews_lock", "api.previews_unlock"]:
            if thumb := get_thumbinfo(id):
                lock_file(thumb["file_name"], request.endpoint == "api.previews_lock")
                return "", 204
            abort(422, f"Thumb not found ({id})")
        if request.endpoint == "previews_convert":
            if thumb := get_thumbinfo(id):
                video_convert(thumb["file_name"])
                return "", 204
            abort(422, f"Thumb not found ({id})")


def thumbs(
    sort_order: bool = False,
    show_types: bool = True,
    time_filter: int = 1,
    time_filter_max: int = 8,
) -> dict[str, Any]:
    thumb_filenames = get_thumbnails(
        sort_order=sort_order,
        show_types=show_types,
        time_filter=time_filter,
        time_filter_max=time_filter_max,
    )
    return draw_files(thumb_filenames)


def get_thumbinfo(uid: str) -> dict[str, Any] | None:
    """Return filename."""
    for thumb in thumbs():
        if uid == thumb["id"]:
            return thumb
