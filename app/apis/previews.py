"""Api gallery."""

from flask import current_app as ca
from flask import request
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..blueprints.preview import get_thumbs, video_convert
from ..helpers.decorator import role_required
from ..helpers.filer import delete_mediafiles, maintain_folders
from ..models import Files, db
from .models import deletes, files, lock_mode, message

api = Namespace(
    "previews",
    description="Gallery management",
    decorators=[role_required(["medium", "max"]), login_required],
)
api.add_model("Files", files)
api.add_model("Deletes", deletes)
api.add_model("LockMode", lock_mode)


@api.response(401, "Unauthorized")
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

    @api.doc(description="Delete all files or files list")
    @api.expect(deletes)
    @api.marshal_with(deletes, code=201)
    def delete(self):
        """Delete all media files."""
        deleted_ids = []
        if self.api.payload:
            for id in self.api.payload.get("thumb_id", []):
                if thumb := db.session.scalars(
                    db.select(Files).filter_by(id=id)
                ).first():
                    if thumb.locked:
                        continue
                    delete_mediafiles(thumb.name)
                    maintain_folders(ca.raspiconfig.media_path, False, False)
                    deleted_ids.append(id)
        else:
            maintain_folders(ca.raspiconfig.media_path, True, True)
        db.session.close()
        return deleted_ids, 201


@api.route("/<string:id>")
@api.response(401, "Unauthorized")
@api.response(404, "Not found", message)
@api.response(422, "Error", message)
class Thumb(Resource):
    """Preview."""

    @api.marshal_with(files)
    def get(self, id: str):
        """Get file information."""
        return db.get_or_404(Files, id, description="Thumb not found")

    @api.doc(description="Delete file")
    @api.response(204, "Success")
    def delete(self, id: str):
        """Delete file."""
        thumb = db.get_or_404(Files, id, description="Thumb not found")
        if thumb.locked:
            abort(422, f"Protected thumbnail ({id})")
        delete_mediafiles(thumb.name)
        maintain_folders(ca.raspiconfig.media_path, False, False)
        return "", 204


@api.route("/lock_mode")
@api.response(204, "Success")
@api.response(401, "Unauthorized")
class LockMode(Resource):
    """Lock Mode."""

    @api.expect(lock_mode)
    def post(self):
        """Lock Mode."""
        ids = self.api.payload["ids"]
        mode = self.api.payload["mode"] is True
        ids = [ids] if isinstance(ids, str) else ids
        for id in ids:
            if thumb := db.session.scalars(db.select(Files).filter_by(id=id)).first():
                thumb.locked = mode
                db.session.commit()
        return "", 204


@api.route("/<string:id>/lock")
@api.response(201, "Already lock", message)
@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(404, "Not Found")
class Lock(Resource):
    """Lock file."""

    def post(self, id: str):
        """Lock."""
        thumb = db.get_or_404(Files, id, description="Thumb not found")
        if thumb.locked is True:
            return {"message": "Thumb is already locked"}, 201
        thumb.locked = True
        db.session.commit()
        return "", 204


@api.route("/<string:id>/unlock")
@api.response(201, "Already unlock", message)
@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(404, "Not Found")
class Unlock(Resource):
    """Unock file."""

    def post(self, id: str):
        """Unlock."""
        thumb = db.get_or_404(Files, id, description="Thumb not found")
        if thumb.locked is False:
            return {"message": "Thumb is already unlocked"}, 201
        thumb.locked = False
        db.session.commit()
        return "", 204


@api.route("/<string:id>/convert")
@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.response(404, "Not Found")
class Convert(Resource):
    """Convert timelapse file to mp4."""

    def post(self, id: str):
        """Coonvert timelapse."""
        thumb = db.get_or_404(Files, id, description="Thumb not found")
        video_convert(thumb.name)
        return "", 204
