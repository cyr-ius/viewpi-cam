"""Api camera."""
from flask import request, url_for
from flask_restx import Namespace, Resource, fields

from ..blueprints.preview import draw_files, get_thumbnails, lock_file
from ..helpers.decorator import token_required
from ..helpers.filer import delete_mediafiles
from .models import error_m

api = Namespace("previews")
api.add_model("Error", error_m)


class PathURI(fields.Raw):
    """Path URI."""

    def format(self, value):
        return url_for("static", filename=value)


class Id(fields.Raw):
    """Id."""

    def format(self, value):
        base = value.split(".")[0]
        return base.replace("_", "")


files = api.model(
    "Files",
    {
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
        "id": Id(attribute="file_name", example="string"),
    },
)


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/previews")
class Previews(Resource):
    """Previews."""

    @token_required
    @api.marshal_list_with(files)
    @api.param("order", "Ordrering thumbnail (True/False)")
    def get(self):
        """Get all media files."""
        sort_order = request.args.get("sort_order", True) is True
        thumb_filenames = get_thumbnails(
            sort_order=sort_order, show_types=True, time_filter=1, time_filter_max=8
        )

        return draw_files(thumb_filenames)

    @api.response(204, "Delete successful")
    @api.expect(
        api.model("Deletes", {"ids": fields.List(fields.String(description="id"))})
    )
    @token_required
    def delete(self):
        """Delete multiple media files (id)."""
        for file in api.payload.get("ids", []):
            delete_mediafiles(file)
        return "", 204


@api.response(422, "Error", error_m)
@api.response(403, "Forbidden", error_m)
@api.route("/previews/<string:id>")
class Preview(Resource):
    """Preview."""

    @token_required
    @api.marshal_with(files)
    def get(self, id):
        """Get file information."""
        thumbs = Previews().get()
        for thumb in thumbs:
            if id == thumb["id"]:
                return thumb

    @token_required
    @api.doc(description="Delete file")
    def delete(self, id):
        """Delete file."""
        thumbs = Previews().get()
        for thumb in thumbs:
            if id == thumb["id"]:
                delete_mediafiles(thumb["file_name"])
                break


@api.route(
    "/previews/<string:id>/lock",
    endpoint="preview_lock",
    doc={"description": "Lock file"},
)
@api.route(
    "/previews/<string:id>/unlock",
    endpoint="preview_unlock",
    doc={"description": "Unlock file"},
)
class Actions(Resource):
    """Actions."""

    @token_required
    def post(self, id):
        """Post action."""
        thumbs = Previews().get()
        for thumb in thumbs:
            if id == thumb["id"]:
                lock_file(thumb["file_name"], request.endpoint == "api.preview_lock")
                break
        return {}
