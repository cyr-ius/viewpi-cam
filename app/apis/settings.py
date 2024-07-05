"""Blueprint Settings API."""

from flask import current_app as ca
from flask_login import login_required
from flask_restx import Namespace, Resource
from sqlalchemy import update

from ..helpers.decorator import role_required
from ..models import Settings, Ubuttons, db
from .models import button, buttons, macro, message, setting

api = Namespace(
    "settings",
    description="Change settings",
    decorators=[role_required("max"), login_required],
)
api.add_model("Set", setting)
api.add_model("Macro", macro)
api.add_model("Button", button)
api.add_model("Buttons", buttons)


@api.response(401, "Unauthorized")
@api.route("/")
class Sets(Resource):
    """Settings."""

    @api.marshal_with(setting)
    def get(self):
        """Get settings."""
        return db.session.scalars(db.select(Settings)).first()

    @api.expect(setting)
    @api.response(204, "Success")
    def post(self):
        """Set settings."""
        settings = db.session.scalars(db.select(Settings)).first()
        settings.data.update(api.payload)
        db.session.execute(update(Settings), settings.__dict__)
        db.session.commit()

        if loglevel := api.payload.get("loglevel"):
            ca.logger.setLevel(loglevel)
            ca.logger.debug(f"Log level: {loglevel}")
        return "", 204


@api.response(401, "Unauthorized")
@api.route("/buttons")
class Buttons(Resource):
    """List buttons."""

    @api.marshal_with(buttons, as_list=True)
    def get(self):
        """List buttons."""
        return db.session.scalars(db.select(Ubuttons)).all()

    @api.expect(button)
    @api.marshal_with(buttons, code=201)
    def post(self):
        """Create button."""
        api.payload.pop("id", None)
        ubutton = Ubuttons(**api.payload)
        db.session.add(ubutton)
        db.session.commit()
        return ubutton, 201


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


@api.response(401, "Unauthorized")
@api.route("/macros")
class Macros(Resource):
    """Macros."""

    @staticmethod
    def get_config():
        """Return config."""
        return {item: getattr(ca.raspiconfig, item) for item in ca.config["MACROS"]}

    @api.marshal_with(macro, as_list=True)
    def get(self):
        """Get macros."""
        list_macros = []
        for key, value in Macros().get_config().items():
            state = True
            if value[:1] == "-":
                value = value[1:]
                state = False
            list_macros.append({"name": key, "command": value, "state": state})
        return list_macros

    @api.expect(macro)
    @api.response(204, "Success")
    def post(self):
        """Set macro."""
        if api.payload:
            for idx, name in enumerate(Macros().get_config().keys()):
                if api.payload["name"] == name:
                    break

            cmd = api.payload["command"]
            if not api.payload["state"]:
                cmd = f"-{cmd}"
            ca.raspiconfig.send(f"um {idx} {cmd}")
        return "", 204
