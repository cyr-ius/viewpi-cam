from .base import db, migrate
from .schema import (  # noqa
    Calendar,
    DaysMode,
    Files,
    Multiviews,
    Presets,
    Scheduler,
    Settings,
    Ubuttons,
    Users,
)


def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db)
