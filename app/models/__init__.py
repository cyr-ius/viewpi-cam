from flask_migrate import Migrate

from .base import db
from .schema import (  # noqa
    Calendar,
    DaysMode,
    LockFiles,
    Multiviews,
    Presets,
    Scheduler,
    Settings,
    Ubuttons,
    Users,
)


def init_app(app):
    db.init_app(app)
    _migrate = Migrate(app, db)  # lgtm [py/unused-local-variable]
