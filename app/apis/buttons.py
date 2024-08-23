"""Blueprint Buttons API."""

from flask import url_for
from flask_login import login_required
from flask_restx import Namespace, Resource
from sqlalchemy import update

from ..helpers.decorator import role_required
from ..models import Ubuttons, db
from .models import button, message

api = Namespace(
    "buttons",
    description="Custom buttons",
    decorators=[role_required("max"), login_required],
)

api.add_model("Button", button)


@api.response(401, "Unauthorized")
@api.route("/buttons")
class Buttons(Resource):
    """List buttons."""

    @api.marshal_with(button, as_list=True)
    def get(self):
        """List buttons."""
        return db.session.scalars(db.select(Ubuttons)).all()

    @api.expect(button.copy().pop("id"))
    @api.response(204, "Success")
    def post(self):
        """Create button."""
        api.payload.pop("id", None)
        ubutton = Ubuttons(**api.payload)
        db.session.add(ubutton)
        db.session.commit()
        return (
            "",
            204,
            {"Location": url_for("api.buttons_button", id=ubutton.id)},
        )


@api.response(401, "Unauthorized")
@api.response(404, "Not found", message)
@api.route("/buttons/<int:id>")
class Button(Resource):
    """Button object."""

    @api.marshal_with(button)
    @api.response(404, "Not found", message)
    def get(self, id: int):
        """Get button."""
        return db.get_or_404(Ubuttons, id, description="Button not found")

    @api.expect(button)
    @api.response(204, "Success")
    def put(self, id: int):
        """Set button."""
        db.session.execute(update(Ubuttons), api.payload)
        db.session.commit()
        return "", 204

    @api.response(204, "Actions is success")
    def delete(self, id: int):
        """Delete button."""
        ubutton = db.get_or_404(Ubuttons, id, description="Button not found")
        db.session.delete(ubutton)
        db.session.commit()
        return "", 204
