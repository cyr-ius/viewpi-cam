"""ViewPI Camera."""
import logging
import os
from subprocess import Popen

from flask import Flask
from flask_assets import Environment
from flask_babel import Babel

# from flask_mail import Mail

# from flask_swagger import swagger
from werkzeug.middleware.proxy_fix import ProxyFix

from .helpers.raspiconfig import RaspiConfig
from .helpers.settings import Settings
from .services.assets import css_custom, css_main, js_custom, js_main, js_pipan
from .services.handle import (
    handle_access_forbidden,
    handle_bad_request,
    handle_internal_server_error,
    handle_page_not_found,
)

# mail = Mail()
assets = Environment()
babel = Babel()
settings = Settings()
raspiconfig = RaspiConfig()


def create_app(config=None):
    app = Flask(__name__)

    # Create static folder outside app folder
    app.static_folder = f"{app.root_path}/../static"

    app.system_folder = f"{app.root_path}/../system"
    if os.path.isdir(app.system_folder) is False:
        os.mkdir(app.system_folder)

    # Read log level from environment variable
    log_level_name = os.environ.get("LOG_LEVEL", "WARNING")
    log_level = logging.getLevelName(log_level_name.upper())
    # Setting logger
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

    # Important ordering
    raspiconfig.init_app(app)
    settings.init_app(app)

    # Register Assets
    assets.register("css_main", css_main)
    assets.register("js_main", js_main)
    assets.register("css_custom", css_custom)
    assets.register("js_custom", js_custom)
    assets.register("js_pipan", js_pipan)

    # Create app blueprints
    from .blueprints.auth.route import bp as auth_bp
    from .blueprints.main.route import bp as main_bp
    from .blueprints.preview.route import bp as pview_bp
    from .blueprints.schedule.route import bp as sch_bp
    from .blueprints.settings.route import bp as sets_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(sch_bp)
    app.register_blueprint(sets_bp)
    app.register_blueprint(pview_bp)

    # Register error handler
    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(403, handle_access_forbidden)
    app.register_error_handler(404, handle_page_not_found)
    app.register_error_handler(500, handle_internal_server_error)

    # Register filter
    app.jinja_env.add_extension("jinja2.ext.debug")
    app.jinja_env.add_extension("jinja2.ext.i18n")

    @app.context_processor
    def inject_path_exists():
        def file_exists(path):
            return os.path.exists(f"{app.config.root_path}/{path}")

        return {"file_exists": file_exists}

    # Create files & folders
    os.makedirs(os.path.dirname(app.raspiconfig.status_file), exist_ok=True)
    os.makedirs(os.path.dirname(app.raspiconfig.control_file), exist_ok=True)
    if (media := app.raspiconfig.media_path) != "":
        os.makedirs(media, exist_ok=True)
    if (macros := app.raspiconfig.macros_path) != "":
        os.makedirs(macros, exist_ok=True)
    if (boxing := app.raspiconfig.boxing_path) != "":
        os.makedirs(boxing, exist_ok=True)

    if os.path.isfile(app.raspiconfig.control_file):
        os.mkfifo(app.raspiconfig.control_file)
    if os.path.isfile(app.raspiconfig.motion_pipe):
        os.mkfifo(app.raspiconfig.motion_pipe)

    if not os.path.isfile(app.raspiconfig.status_file):
        status_file = open(app.raspiconfig.status_file, "a")
        status_file.close()

    # Start Raspimjpeg
    if "RASPIMJPEG_START" in os.environ:
        Popen("raspimjpeg")

    # Start scheduler
    if "SCHEDULER_START" in os.environ:
        """Start scheduler"""
        from .blueprints.schedule.route import launch_schedule

        launch_schedule()

    return app
