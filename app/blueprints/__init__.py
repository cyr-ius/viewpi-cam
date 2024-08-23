# Create app blueprints
from .camera import bp as cam_bp


def init_app(app):
    """Init Blueprint."""
    app.register_blueprint(cam_bp)
