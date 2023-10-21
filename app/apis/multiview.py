"""Blueprint Multiview API."""
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required, token_required
from .models import message, multiview, multiviews

api = Namespace(
    "multiview",
    path="/api",
    description="Multiviews",
    decorators=[token_required, role_required("max")],
)
api.add_model("Error", message)
api.add_model("Multiview", multiview)
api.add_model("Multiviews", multiviews)


@api.response(403, "Forbidden", message)
@api.route("/multiviews")
class Multiviews(Resource):
    """List hosts."""

    @api.marshal_with(multiview, as_list=True)
    def get(self):
        """List hosts."""
        return ca.settings.get("multiviews", [])

    @api.expect(multiview)
    @api.marshal_with(multiviews)
    def post(self):
        """Create host."""
        if ca.settings.get("multiviews") is None:
            ca.settings.multiviews = []
        ids = [multiview["id"] for multiview in ca.settings.multiviews]
        api.payload["id"] = 1 if len(ids) == 0 else max(ids) + 1
        ca.settings.multiviews.append(api.payload)
        ca.settings.update(multiviews=ca.settings.multiviews)
        return api.payload


@api.response(403, "Forbidden", message)
@api.route("/multiviews/<int:id>")
class Multiview(Resource):
    """Multiview objet."""

    @api.marshal_with(multiview)
    @api.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get multiview."""
        if stm := ca.settings.get_object("multiviews", id):
            return stm
        abort(404, "Host not found")

    @api.expect(multiviews)
    @api.marshal_with(multiview)
    @api.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set multiview."""
        api.payload["id"] = id
        if stm := ca.settings.get_object("multiviews", id):
            ca.settings.multiviews.remove(stm)
            ca.settings.multiviews.append(api.payload)
            ca.settings.update(multiviews=ca.settings.multiviews)
            return api.payload
        abort(404, "Host not found")

    @api.response(204, "Actions is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete multiview."""
        if stm := ca.settings.get_object("multiviews", id):
            ca.settings.multiviews.remove(stm)
            ca.settings.update(multiviews=ca.settings.multiviews)
            return "", 204
        abort(404, "Host not found")
