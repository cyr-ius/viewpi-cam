from datetime import datetime as dt
from datetime import timezone
from typing import List

import jwt
import pyotp
from flask import current_app as ca
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.mutable import MutableDict
from werkzeug.security import check_password_hash

from .base import db


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(MutableDict.as_mutable(JSON))


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
    alternate_id: db.Mapped[int] = db.mapped_column(db.String)
    enabled: db.Mapped[bool] = db.mapped_column(db.Boolean, default=True)
    locale: db.Mapped[str] = db.mapped_column(db.String(2), default="en")
    name: db.Mapped[str] = db.mapped_column(db.String, unique=True)
    secret: db.Mapped[str] = db.mapped_column(db.String)
    otp_secret: db.Mapped[str] = db.mapped_column(db.String)
    otp_confirmed: db.Mapped[str] = db.mapped_column(db.Boolean, default=False)
    api_token: db.Mapped[str] = db.mapped_column(db.String)
    cam_token: db.Mapped[str] = db.mapped_column(db.String)
    right: db.Mapped[str] = db.mapped_column(
        db.ForeignKey("roles.level"), nullable=False
    )

    roles: db.Mapped["Roles"] = db.relationship(back_populates="users")

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.enabled

    def is_anonymous(self):
        return False

    def level(self):
        return int(self.right)

    def get_id(self):
        return str(self.id)

    def set_secret(self) -> None:
        """Set otp code."""
        if self.otp_confirmed is None:
            self.otp_secret = pyotp.random_base32()
            db.session.commit()

    def delete_secret(self) -> None:
        """Remove otp code."""
        if self.otp_confirmed:
            self.otp_secret = None
            self.otp_confirmed = False
            db.session.commit()

    def check_otp_secret(self, code: str) -> bool:
        """Validate otp code."""
        otp = pyotp.TOTP(self.otp_secret)
        return otp.verify(code)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.secret, password)

    def generate_jwt(self) -> str:
        dt_now = dt.now(tz=timezone.utc)
        dt_lifetime = dt_now + ca.config["PERMANENT_SESSION_LIFETIME"]
        return jwt.encode(
            payload={
                "iis": self.name,
                "id": self.id,
                "iat": dt_now,
                "exp": dt_lifetime,
            },
            key=ca.config["SECRET_KEY"],
            algorithm="HS256",
        )


class Roles(db.Model):
    __tablename__ = "roles"
    level: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)

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
    db.Column("scheduler_id", db.Integer, db.ForeignKey("scheduler.id")),
    db.Column("calendar_id", db.Integer, db.ForeignKey("calendar.id")),
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


class Scheduler(db.Model):
    __tablename__ = "scheduler"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    command_on: db.Mapped[str] = db.mapped_column(db.String)
    command_off: db.Mapped[str] = db.mapped_column(db.String)
    mode: db.Mapped[str] = db.mapped_column(db.String)
    enabled: db.Mapped[bool] = db.mapped_column(db.Boolean)
    period: db.Mapped[str] = db.mapped_column(db.String)
    daysmode_id: db.Mapped[int] = db.mapped_column(
        db.ForeignKey("daysmode.id"), nullable=False
    )

    daysmode: db.Mapped["DaysMode"] = db.relationship(back_populates="scheduler")
    calendars: db.Mapped[List["Calendar"]] = db.relationship(
        secondary=scheduler_calendar
    )

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
