"""Api gallery."""
from flask import current_app as ca
from flask import request, url_for
from flask_restx import Namespace, Resource, abort, fields

from ..blueprints.preview import get_thumb, get_thumbnails, video_convert
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
        "file_lock": fields.Boolean(
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


@api.response(403, "Forbidden", forbidden)
@api.route("/previews")
class Previews(Resource):
    """Previews."""

    @token_required
    @api.marshal_list_with(files)
    @api.param("order", "Ordering thumbnail [desc|asc]")
    @api.param("show_types", "Show types [both|image|video]")
    @api.param("time_filter", "Time filter")
    def get(self):
        """Get all media files."""
        return get_thumbnails(
            sort_order=request.args.get("sort_order", "asc").lower(),
            show_types=request.args.get("show_types", "both").lower(),
            time_filter=int(request.args.get("time_filter", 1)),
        )

    @token_required
    @api.response(204, "Action is success")
    def delete(self):
        """Delete all media files."""
        maintain_folders(ca.raspiconfig.media_path, True, True)
        return "", 204


@api.route("/previews/<string:id>")
@api.response(403, "Forbidden", forbidden)
class Preview(Resource):
    """Preview."""

    @token_required
    @api.marshal_with(files)
    def get(self, id: str):  # pylint: disable=W0622
        """Get file information."""
        return get_thumb(id)

    @token_required
    @api.doc(description="Delete file")
    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    @api.response(422, "Error", message)
    def delete(self, id: str):  # pylint: disable=W0622
        """Delete file."""
        if thumb := get_thumb(id):
            if id in ca.settings.lock_files:
                abort(422, f"Protected thumbnail ({id})")
            delete_mediafiles(thumb["file_name"])
            maintain_folders(ca.raspiconfig.media_path, False, False)
            return "", 204
        abort(404, "Thumb not found")


@api.route("/previews/<string:id>/lock")
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Lock(Resource):
    """Lock file."""

    @token_required
    def post(self, id: str):  # pylint: disable=W0622
        """Lock."""
        if thumb := get_thumb(id):
            lock_file(
                thumb["file_name"],
                thumb["id"],
                True,
            )
            return "", 204
        abort(404, f"Thumb not found ({id})")


@api.route("/previews/<string:id>/unlock")
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Unlock(Resource):
    """Unock file."""

    @token_required
    def post(self, id: str):  # pylint: disable=W0622
        """Unlock."""
        if thumb := get_thumb(id):
            lock_file(
                thumb["file_name"],
                thumb["id"],
                request.endpoint == "api.previews_lock",
            )
            return "", 204
        abort(404, f"Thumb not found ({id})")


@api.route("/previews/<string:id>/convert")
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Convert(Resource):
    """Convert timelapse file to mp4."""

    @token_required
    def post(self, id: str):  # pylint: disable=W0622
        """Coonvert timelapse."""
        if thumb := get_thumb(id):
            video_convert(thumb["file_name"])
            return "", 204
        abort(404, "Thumb not found")
