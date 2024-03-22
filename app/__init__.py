"""ViewPI Camera."""

import logging
import os
import shutil

from flask import Flask, g
from werkzeug.middleware.proxy_fix import ProxyFix

from . import apis, blueprints, models, services
from .helpers.utils import get_pid, launch_schedule, set_timezone
from .models import Settings as settings_db
from .models import db


# pylint: disable=E1101,W0613
def create_app(config=None):
    """Create Flask application."""
    app = Flask(__name__)

    # Create static folder outside app folder
    app.static_folder = f"{app.root_path}/../static"
    os.makedirs(app.static_folder, exist_ok=True)

    app.system_folder = f"{app.root_path}/../system"
    os.makedirs(app.system_folder, exist_ok=True)

    app.db_folder = f"{app.root_path}/../db"
    os.makedirs(app.system_folder, exist_ok=True)

    shutil.copytree(
        f"{app.root_path}/resources/css/fonts",
        f"{ app.static_folder}/css/fonts",
        dirs_exist_ok=True,
    )
    shutil.copytree(
        f"{app.root_path}/resources/img",
        f"{ app.static_folder}/img",
        dirs_exist_ok=True,
    )

    # Set log level
    log_level = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO").upper())
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
    )

    # If we use Docker + Gunicorn, adjust the log handler
    if "GUNICORN_LOGLEVEL" in os.environ:
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    # Proxy
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Load default configuration
    app.config.from_object("app.config")

    # Load config file from FLASK_CONF env variable
    if "FLASK_CONF" in os.environ:
        app.config.from_envvar("FLASK_CONF")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{app.db_folder}/app.db"

    # Register filter
    app.jinja_env.add_extension("jinja2.ext.debug")
    app.jinja_env.add_extension("jinja2.ext.i18n")

    # Load app's components
    apis.init_app(app)
    blueprints.init_app(app)
    services.init_app(app)
    models.init_app(app)

    # Start raspimjpeg
    if bool(int(app.config["SVC_RASPIMJPEG"])) and not get_pid(
        app.config["RASPI_BINARY"]
    ):
        app.raspiconfig.start()

    # Start scheduler
    if bool(int(app.config["SVC_SCHEDULER"])):
        launch_schedule()

    @app.context_processor
    def inject_path_exists():
        def file_exists(path):
            return os.path.exists(f"{app.config.root_path}/{path}")

        return {"file_exists": file_exists}

    @app.before_request
    def before_app_request():
        """Execute before request."""
        settings = settings_db.query.first()
        g.loglevel = settings.data["loglevel"]

    @app.after_request
    def set_secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    with app.app_context():
        if db.inspect(db.engine).has_table("Setting"):
            # Get settings
            settings = settings_db.query.first()

            # Custom log level
            if custom_level := settings.data.get("loglevel"):
                app.logger.setLevel(custom_level.upper())

            # Set timezone
            if offset := settings.data.get("gmt_offset"):
                set_timezone(offset)

    return app
