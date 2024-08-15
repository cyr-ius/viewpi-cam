"""Blueprint Multiview API."""

from flask import url_for
from flask_login import login_required
from flask_restx import Namespace, Resource
from sqlalchemy import update

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
        return db.session.scalars(db.select(multiviews_db)).all()

    @api.expect(multiview)
    @api.marshal_with(multiviews, code=201)
    def post(self):
        """Create host."""
        api.payload.pop("id", None)
        multiview = multiviews_db(**api.payload)
        db.session.add(multiview)
        db.session.commit()
        return multiview, 201, {"Location": url_for("api.multiview_multiview", id=multiview.id)}


@api.response(401, "Unauthorized")
@api.response(404, "Not found", message)
@api.route("/<int:id>")
class Multiview(Resource):
    """Multiview object."""

    @api.marshal_with(multiview)
    def get(self, id: int):
        """Get multiview."""
        return db.get_or_404(multiviews_db, id, description="View not found")

    @api.response(204, "Success")
    @api.expect(multiviews)
    def put(self, id: int):
        """Set multiview."""
        db.session.execute(update(multiviews_db), api.payload)
        db.session.commit()
        return "", 204

    @api.response(204, "Success")
    def delete(self, id: int):
        """Delete multiview."""
        multiview = db.get_or_404(multiviews_db, id, description="View not found")
        db.session.delete(multiview)
        db.session.commit()
        return "", 204
