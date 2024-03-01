from typing import List

from .base import db


class Settings(db.Model):
    __tablename__ = "settings"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    api_token: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    cam_token: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    autocamera_interval: db.Mapped[int] = db.mapped_column(db.Integer)
    autocapture_interval: db.Mapped[int] = db.mapped_column(db.Integer)
    cmd_poll: db.Mapped[float] = db.mapped_column(db.Float)
    dawnstart_minutes: db.Mapped[int] = db.mapped_column(db.Integer)
    duskend_minutes: db.Mapped[int] = db.mapped_column(db.Integer)
    dayend_minutes: db.Mapped[int] = db.mapped_column(db.Integer)
    daystart_minutes: db.Mapped[int] = db.mapped_column(db.Integer)
    daymode: db.Mapped[int] = db.mapped_column(
        db.ForeignKey("daysmode.id"), nullable=False
    )
    gmt_offset: db.Mapped[str] = db.mapped_column(db.String)
    loglevel: db.Mapped[str] = db.mapped_column(db.String)
    latitude: db.Mapped[float] = db.mapped_column(db.Float)
    longitude: db.Mapped[float] = db.mapped_column(db.Float)
    management_command: db.Mapped[str] = db.mapped_column(db.String)
    management_interval: db.Mapped[int] = db.mapped_column(db.Integer)
    max_capture: db.Mapped[int] = db.mapped_column(db.Integer)
    mode_poll: db.Mapped[int] = db.mapped_column(db.Integer)
    pilight: db.Mapped[bool] = db.mapped_column(db.Boolean)
    pipan: db.Mapped[bool] = db.mapped_column(db.Boolean)
    servo: db.Mapped[bool] = db.mapped_column(db.Boolean)
    purgeimage_hours: db.Mapped[int] = db.mapped_column(db.Integer)
    purgelapse_hours: db.Mapped[int] = db.mapped_column(db.Integer)
    purgespace_level: db.Mapped[int] = db.mapped_column(db.Integer)
    purgespace_modeex: db.Mapped[int] = db.mapped_column(db.Integer)
    purgevideo_hours: db.Mapped[int] = db.mapped_column(db.Integer)
    upreset: db.Mapped[str] = db.mapped_column(
        db.ForeignKey("presets.mode"), nullable=False
    )

    presets: db.Mapped["Presets"] = db.relationship(back_populates="settings")
    daysmode: db.Mapped["DaysMode"] = db.relationship()

    def __repr__(self):
        return "<Settings {0}r>".format(self.name)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Multiviews(db.Model):
    __tablename__ = "multiviews"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    delay: db.Mapped[int] = db.mapped_column(db.Integer)
    state: db.Mapped[int] = db.mapped_column(db.Integer)
    url: db.Mapped[str] = db.mapped_column(db.String)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Users(db.Model):
    __tablename__ = "users"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    locale: db.Mapped[str] = db.mapped_column(db.String(2), default="en")
    name: db.Mapped[str] = db.mapped_column(db.String, unique=True)
    secret: db.Mapped[str] = db.mapped_column(db.String)
    totp: db.Mapped[str] = db.mapped_column(db.String)
    right = db.mapped_column(db.ForeignKey("roles.id"))

    roles: db.Mapped["Roles"] = db.relationship(back_populates="users")

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Roles(db.Model):
    __tablename__ = "roles"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    level: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)

    users: db.Mapped["Users"] = db.relationship(back_populates="roles")


class Presets(db.Model):
    __tablename__ = "presets"
    id: db.Mapped[int] = db.mapped_column(db.String, primary_key=True)
    mode: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    width: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    height: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    fps: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    i_width: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    i_height: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    i_rate: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)

    settings: db.Mapped["Settings"] = db.relationship(back_populates="presets")


class LockFiles(db.Model):
    __tablename__ = "lock_files"
    id: db.Mapped[str] = db.mapped_column(db.String, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)


class Ubuttons(db.Model):
    __tablename__ = "ubuttons"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    macro: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    style: db.Mapped[str] = db.mapped_column(db.String)
    other: db.Mapped[str] = db.mapped_column(db.String)
    css_class: db.Mapped[str] = db.mapped_column(db.String)
    display: db.Mapped[bool] = db.mapped_column(db.Boolean)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


scheduler_calendar = db.Table(
    "scheduler_calendar",
    db.Model.metadata,
    db.Column(
        "scheduler_id", db.Integer, db.ForeignKey("scheduler.id"), primary_key=True
    ),
    db.Column(
        "calendar_id", db.Integer, db.ForeignKey("calendar.id"), primary_key=True
    ),
)


class Calendar(db.Model):
    __tablename__ = "calendar"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)


class DaysMode(db.Model):
    __tablename__ = "daysmode"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)

    scheduler: db.Mapped["Scheduler"] = db.relationship(back_populates="daysmode")
    settings: db.Mapped["Settings"] = db.relationship(back_populates="daysmode")


class Scheduler(db.Model):
    __tablename__ = "scheduler"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    command_on: db.Mapped[str] = db.mapped_column(db.String)
    command_off: db.Mapped[str] = db.mapped_column(db.String)
    mode: db.Mapped[str] = db.mapped_column(db.String)
    enabled: db.Mapped[bool] = db.mapped_column(db.Boolean)
    daysmode_id: db.Mapped[int] = db.mapped_column(db.ForeignKey("daysmode.id"))
    period: db.Mapped[str] = db.mapped_column(db.String)

    daysmode: db.Mapped["DaysMode"] = db.relationship(back_populates="scheduler")
    calendars: db.Mapped[List["Calendar"]] = db.relationship(
        secondary=scheduler_calendar
    )

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
