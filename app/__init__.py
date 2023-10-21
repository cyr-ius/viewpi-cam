"""ViewPI Camera."""
import logging
import os
import shutil

from flask import Flask
from flask_assets import Environment
from flask_babel import Babel
from werkzeug.middleware.proxy_fix import ProxyFix

from .apis import bp as api_bp
from .blueprints.auth import bp as auth_bp
from .blueprints.camera import bp as cam_bp
from .blueprints.main import bp as main_bp
from .blueprints.motion import bp as motion_bp
from .blueprints.preview import bp as pview_bp
from .blueprints.schedule import bp as sch_bp
from .blueprints.schedule import launch_schedule
from .blueprints.settings import bp as sets_bp
from .helpers.raspiconfig import RaspiConfig
from .helpers.settings import Settings
from .helpers.utils import execute_cmd, get_pid
from .services.assets import css_custom, css_main, js_custom, js_main, js_pipan
from .services.handle import (
    ViewPiCamException,
    handle_access_forbidden,
    handle_bad_gateway,
    handle_bad_request,
    handle_internal_server_error,
    handle_page_not_found,
)

assets = Environment()
babel = Babel()
settings = Settings()
raspiconfig = RaspiConfig()


# pylint: disable=E1101,W0613
def create_app(config=None):
    """Create Flask application."""
    app = Flask(__name__)

    # Create static folder outside app folder
    app.static_folder = f"{app.root_path}/../static"

    shutil.copytree(
        f"{app.root_path}/ressources/css/fonts",
        f"{ app.static_folder}/css/fonts",
        dirs_exist_ok=True,
    )
    shutil.copytree(
        f"{app.root_path}/ressources/img",
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
    # mail.init_app(app)
    assets.init_app(app)
    babel.init_app(app)

    # !!! Important ordering !!!
    raspiconfig.init_app(app)
    settings.init_app(app)

    # Custom log level
    if custom_level := settings.get("loglevel"):
        app.logger.setLevel(custom_level.upper())
    else:
        settings["loglevel"] = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Register Assets
    assets.register("css_custom", css_custom)
    assets.register("css_main", css_main)
    assets.register("js_custom", js_custom)
    assets.register("js_main", js_main)
    assets.register("js_pipan", js_pipan)

    # Create app blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(cam_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(motion_bp)
    app.register_blueprint(pview_bp)
    app.register_blueprint(sch_bp)
    app.register_blueprint(sets_bp)
    app.register_blueprint(api_bp)

    # Register error handler
    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(403, handle_access_forbidden)
    app.register_error_handler(404, handle_page_not_found)
    app.register_error_handler(500, handle_internal_server_error)
    app.register_error_handler(502, handle_bad_gateway)

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
    if "NO_RASPIMJPEG" not in os.environ and not get_pid(app.config["RASPI_BINARY"]):
        app.raspiconfig.start()

    # Start scheduler
    if "NO_SCHEDULER" not in os.environ:
        launch_schedule()

    @app.context_processor
    def inject_path_exists():
        def file_exists(path):
            return os.path.exists(f"{app.config.root_path}/{path}")

        return {"file_exists": file_exists}

    return app
