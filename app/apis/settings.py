"""Blueprint Settings API."""

from flask import current_app as ca
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..models import Settings as settting_db
from ..models import Ubuttons, db
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
        settings = settting_db.query.first()
        return settings.data

    @api.expect(setting)
    @api.response(204, "Success")
    def post(self):
        """Set settings."""
        settings = settting_db.query.first()
        settings.data.update(**api.payload)
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
        return Ubuttons.query.all()

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
@api.route("/buttons/<int:id>")
class Button(Resource):
    """Button object."""

    @api.marshal_with(button)
    @api.response(404, "Not found", message)
    def get(self, id: int):
        """Get button."""
        return db.get_or_404(Ubuttons, id)

    @api.expect(button)
    @api.response(204, "Success")
    @api.response(404, "Not found", message)
    def put(self, id: int):
        """Set button."""
        if (ubutton := Ubuttons.query.filter_by(id=id)) and ubutton.first() is not None:
            ubutton.update(api.payload)
            db.session.commit()
            return "", 204
        abort(404, "Button not found")

    @api.response(204, "Actions is success")
    @api.response(404, "Not found", message)
    def delete(self, id: int):
        """Delete button."""
        if ubutton := db.get_or_404(Ubuttons, id):
            db.session.delete(ubutton)
            db.session.commit()
            return "", 204
        abort(404, "Button not found")


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
