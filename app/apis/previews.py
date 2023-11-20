"""Api gallery."""
from flask import current_app as ca
from flask import request
from flask_restx import Namespace, Resource, abort

from ..blueprints.preview import get_thumb, get_thumbnails, video_convert
from ..helpers.decorator import role_required, token_required
from ..helpers.filer import delete_mediafiles, lock_file, maintain_folders
from .models import files, forbidden, message

api = Namespace(
    "previews",
    path="/api",
    description="Gallery management",
    decorators=[token_required, role_required(["medium", "max"])],
)
api.add_model("Error", message)
api.add_model("Forbidden", forbidden)
api.add_model("Files", files)


@api.response(403, "Forbidden", forbidden)
@api.route("/previews")
class Previews(Resource):
    """Previews."""

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

    @api.response(204, "Action is success")
    def delete(self):
        """Delete all media files."""
        maintain_folders(ca.raspiconfig.media_path, True, True)
        return "", 204


@api.route("/previews/<string:id>")
@api.response(403, "Forbidden", forbidden)
class Preview(Resource):
    """Preview."""

    @api.marshal_with(files)
    def get(self, id: str):  # pylint: disable=W0622
        """Get file information."""
        return get_thumb(id)

    @api.doc(description="Delete file")
    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    @api.response(422, "Error", message)
    def delete(self, id: str):  # pylint: disable=W0622
        """Delete file."""
        if thumb := get_thumb(id):
            if id in ca.settings.get("lock_files", []):
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

    def post(self, id: str):  # pylint: disable=W0622
        """Coonvert timelapse."""
        if thumb := get_thumb(id):
            video_convert(thumb["file_name"])
            return "", 204
        abort(404, "Thumb not found")
