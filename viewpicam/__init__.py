"""ViewPI Camera."""
import logging
import os

from flask import Flask
from flask_assets import Environment
from flask_babel import Babel
from flask_mail import Mail

# from flask_swagger import swagger
from werkzeug.middleware.proxy_fix import ProxyFix

from .services.assets import css_custom, css_main, js_custom, js_main, js_pipan
from .services.handle import (
    handle_access_forbidden,
    handle_bad_request,
    handle_internal_server_error,
    handle_page_not_found,
)
from .services.scheduler import scheduler as job_scheduler

mail = Mail()
assets = Environment()
babel = Babel()


def create_app(config=None):
    viewpicam = Flask(__name__)

    # Create static folder outside app folder
    viewpicam.static_folder = f"{viewpicam.root_path}/../static"

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
        viewpicam.logger.handlers = gunicorn_logger.handlers
        viewpicam.logger.setLevel(gunicorn_logger.level)

    # Proxy
    viewpicam.wsgi_app = ProxyFix(viewpicam.wsgi_app)

    # Load default configuration
    viewpicam.config.from_object("viewpicam.config")

    # Load config file from FLASK_CONF env variable
    if "FLASK_CONF" in os.environ:
        viewpicam.config.from_envvar("FLASK_CONF")

    # Load app's components
    mail.init_app(viewpicam)
    assets.init_app(viewpicam)
    babel.init_app(viewpicam)

    # Register Assets
    assets.register("css_main", css_main)
    assets.register("js_main", js_main)
    assets.register("css_custom", css_custom)
    assets.register("js_custom", js_custom)
    assets.register("js_pipan", js_pipan)

    # Create app blueprints
    from .blueprints.main.routes import main_bp

    viewpicam.register_blueprint(main_bp)

    # Register error handler
    viewpicam.register_error_handler(400, handle_bad_request)
    viewpicam.register_error_handler(403, handle_access_forbidden)
    viewpicam.register_error_handler(404, handle_page_not_found)
    viewpicam.register_error_handler(500, handle_internal_server_error)

    # Register filter
    viewpicam.jinja_env.add_extension("jinja2.ext.debug")
    viewpicam.jinja_env.add_extension("jinja2.ext.i18n")

    @viewpicam.context_processor
    def inject_path_exists():
        def file_exists(path):
            return os.path.exists(f"{viewpicam.config.root_path}/{path}")

        return {"file_exists": file_exists}

    @viewpicam.cli.command("scheduler")
    def scheduler():
        job_scheduler()

    return viewpicam
