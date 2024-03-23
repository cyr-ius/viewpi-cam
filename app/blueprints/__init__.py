# Create app blueprints
from .auth import bp as auth_bp
from .camera import bp as cam_bp
from .main import bp as main_bp
from .motion import bp as motion_bp
from .preview import bp as pview_bp
from .schedule import bp as sch_bp
from .settings import bp as sets_bp


def init_app(app):
    """Init Blueprint."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(cam_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(motion_bp)
    app.register_blueprint(pview_bp)
    app.register_blueprint(sch_bp)
    app.register_blueprint(sets_bp)
