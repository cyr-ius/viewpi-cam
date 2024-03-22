"""Blueprint Settings API."""

import random
from datetime import datetime as dt
from datetime import timezone

import jwt
from flask import current_app as ca
from flask_login import login_required
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import role_required
from ..models import Settings as settting_db
from ..models import Ubuttons, db
from .models import api_token, button, buttons, cam_token, macros, message, setting

api = Namespace(
    "settings",
    description="Change settings",
    decorators=[role_required("max"), login_required],
)
api.add_model("Error", message)
api.add_model("Set", setting)
api.add_model("Macros", macros)
api.add_model("CamToken", cam_token)
api.add_model("APIToken", api_token)
api.add_model("Button", button)
api.add_model("Buttons", buttons)


@api.response(403, "Forbidden", message)
@api.route("/")
class Sets(Resource):
    """Settings."""

    @api.marshal_with(setting)
    def get(self):
        """Get settings."""
        settings = settting_db.query.first()
        return settings.data

    @api.expect(setting)
    @api.marshal_with(setting)
    @api.response(204, "Action is success")
    def post(self):
        """Set settings."""
        settings = settting_db.query.first()
        settings.data.update(**api.payload)
        db.session.commit()
        if loglevel := api.payload.get("loglevel"):
            ca.logger.setLevel(loglevel)
        return "", 204


@api.response(403, "Forbidden", message)
@api.route("/buttons")
class Buttons(Resource):
    """List buttons."""

    @api.marshal_with(buttons, as_list=True)
    def get(self):
        """List buttons."""
        return Ubuttons.query.all()

    @api.expect(button)
    @api.marshal_with(buttons)
    def post(self):
        """Create button."""
        api.payload.pop("id", None)
        ubutton = Ubuttons(**api.payload)
        db.session.add(ubutton)
        db.session.commit()
        return ubutton


@api.response(403, "Forbidden", message)
@api.route("/buttons/<int:id>")
class Button(Resource):
    """Button object."""

    @api.marshal_with(button)
    @api.response(404, "Not found", message)
    def get(self, id: int):
        """Get button."""
        return db.get_or_404(Ubuttons, id)

    @api.expect(button)
    @api.marshal_with(button)
    @api.response(404, "Not found", message)
    def put(self, id: int):
        """Set button."""
        if ubutton := db.get_or_404(Ubuttons, id):
            ubutton.update(**api.payload)
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


@api.response(403, "Forbidden", message)
@api.route("/ctoken")
class Token(Resource):
    """Token."""

    @api.marshal_with(cam_token)
    def get(self):
        """Get token."""
        settings = settting_db.query.first()
        return {"cam_token": settings.data["cam_token"]}

    @api.marshal_with(cam_token)
    def post(self):
        """Create token."""
        secure_token = f"B{random.getrandbits(256)}"
        settings = settting_db.query.first()
        settings.data["cam_token"] = secure_token
        db.session.commit()
        return {"cam_token": secure_token}

    @api.response(204, "Actions is success")
    def delete(self):
        """Delete token."""
        settings = settting_db.query.first()
        settings.data.pop("cam_token", None)
        db.session.commit()
        return "", 204


@api.response(403, "Forbidden", message)
@api.route("/token", doc=False)
class APIToken(Resource):
    """Token."""

    @api.marshal_with(api_token)
    def get(self):
        """Get token."""
        settings = settting_db.query.first()
        return {"api_token": settings.data["api_token"]}

    @api.marshal_with(api_token)
    def post(self):
        """Create token."""
        secure_token = jwt.encode(
            {"iss": "system", "id": 0, "iat": dt.now(tz=timezone.utc)},
            ca.config["SECRET_KEY"],
            algorithm="HS256",
        )
        settings = settting_db.query.first()
        settings.data["api_token"] = secure_token
        db.session.commit()
        return {"api_token": secure_token}

    @api.response(204, "Actions is success")
    def delete(self):
        """Delete token."""
        settings = settting_db.query.first()
        settings.data.pop(api_token, None)
        db.session.commit()
        return "", 204


@api.response(403, "Forbidden", message)
@api.route("/macros")
class Macros(Resource):
    """Macros."""

    @staticmethod
    def get_config():
        """Return config."""
        return {item: getattr(ca.raspiconfig, item) for item in ca.config["MACROS"]}

    @api.marshal_with(macros, as_list=True)
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

    @api.expect(macros)
    @api.marshal_with(macros)
    @api.response(204, "Action is success")
    def post(self):
        """Set macro."""
        if api.payload:
            name = api.payload["name"]
            command = api.payload["command"]
            if not api.payload["state"]:
                command = f"-{command}"
            ca.raspiconfig.set_config({name: command})
        return "", 204
