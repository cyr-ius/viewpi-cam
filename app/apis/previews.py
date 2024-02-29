"""Api gallery."""

from flask import current_app as ca
from flask import request
from flask_restx import Namespace, Resource, abort

from ..blueprints.preview import get_thumb, get_thumbnails, video_convert
from ..helpers.decorator import role_required, token_required
from ..helpers.filer import delete_mediafiles, maintain_folders
from ..models import LockFiles as lockfiles_db
from ..models import db
from .models import deletes, files, forbidden, message

api = Namespace(
    "previews",
    description="Gallery management",
    decorators=[token_required, role_required(["medium", "max"])],
)
api.add_model("Error", message)
api.add_model("Forbidden", forbidden)
api.add_model("Files", files)
api.add_model("Deletes", deletes)


@api.response(403, "Forbidden", forbidden)
@api.route("/")
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

    @api.doc(description="Delete  all files or files list")
    @api.response(204, "Action is success")
    @api.expect(deletes)
    def delete(self):
        """Delete all media files."""
        if self.api.payload:
            for uid in self.api.payload.get("thumb_id", []):
                if thumb := get_thumb(uid):
                    if lockfiles_db.query.get(uid):
                        continue
                    delete_mediafiles(thumb["file_name"])
                    maintain_folders(ca.raspiconfig.media_path, False, False)
        else:
            maintain_folders(ca.raspiconfig.media_path, True, True)
        return "", 204


@api.route("/<string:id>")
@api.response(403, "Forbidden", forbidden)
class Preview(Resource):
    """Preview."""

    @api.marshal_with(files)
    def get(self, id: str):
        """Get file information."""
        return get_thumb(id)

    @api.doc(description="Delete file")
    @api.response(204, "Action is success")
    @api.response(404, "Not found", message)
    @api.response(422, "Error", message)
    def delete(self, id: str):
        """Delete file."""
        if thumb := get_thumb(id):
            if lockfiles_db.query.get(id):
                abort(422, f"Protected thumbnail ({id})")
            delete_mediafiles(thumb["file_name"])
            maintain_folders(ca.raspiconfig.media_path, False, False)
            return "", 204
        abort(404, "Thumb not found")


@api.route("/<string:id>/lock")
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Lock(Resource):
    """Lock file."""

    def post(self, id: str):
        """Lock."""
        thumb = get_thumb(id)
        if thumb and lockfiles_db.query.get(thumb["id"]) is None:
            lockfile = lockfiles_db(id=thumb["id"], name=thumb["file_name"])
            db.session.add(lockfile)
            db.session.commit()
            return "", 204
        abort(404, f"Thumb not found ({id})")


@api.route("/<string:id>/unlock")
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Unlock(Resource):
    """Unock file."""

    def post(self, id: str):
        """Unlock."""
        thumb = get_thumb(id)
        if thumb and (lockfile := lockfiles_db.query.get(thumb["id"])):
            db.session.delete(lockfile)
            db.session.commit()
            return "", 204
        abort(404, f"Thumb not found ({id})")


@api.route("/<string:id>/convert")
@api.response(204, "Action is success")
@api.response(404, "Not found", message)
@api.response(403, "Forbidden", forbidden)
class Convert(Resource):
    """Convert timelapse file to mp4."""

    def post(self, id: str):
        """Coonvert timelapse."""
        if thumb := get_thumb(id):
            video_convert(thumb["file_name"])
            return "", 204
        abort(404, "Thumb not found")
