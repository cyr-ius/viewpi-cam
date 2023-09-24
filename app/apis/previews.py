"""Api camera."""
from flask import request, url_for
from flask_restx import Namespace, Resource, fields

from ..blueprints.preview import draw_files, get_thumbnails, lock_file
from ..helpers.decorator import token_required
from ..helpers.filer import delete_mediafiles

api = Namespace("Previews")
error_m = api.model("Error", {"message": fields.String(required=True)})


class PathURI(fields.Raw):
    def format(self, value):
        return url_for("static", filename=value)


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
        "uri": PathURI(attribute="file_name"),
    },
)

action_m = api.model(
    "Action",
    {
        "action": fields.String(
            required=True, description="Stop or Start action", enum=["lock", "unlock"]
        ),
        "files": fields.List(fields.String),
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
        sort_order = request.args.get("sort_order", True) is True
        thumb_filenames = get_thumbnails(
            sort_order=sort_order, show_types=True, time_filter=1, time_filter_max=8
        )

        return draw_files(thumb_filenames)

    @api.expect(action_m)
    @api.marshal_list_with(files)
    @token_required
    def put(self):
        action = api.payload.get("action")
        for file in api.payload.get("files", []):
            lock_file(file, action == "lock")

        view_alls = draw_files(
            get_thumbnails(
                sort_order=True, show_types=True, time_filter=1, time_filter_max=8
            )
        )

        return [
            file
            for file in view_alls
            if file["file_name"] in api.payload.get("files", [])
        ]

    @api.response(204, "Delete successful")
    @api.expect(api.model("Deletes", {"files": fields.List(fields.String)}))
    @token_required
    def delete(self):
        for file in api.payload.get("files", []):
            delete_mediafiles(file)
        return "", 204
