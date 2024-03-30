"""Api gallery."""

from flask import current_app as ca
from flask import request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..blueprints.preview import get_thumbs, video_convert
from ..helpers.decorator import role_required
from ..helpers.filer import delete_mediafiles, maintain_folders
from ..models import Files as files_db
from ..models import db
from .models import deletes, files, message

api = Namespace(
    "previews",
    description="Gallery management",
    decorators=[role_required(["medium", "max"]), login_required],
)
api.add_model("Files", files)
api.add_model("Deletes", deletes)


@api.response(401, "Unauthorized", message)
@api.route("/")
class Thumbs(Resource):
    """Previews."""

    @api.marshal_list_with(files)
    @api.param("order", "Ordering thumbnail [desc|asc]")
    @api.param("show_types", "Show types [both|image|video]")
    @api.param("time_filter", "Time filter")
    def get(self):
        """Get all media files."""
        sort_order = request.args.get("sort_order", "asc").lower()
        show_types = request.args.get("show_types", "both").lower()
        time_filter = int(request.args.get("time_filter", 1))

        return get_thumbs(sort_order, show_types, time_filter)

    @api.doc(description="Delete  all files or files list")
    @api.expect(deletes)
    def delete(self):
        """Delete all media files."""
        deleted_ids = []
        if self.api.payload:
            for id in self.api.payload.get("thumb_id", []):
                if thumb := files_db.query.get(id):
                    if thumb.locked:
                        continue
                    delete_mediafiles(thumb.name)
                    maintain_folders(ca.raspiconfig.media_path, False, False)
                    deleted_ids.append(id)
        else:
            maintain_folders(ca.raspiconfig.media_path, True, True)
        db.session.close()
        return deleted_ids


@api.route("/<string:id>")
@api.response(401, "Unauthorized", message)
class Thumb(Resource):
    """Preview."""

    @api.marshal_with(files)
    def get(self, id: str):
        """Get file information."""
        return files_db.get(id)

    @api.doc(description="Delete file")
    @api.response(204, "Success")
    @api.response(404, "Not found", message)
    @api.response(422, "Error", message)
    def delete(self, id: str):
        """Delete file."""
        if thumb := files_db.query.get(id):
            if thumb.locked:
                abort(422, f"Protected thumbnail ({id})")
            delete_mediafiles(thumb.name)
            maintain_folders(ca.raspiconfig.media_path, False, False)
            return "", 204
        abort(404, "Thumb not found")


@api.route("/<string:id>/lock")
@api.response(204, "Success")
@api.response(401, "Unauthorized", message)
@api.response(404, "Not found", message)
class Lock(Resource):
    """Lock file."""

    def post(self, id: str):
        """Lock."""
        if thumb := files_db.query.get(id):
            if thumb.locked is False:
                thumb.locked = True
                db.session.commit()
                return "", 204
            return "Thumb is already locked", 204
        abort(404, f"Thumb not found ({id})")


@api.route("/<string:id>/unlock")
@api.response(204, "Success")
@api.response(401, "Unauthorized", message)
@api.response(404, "Not found", message)
class Unlock(Resource):
    """Unock file."""

    def post(self, id: str):
        """Unlock."""
        if thumb := files_db.query.get(id):
            if thumb.locked is True:
                thumb.locked = False
                db.session.commit()
                return "", 204
            return "Thumb is already unlocked", 204
        abort(404, f"Thumb not found ({id})")


@api.route("/<string:id>/convert")
@api.response(204, "Success")
@api.response(401, "Unauthorized", message)
@api.response(404, "Not found", message)
class Convert(Resource):
    """Convert timelapse file to mp4."""

    def post(self, id: str):
        """Coonvert timelapse."""
        if thumb := files_db.query.get(id):
            video_convert(thumb.name)
            return "", 204
        abort(404, "Thumb not found")
