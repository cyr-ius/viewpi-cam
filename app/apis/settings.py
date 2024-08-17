"""Blueprint Settings API."""

from datetime import datetime as dt

from flask import current_app as ca
from flask import send_file, url_for
from flask_login import login_required
from flask_restx import Namespace, Resource, abort
from sqlalchemy import delete, update
from werkzeug.datastructures import FileStorage

from ..helpers.database import update_img_db
from ..helpers.decorator import role_required
from ..helpers.filer import allowed_file, zip_extract, zip_folder
from ..models import Files, Settings, Ubuttons, db
from ..services.raspiconfig import RaspiConfigError
from .models import button, macro, message, setting

api = Namespace(
    "settings",
    description="Change settings",
    decorators=[role_required("max"), login_required],
)
api.add_model("Set", setting)
api.add_model("Macro", macro)
api.add_model("Button", button)


upload_parser = api.parser()
upload_parser.add_argument("file", location="files", type=FileStorage, required=True)


@api.response(401, "Unauthorized")
@api.route("/")
class Sets(Resource):
    """Settings."""

    @api.marshal_with(setting)
    def get(self):
        """Get settings."""
        settings = db.session.scalars(db.select(Settings)).first()
        return settings.data

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
            {"Location": url_for("api.settings_button", id=ubutton.id)},
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
            try:
                ca.raspiconfig.send(f"um {idx} {cmd}")
            except RaspiConfigError as error:
                abort(500, error)

        return "", 204


@api.response(200, "Success")
@api.response(401, "Unauthorized")
@api.route("/backup")
class Backup(Resource):
    """Download settings."""

    def get(self):
        date_str = dt.now().strftime("%Y%m%d_%H%M%S")
        zipname = f"config_{date_str}.zip"
        zip_file = zip_folder(ca.config_folder)

        return send_file(
            zip_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name=zipname,
        )


@api.response(204, "Success")
@api.response(401, "Unauthorized")
@api.route("/restore")
@api.expect(upload_parser)
class Restore(Resource):
    """Upload settings."""

    def post(self):
        args = upload_parser.parse_args()
        file = args["file"]
        if file and allowed_file(file):
            zip_extract(file, ca.config_folder)
            db.session.execute(delete(Files))
            db.session.commit()
            update_img_db()
        return "", 204
