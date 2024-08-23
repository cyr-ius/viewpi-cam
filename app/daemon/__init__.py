# Create app blueprints
from .schedule import bp

def init_app(app):
    """Init Blueprint."""
    app.register_blueprint(bp)

