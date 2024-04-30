""" Schema database."""
import random
import uuid
from datetime import datetime as dt
from datetime import timezone

import jwt
import pyotp
from flask import current_app as ca
from flask_restx import abort
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
    delay: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    state: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    url: db.Mapped[str] = db.mapped_column(db.String, nullable=False)

    def delete(self):
        """Delete."""
        db.session.delete(self)
        db.session.commit()


class Users(db.Model):
    __tablename__ = "users"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    alternative_id: db.Mapped[int] = db.mapped_column(
        db.String, default=str(uuid.uuid4()), nullable=False
    )
    enabled: db.Mapped[bool] = db.mapped_column(
        db.Boolean, nullable=False, default=True
    )
    locale: db.Mapped[str] = db.mapped_column(
        db.String(2), default="en", nullable=False
    )
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False, unique=True)
    secret: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    otp_secret: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    otp_confirmed: db.Mapped[str] = db.mapped_column(
        db.Boolean, default=False, nullable=False
    )
    api_token: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    cam_token: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    right: db.Mapped[str] = db.mapped_column(
        db.ForeignKey("roles.level"), nullable=False
    )

    roles: db.Mapped["Roles"] = db.relationship(back_populates="users")

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

    def check_otp_secret(self, code: str) -> bool:
        """Validate otp code."""
        otp = pyotp.TOTP(self.otp_secret)
        self.otp_confirmed = otp.verify(code)
        db.session.commit()
        return self.otp_confirmed

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

    def create_user(self) -> None:
        user = Users.query.filter(str(Users.name).lower() == self.name.lower()).first()
        if user:
            abort(422, "User name is already exists, please change.")

        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete."""
        db.session.delete(self)
        db.session.commit()


class Roles(db.Model):
    __tablename__ = "roles"
    level: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False, unique=True)

    users: db.Mapped["Users"] = db.relationship(back_populates="roles")


class Presets(db.Model):
    __tablename__ = "presets"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    mode: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    width: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    height: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    fps: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    i_width: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    i_height: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    i_rate: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)


class Ubuttons(db.Model):
    __tablename__ = "ubuttons"
    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    macro: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    style: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    other: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    css_class: db.Mapped[str] = db.mapped_column(db.String, nullable=True)
    display: db.Mapped[bool] = db.mapped_column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    def delete(self):
        """Delete."""
        db.session.delete(self)
        db.session.commit()


scheduler_calendar = db.Table(
    "scheduler_calendar",
    db.Model.metadata,
    db.Column(
        "scheduler_id", db.Integer, db.ForeignKey("scheduler.id"), nullable=False
    ),
    db.Column("calendar_id", db.Integer, db.ForeignKey("calendar.id"), nullable=False),
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
    command_on: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    command_off: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    mode: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    enabled: db.Mapped[bool] = db.mapped_column(db.Boolean, nullable=False)
    period: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    daysmode_id: db.Mapped[int] = db.mapped_column(
        db.ForeignKey("daysmode.id"), nullable=False
    )

    daysmode: db.Mapped["DaysMode"] = db.relationship(back_populates="scheduler")
    calendars: db.Mapped[list["Calendar"]] = db.relationship(
        secondary=scheduler_calendar
    )


class Files(db.Model):
    __tablename__ = "files"
    id: db.Mapped[str] = db.mapped_column(db.String, primary_key=True)
    name: db.Mapped[str] = db.mapped_column(
        db.String, index=True, unique=True, nullable=False
    )
    type: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    size: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    icon: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    datetime: db.Mapped[dt] = db.mapped_column(db.DateTime, nullable=False)
    locked: db.Mapped[bool] = db.mapped_column(db.Boolean, nullable=False)
    realname: db.Mapped[str] = db.mapped_column(
        db.String, index=True, unique=True, nullable=False
    )
    number: db.Mapped[str] = db.mapped_column(db.String, nullable=False)
    lapse_count: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    duration: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)

    def delete(self):
        """Delete file in database."""
        db.session.delete(self)
        db.session.commit()
