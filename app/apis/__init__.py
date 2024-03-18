"""Apis viewpicam."""

from .base import api, bp
from .captures import api as captures
from .logs import api as logs
from .multiview import api as multiview
from .previews import api as previews
from .schedule import api as schedule
from .settings import api as settings
from .system import api as system
from .totp import api as totp
from .users import api as users


def init_app(app):
    """Init API."""
    app.register_blueprint(bp, url_prefix="/api")

    api.add_namespace(captures)
    api.add_namespace(logs)
    api.add_namespace(multiview)
    api.add_namespace(previews)
    api.add_namespace(schedule)
    api.add_namespace(settings)
    api.add_namespace(system)
    api.add_namespace(totp)
    api.add_namespace(users)
