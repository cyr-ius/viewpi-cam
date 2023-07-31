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
from .helpers.settings import Settings

mail = Mail()
assets = Environment()
babel = Babel()
settings = Settings()


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
    mail.init_app(app)
    assets.init_app(app)
    babel.init_app(app)
    settings.init_app(app)

    # Register Assets
    assets.register("css_main", css_main)
    assets.register("js_main", js_main)
    assets.register("css_custom", css_custom)
    assets.register("js_custom", js_custom)
    assets.register("js_pipan", js_pipan)

    # Create app blueprints
    from .blueprints.main.routes import bp as main_bp
    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.schedule.routes import bp as sch_bp
    from .blueprints.settings.route import bp as sets_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(sch_bp)
    app.register_blueprint(sets_bp)

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

    # Init settings
    app.settings = settings

    # Start scheduler
    if "SCHEDULER_START" in os.environ:
        """Start scheduler"""
        from .blueprints.schedule.routes import launch_schedule

        launch_schedule()

    return app
