"""ViewPI Camera."""
import logging
import os
import shutil

from flask import Flask
from flask_babel import Babel
from werkzeug.middleware.proxy_fix import ProxyFix

from . import blueprints
from .helpers.raspiconfig import RaspiConfig
from .helpers.settings import Settings
from .helpers.usrmgmt import Usrmgmt
from .helpers.utils import (
    execute_cmd,
    get_locale,
    get_pid,
    get_timezone,
    launch_schedule,
)
from .services.assets import assets
from .services.handle import ErrorHandler, ViewPiCamException

babel = Babel()
settings = Settings()
raspiconfig = RaspiConfig()
usrmgmt = Usrmgmt()
errorhandler = ErrorHandler()


# pylint: disable=E1101,W0613
def create_app(config=None):
    """Create Flask application."""
    app = Flask(__name__)

    # Create static folder outside app folder
    app.static_folder = f"{app.root_path}/../static"

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

    # Load app's components
    assets.init_app(app)
    babel.init_app(app, locale_selector=get_locale, timezone_selector=get_timezone)
    blueprints.init_app(app)
    errorhandler.init_app(app)

    # !!! Important ordering !!!
    raspiconfig.init_app(app)
    settings.init_app(app)
    usrmgmt.init_app(app)

    # Custom log level
    if custom_level := settings.get("loglevel"):
        app.logger.setLevel(custom_level.upper())
    else:
        settings["loglevel"] = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Register filter
    app.jinja_env.add_extension("jinja2.ext.debug")
    app.jinja_env.add_extension("jinja2.ext.i18n")

    # Create files & folders
    os.makedirs(os.path.dirname(app.raspiconfig.status_file), exist_ok=True)
    os.makedirs(os.path.dirname(app.raspiconfig.control_file), exist_ok=True)

    app.system_folder = f"{app.root_path}/../system"
    if os.path.isdir(app.system_folder) is False:
        os.makedirs(app.system_folder, exist_ok=True)

    if (media := app.raspiconfig.media_path) != "":
        os.makedirs(media, exist_ok=True)
    if (macros := app.raspiconfig.macros_path) != "":
        os.makedirs(macros, exist_ok=True)
    if (boxing := app.raspiconfig.boxing_path) != "":
        os.makedirs(boxing, exist_ok=True)

    # Set timezone
    if offset := settings.get("gmt_offset"):
        try:
            execute_cmd(f"ln -sf /usr/share/zoneinfo/{offset} /etc/localtime")
        except ViewPiCamException as error:
            app.logger.error(error)

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

    @app.after_request
    def set_secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    return app
