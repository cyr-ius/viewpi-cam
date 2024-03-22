# Create app blueprints
from .auth import bp as auth_bp
from .base import (
    handle_access_forbidden,
    handle_bad_gateway,
    handle_bad_request,
    handle_internal_server_error,
    handle_page_not_found,
    login_manager,
)
from .camera import bp as cam_bp
from .main import bp as main_bp
from .motion import bp as motion_bp
from .preview import bp as pview_bp
from .schedule import bp as sch_bp
from .settings import bp as sets_bp


def init_app(app):
    """Init Blueprint."""
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    app.register_blueprint(auth_bp)
    app.register_blueprint(cam_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(motion_bp)
    app.register_blueprint(pview_bp)
    app.register_blueprint(sch_bp)
    app.register_blueprint(sets_bp)

    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(403, handle_access_forbidden)
    app.register_error_handler(404, handle_page_not_found)
    app.register_error_handler(500, handle_internal_server_error)
    app.register_error_handler(502, handle_bad_gateway)
