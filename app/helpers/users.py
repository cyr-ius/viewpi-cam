"""Users class."""
import random
from typing import Any

import pyotp
from flask import current_app as ca
from werkzeug.security import check_password_hash, generate_password_hash


class User:
    """Class user."""

    def __init__(self, id: int = None, name: str = None):  # pylint: disable=W0622
        """Initialize."""
        if user := (
            ca.settings.get_object("users", id)
            or ca.settings.get_object("users", name, "name")
        ):
            self._user = user
        else:
            raise UserNotFound("User not found.")

    @property
    def id(self):
        return self._user.get("id")

    @property
    def name(self):
        return self._user.get("name")

    @property
    def right(self):
        return self._user.get("right")

    @property
    def token(self):
        return self._user.get("token")

    @property
    def secret(self):
        return self._user.get("secret")

    @property
    def totp(self):
        return self._user.get("totp") is True

    def set_token(self) -> None:
        ca.settings.users.remove(self._user)
        self._user["token"] = f"B{random.getrandbits(256)}"
        ca.settings.users.append(self._user)
        ca.settings.update(users=ca.settings.users)

    def set_secret(self) -> None:
        ca.settings.users.remove(self._user)
        self._user["secret"] = pyotp.random_base32()
        self._user["totp"] = False
        ca.settings.users.append(self._user)
        ca.settings.update(users=ca.settings.users)

    def delete_secret(self) -> None:
        ca.settings.users.remove(self._user)
        self._user.pop("totp", None)
        self._user.pop("secret", None)
        ca.settings.users.append(self._user)
        ca.settings.update(users=ca.settings.users)

    def validate_secret(self, code: str) -> bool:
        totp = pyotp.TOTP(self._user["secret"])
        ca.settings.users.remove(self._user)
        self._user["totp"] = totp.verify(code)
        ca.settings.users.append(self._user)
        ca.settings.update(users=ca.settings.users)

        return self._user["totp"]

    def check_password(self, password: str) -> bool:
        hash_passsword = self._user["password"]
        return check_password_hash(hash_passsword, password)

    def check_totp(self, code: str) -> bool:
        totp = pyotp.TOTP(self._user["secret"])
        return totp.verify(code)

    def set_password(self, password: str) -> None:
        ca.settings.users.remove(self._user)
        self._user["password"] = generate_password_hash(password)
        ca.settings.users.append(self._user)
        ca.settings.update(users=ca.settings.users)

    def set_right(self, right: int) -> None:
        ca.settings.users.remove(self._user)
        self._user["right"] = right
        ca.settings.users.append(self._user)
        ca.settings.update(users=ca.settings.users)

    def refresh(self) -> None:
        self._user = ca.settings.get_object("users", self.id)

    def update(self, **kwargs) -> None:
        if self.name != kwargs["name"] and ca.settings.has_object(
            attr="users", id=kwargs["name"], key="name"
        ):
            raise UserAlreadyExists("User name is already exists, please change.")

        kwargs["id"] = self.id
        if (pwd := kwargs.get("password")) is None:
            kwargs["password"] = self._user["password"]
        else:
            kwargs["password"] = generate_password_hash(pwd)

        ca.settings.users.remove(self._user)
        ca.settings.users.append(kwargs)
        ca.settings.update(users=ca.settings.users)

        return kwargs


class Users:
    """Class users."""

    def set(self, name: str, password: str, right: int, **kwargs: Any) -> None:
        """Create user."""
        users = ca.settings.get("users", [])
        if len(users) == 0:
            ca.settings.users = []
        if ca.settings.has_object(attr="users", id=name, key="name"):
            raise UserAlreadyExists("User name is already exists, please change.")
        ids = [user["id"] for user in users]
        kwargs["id"] = 1 if len(ids) == 0 else (max(ids) + 1)
        ca.settings.users.append({"name": name, "right": right, **kwargs})
        ca.settings.update(users=ca.settings.users)
        user = User(kwargs["id"])
        user.set_password(password)

        return user

    def delete(self, id: int) -> bool:  # pylint: disable=W0622
        """Delete user."""
        if user := ca.settings.get_object("users", id):
            ca.settings.users.remove(user)
            ca.settings.update(users=ca.settings.users)
        else:
            raise UsersException("User not found.")


class UsersException(Exception):
    """Users Exception."""


class UserAlreadyExists(UsersException):
    """Users Exception."""


class UserNotFound(UsersException):
    """Users Exception."""
