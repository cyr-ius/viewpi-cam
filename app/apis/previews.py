"""Api gallery."""

from datetime import datetime as dt

from flask import current_app as ca
from flask import request, send_file
from flask_login import login_required
from flask_restx import Namespace, Resource, abort, fields

from ..helpers.decorator import role_required
from ..helpers.filer import delete_mediafiles, get_zip, maintain_folders
from ..helpers.transform import get_thumbs, video_convert
from ..models import Files, db
from .models import files, lock_mode, message, thumb_ids

api = Namespace(
    "previews",
    description="Gallery management",
    decorators=[role_required(["medium", "max"]), login_required],
)
api.add_model("Files", files)
api.add_model("ThumbIds", thumb_ids)
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
    @api.expect([fields.String(example="thumb id")])
    @api.marshal_with([fields.String(example="thumb id")], code=201)
    def delete(self):
        """Delete all media files."""
        deleted_ids = []
        if self.api.payload:
            for id in self.api.payload:
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


@api.route("/zipfile")
@api.response(401, "Unauthorized")
class ZipFile(Resource):
    """Make Zip."""

    @api.expect([fields.String(example="thumb id")])
    def post(self):
        """Make Zip from thumbs list."""
        date_str = dt.now().strftime("%Y%m%d_%H%M%S")
        zipname = f"cam_{date_str}.zip"

        thumbs = [api.payload] if isinstance(api.payload, str) else api.payload
        if thumbs:
            zip_list = [
                thumb.name
                for id in thumbs
                if (
                    thumb := db.session.scalars(
                        db.select(Files).filter_by(id=id)
                    ).first()
                )
            ]
            raw_file = get_zip(zip_list)

        response = send_file(
            raw_file,
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=zipname,
        )
        return response
