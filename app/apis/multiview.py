"""Blueprint Multiview API."""

from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..models import Multiviews as multiviews_db
from ..models import db
from .models import message, multiview, multiviews

api = Namespace(
    "multiview",
    description="Multiviews",
    decorators=[role_required("max"), login_required],
)
api.add_model("Multiview", multiview)
api.add_model("Multiviews", multiviews)


@api.response(401, "Unauthorized")
@api.route("/")
class Multiviews(Resource):
    """List hosts."""

    @api.marshal_with(multiview, as_list=True)
    def get(self):
        """List hosts."""
        return multiviews_db.query.all()

    @api.expect(multiview)
    @api.marshal_with(multiviews, code=201)
    def post(self):
        """Create host."""
        api.payload.pop("id", None)
        multiview = multiviews_db(**api.payload)
        db.session.add(multiview)
        db.session.commit()
        return multiview, 201


@api.response(401, "Unauthorized")
@api.route("/<int:id>")
class Multiview(Resource):
    """Multiview object."""

    @api.marshal_with(multiview)
    def get(self, id: int):
        """Get multiview."""
        return db.get_or_404(multiviews_db, id)

    @api.response(204, "Success")
    @api.response(404, "NotFound", message)
    @api.expect(multiviews)
    def put(self, id: int):
        """Set multiview."""
        if (
            multiview := multiviews_db.query.filter_by(id=id)
        ) and multiview.first() is not None:
            multiview.update(api.payload)
            db.session.commit()
            return "", 204
        abort(404, "Host not found")

    @api.response(204, "Success")
    @api.response(404, "NotFound", message)
    def delete(self, id: int):
        """Delete multiview."""
        if multiview := db.get_or_404(multiviews_db, id):
            db.session.delete(multiview)
            db.session.commit()
            return "", 204
        abort(404, "Host not found")
