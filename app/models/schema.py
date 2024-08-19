"""Schema database."""

import random
import uuid
from datetime import datetime as dt
from datetime import timezone
from typing import Optional

import jwt
import pyotp
from flask import current_app as ca
from flask_restx import abort
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash

from .base import db


class Settings(db.Model):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[JSON] = mapped_column(type_=JSON)


class Multiviews(db.Model):
    __tablename__ = "multiviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    delay: Mapped[int]
    state: Mapped[int]
    url: Mapped[str]


class Users(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    alternative_id: Mapped[int] = mapped_column(default=str(uuid.uuid4()))
    enabled: Mapped[bool] = mapped_column(default=True)
    locale: Mapped[str] = mapped_column(default="en")
    name: Mapped[str] = mapped_column(unique=True)
    secret: Mapped[Optional[str]]
    otp_secret: Mapped[Optional[str]]
    otp_confirmed: Mapped[str] = mapped_column(default=False)
    api_token: Mapped[Optional[str]]
    cam_token: Mapped[Optional[str]]
    right: Mapped[str] = mapped_column(ForeignKey("roles.level"))
    roles: Mapped["Roles"] = relationship(back_populates="users")

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.enabled

    def is_anonymous(self):
        return False

    def level(self):
        return int(self.right)

    def get_id(self):
        return str(self.alternative_id)

    def set_otp_secret(self) -> None:
        """Set otp code."""
        if not self.otp_confirmed:
            self.otp_secret = pyotp.random_base32()
            db.session.commit()

    def delete_otp_secret(self) -> None:
        """Remove otp code."""
        if self.otp_confirmed:
            self.otp_secret = None
            self.otp_confirmed = False
            db.session.commit()

    def set_camera_token(self) -> str:
        """Set otp code."""
        self.cam_token = f"B{random.getrandbits(256)}"
        db.session.commit()
        return self.cam_token

    def delete_camera_token(self) -> None:
        self.cam_token = None
        db.session.commit()

    def set_api_token(self) -> str:
        self.api_token = jwt.encode(
            payload={"iss": self.name, "id": self.id, "iat": dt.now(tz=timezone.utc)},
            key=ca.config["SECRET_KEY"],
            algorithm="HS256",
        )
        db.session.commit()
        return self.api_token

    def delete_api_token(self) -> None:
        self.api_token = None
        db.session.commit()

    def confirmed_otp_secret(self, code: str) -> bool:
        """Validate otp code."""
        otp = pyotp.TOTP(self.otp_secret)
        self.otp_confirmed = otp.verify(code)
        db.session.commit()
        return self.otp_confirmed

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
                "otp": self.otp_confirmed == 1
            },
            key=ca.config["SECRET_KEY"],
            algorithm="HS256",
        ) , dt_lifetime

    def create_user(self) -> None:
        user = db.session.scalars(
            db.select(Users).filter(Users.name == self.name.lower())
        ).first()
        if user:
            abort(422, "User name is already exists, please change.")
        db.session.add(self)
        db.session.commit()


class Roles(db.Model):
    __tablename__ = "roles"
    level: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    users: Mapped["Users"] = relationship(back_populates="roles")


class Presets(db.Model):
    __tablename__ = "presets"
    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str]
    name: Mapped[str]
    width: Mapped[int]
    height: Mapped[int]
    fps: Mapped[int]
    i_width: Mapped[int]
    i_height: Mapped[int]
    i_rate: Mapped[int]


class Ubuttons(db.Model):
    __tablename__ = "ubuttons"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    macro: Mapped[str]
    style: Mapped[Optional[str]]
    other: Mapped[Optional[str]]
    css_class: Mapped[Optional[str]]
    display: Mapped[bool] = mapped_column(default=False)


scheduler_calendar = db.Table(
    "scheduler_calendar",
    db.Model.metadata,
    db.Column("scheduler_id", db.Integer, ForeignKey("scheduler.id"), nullable=False),
    db.Column("calendar_id", db.Integer, ForeignKey("calendar.id"), nullable=False),
)


class Calendar(db.Model):
    __tablename__ = "calendar"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class DaysMode(db.Model):
    __tablename__ = "daysmode"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    scheduler: Mapped["Scheduler"] = relationship(back_populates="daysmode")


class Scheduler(db.Model):
    __tablename__ = "scheduler"
    id: Mapped[int] = mapped_column(primary_key=True)
    command_on: Mapped[str]
    command_off: Mapped[str]
    mode: Mapped[str]
    enabled: Mapped[bool]
    period: Mapped[str]
    daysmode_id: Mapped[int] = mapped_column(ForeignKey("daysmode.id"))
    daysmode: Mapped["DaysMode"] = relationship(back_populates="scheduler")
    calendars: Mapped[list["Calendar"]] = relationship(secondary=scheduler_calendar)


class Files(db.Model):
    __tablename__ = "files"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    type: Mapped[str]
    size: Mapped[int]
    icon: Mapped[str]
    datetime: Mapped[dt]
    locked: Mapped[bool]
    realname: Mapped[str] = mapped_column(index=True, unique=True)
    number: Mapped[str]
    lapse_count: Mapped[int]
    duration: Mapped[int]
