"""Blueprint Settings API."""
import random

from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

from ..helpers.decorator import token_required
from .models import button, buttons, macros, message, setting, token

api = Namespace("settings", path="/api", description="Change settings")
api.add_model("Error", message)
api.add_model("Set", setting)
api.add_model("Macros", macros)
api.add_model("Token", token)

ubuttons = Namespace("buttons", path="/api", description="User buttons")
ubuttons.add_model("Error", message)
ubuttons.add_model("Button", button)
ubuttons.add_model("Buttons", buttons)


@ubuttons.response(403, "Forbidden", message)
@ubuttons.route("/buttons")
class Buttons(Resource):
    """List buttons."""

    @ubuttons.marshal_with(buttons, as_list=True)
    @token_required
    def get(self):
        """List buttons."""
        return ca.settings.get("ubuttons", [])

    @ubuttons.expect(button)
    @ubuttons.marshal_with(buttons)
    @token_required
    def post(self):
        """Create button."""
        if ca.settings.get("ubuttons") is None:
            ca.settings.ubuttons = []
        ids = [button["id"] for button in ca.settings.ubuttons]
        ubuttons.payload["id"] = 1 if len(ids) == 0 else max(ids) + 1
        ca.settings.ubuttons.append(ubuttons.payload)
        ca.settings.update(ubuttons=ca.settings.ubuttons)
        return ubuttons.payload


@ubuttons.response(403, "Forbidden", message)
@ubuttons.route("/buttons/<int:id>")
class Button(Resource):
    """Button objet."""

    def get_byid(self, id: int):  # pylint: disable=W0622
        """Return button."""
        for button_dict in ca.settings.get("ubuttons", []):
            if button_dict["id"] == id:
                return button_dict

    @token_required
    @ubuttons.marshal_with(button)
    @ubuttons.response(404, "Not found", message)
    def get(self, id: int):  # pylint: disable=W0622
        """Get button."""
        if button_dict := self.get_byid(id):
            return button_dict
        abort(404, "Button not found")

    @token_required
    @ubuttons.expect(button)
    @ubuttons.marshal_with(button)
    @ubuttons.response(404, "Not found", message)
    def put(self, id: int):  # pylint: disable=W0622
        """Set button."""
        if dict_button := self.get_byid(id):
            ca.settings.ubuttons.remove(dict_button)
            ubuttons.payload["id"] = id
            ca.settings.ubuttons.append(ubuttons.payload)
            ca.settings.update(ubuttons=ca.settings.ubuttons)
            return ubuttons.payload
        abort(404, "Button not found")

    @token_required
    @ubuttons.response(204, "Actions is success")
    @ubuttons.response(404, "Not found", message)
    def delete(self, id: int):  # pylint: disable=W0622
        """Delete button."""
        if dict_button := self.get_byid(id):
            ca.settings.ubuttons.remove(dict_button)
            ca.settings.update(ubuttons=ca.settings.ubuttons)
            return "", 204
        abort(404, "Button not found")


@api.response(403, "Forbidden", message)
@api.route("/settings")
class Sets(Resource):
    """Settings."""

    @token_required
    @api.marshal_with(setting)
    def get(self):
        """Get settings."""
        return ca.settings

    @token_required
    @ubuttons.expect(setting)
    @api.marshal_with(setting)
    @api.response(204, "Action is success")
    def post(self):
        """Set setttings."""
        ca.settings.update(**api.payload)
        if loglevel := api.payload.get("loglevel"):
            ca.logger.setLevel(loglevel)
        return "", 204


@api.response(403, "Forbidden", message)
@api.route("/token")
class Token(Resource):
    """Token."""

    @token_required
    @api.marshal_with(token)
    def get(self):
        """Get token."""
        return {"token": ca.settings.get("token")}

    @token_required
    @api.marshal_with(token)
    def post(self):
        """Create token."""
        secure_token = f"B{random.getrandbits(256)}"
        ca.settings.update(token=secure_token)
        return {"token": token}

    @token_required
    @api.response(204, "Actions is success")
    def delete(self):
        """Delete token."""
        del ca.settings.token
        ca.settings.update(token=None)
        return "", 204


@api.response(403, "Forbidden", message)
@api.route("/macros")
class Macros(Resource):
    """Macros."""

    @staticmethod
    def get_config():
        """Return config."""
        return {item: getattr(ca.raspiconfig, item) for item in ca.config["MACROS"]}

    @token_required
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

    @token_required
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
