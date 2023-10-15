"""Blueprint Multiview API."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort, fields

from ..helpers.decorator import token_required
from .models import message

api = Namespace("multiview")
api.add_model("Error", message)

host = api.model(
    "Stream",
    {
        "id": fields.Integer(required=False, description="Unique id"),
        "streamer": fields.String(
            required=True,
            description="URL Stream MJPEG",
            example="http://192.168.1.1:8080/stream",
        ),
        "delays": fields.Integer(required=True, description="Refresh rate"),
    },
)

hosts = api.model("Streamers", host)
hosts.pop("id")


@api.response(403, "Forbidden", message)
@api.route("/multiview")
class Streamers(Resource):
    """List hosts."""

    @token_required
    @api.marshal_with(host, as_list=True)
    def get(self):
        """List hosts."""
        return ca.settings.get("streamers", [])

    @token_required
    @api.expect(hosts, validate=True)
    @api.marshal_with(host)
    def post(self):
        """Create host."""
        if ca.settings.get("streamers") is None:
            ca.settings.streamers = []
        ids = [streamer["id"] for streamer in ca.settings.streamers]
        api.payload["id"] = 1 if len(ids) == 0 else max(ids) + 1
        ca.settings.streamers.append(api.payload)
        ca.settings.update(streamers=ca.settings.streamers)
        return api.payload


@api.response(403, "Forbidden", message)
@api.route("/multiview/<int:id>")
class Streamer(Resource):
    """Host objet."""

    @token_required
    @api.marshal_with(host)
    @api.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get streamer."""
        if stream := ca.settings.get_object("streamers", id):
            return stream
        abort(404, "Host not found")

    @token_required
    @api.expect(hosts)
    @api.marshal_with(host)
    @api.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set streamer."""
        api.payload["id"] = id
        if stream := ca.settings.get_object("streamers", id):
            ca.settings.streamers.remove(stream)
            ca.settings.streamers.append(api.payload)
            ca.settings.update(streamers=ca.settings.streamers)
            return api.payload
        abort(404, "Host not found")

    @token_required
    @api.response(204, "Actions is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete streamer."""
        if stream := ca.settings.get_object("streamers", id):
            ca.settings.streamers.remove(stream)
            ca.settings.update(streamers=ca.settings.streamers)
            return "", 204
        abort(404, "Host not found")
