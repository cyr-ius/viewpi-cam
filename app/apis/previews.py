"""Api gallery."""
from flask import current_app as ca
from flask import request, url_for
from flask_restx import Namespace, Resource, abort, fields

from ..blueprints.preview import get_thumbnails_id, thumbs, video_convert
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
        sort_order = int(
            1 if request.args.get("order", "true").lower() == "true" else 2
        )
        return thumbs(sort_order)

    @token_required
    @api.response(204, "Action is success")
    def delete(self):
        """Delete all media files."""
        maintain_folders(ca.raspiconfig.media_path, True, True)
        return "", 204


@api.route("/previews/<string:id>")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Preview(Resource):
    """Preview."""

    @token_required
    @api.marshal_with(files)
    @api.response(200, "Success")
    def get(self, id):
        """Get file information."""
        for thumb in thumbs():
            if thumb["id"] == id:
                return thumb

    @token_required
    @api.doc(description="Delete file")
    @api.response(204, "Action is success")
    def delete(self, id):
        """Delete file."""
        if thumb := get_thumbnails_id(id):
            delete_mediafiles(thumb["file_name"])
            maintain_folders(ca.raspiconfig.media_path, False, False)
            return "", 204
        abort(404, f"Thumb not found ({id})")


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
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Actions(Resource):
    """Actions."""

    @token_required
    def post(self, id: str):
        """Post action."""
        if request.endpoint in ["api.previews_lock", "api.previews_unlock"]:
            if thumb := get_thumbnails_id(id):
                lock_file(
                    thumb["file_name"],
                    thumb["id"],
                    request.endpoint == "api.previews_lock",
                )
                return "", 204
            abort(404, f"Thumb not found ({id})")
        if request.endpoint == "previews_convert":
            if thumb := get_thumbnails_id(id):
                video_convert(thumb["file_name"])
                return "", 204
            abort(404, f"Thumb not found ({id})")


@api.route(
    "/previews/<string:id>/convert",
    endpoint="previews_convert",
    doc={"description": "Convert timelapse file to mp4"},
)
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Convert(Resource):
    """Convert to mp4."""

    @token_required
    def post(self, id: str):
        """Coonvert timelapse."""
        if thumb := get_thumbnails_id(id):
            video_convert(thumb["file_name"])
            return "", 204
        abort(404, f"Thumb not found ({id})")
