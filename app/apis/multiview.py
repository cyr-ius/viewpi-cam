"""Blueprint Multiview API."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import token_required
from .models import message, stream, streams

api = Namespace("multiview", path="/api")
api.add_model("Error", message)
api.add_model("Stream", stream)
api.add_model("Streams", streams)


@api.response(403, "Forbidden", message)
@api.route("/multiview")
class Streamers(Resource):
    """List hosts."""

    @token_required
    @api.marshal_with(stream, as_list=True)
    def get(self):
        """List hosts."""
        return ca.settings.get("streamers", [])

    @token_required
    @api.expect(streams, validate=True)
    @api.marshal_with(stream)
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
    @api.marshal_with(stream)
    @api.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get streamer."""
        if stm := ca.settings.get_object("streamers", id):
            return stm
        abort(404, "Host not found")

    @token_required
    @api.expect(streams)
    @api.marshal_with(stream)
    @api.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set streamer."""
        api.payload["id"] = id
        if stm := ca.settings.get_object("streamers", id):
            ca.settings.streamers.remove(stm)
            ca.settings.streamers.append(api.payload)
            ca.settings.update(streamers=ca.settings.streamers)
            return api.payload
        abort(404, "Host not found")

    @token_required
    @api.response(204, "Actions is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete streamer."""
        if stm := ca.settings.get_object("streamers", id):
            ca.settings.streamers.remove(stm)
            ca.settings.update(streamers=ca.settings.streamers)
            return "", 204
        abort(404, "Host not found")
