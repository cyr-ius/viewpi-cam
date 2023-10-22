"""Users class."""
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
            self._users = ca.settings.users.copy()
            self._users.remove(user)
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
        return self._user.get("totp", False) is True

    def set_secret(self) -> None:
        if self.totp is False:
            self._user["secret"] = pyotp.random_base32()
            self._saveset()

    def delete_secret(self) -> None:
        self._user.pop("totp", None)
        self._user.pop("secret", None)
        self._saveset()

    def validate_secret(self, code: str) -> bool:
        totp = pyotp.TOTP(self._user["secret"])
        self._user["totp"] = totp.verify(code)
        self._saveset()
        return self._user["totp"]

    def check_password(self, password: str) -> bool:
        hash_passsword = self._user["password"]
        return check_password_hash(hash_passsword, password)

    def check_totp(self, code: str) -> bool:
        totp = pyotp.TOTP(self._user["secret"])
        return totp.verify(code)

    def _saveset(self) -> None:
        self._users.append(self._user)
        ca.settings.update(users=self._users)

    @staticmethod
    def checkname(users, name) -> None:
        if len(users) > 0 and ca.settings.has_object(attr="users", id=name, key="name"):
            raise UserAlreadyExists("User name is already exists, please change.")

    @staticmethod
    def create(name: str, password: str, right: int, **kwargs: Any) -> None:
        users = ca.settings.get("users", [])
        User.checkname(users, name)
        ids = [user["id"] for user in users]
        kwargs["id"] = 1 if len(ids) == 0 else (max(ids) + 1)
        password = generate_password_hash(password)
        users.append({"name": name, "password": password, "right": right, **kwargs})
        ca.settings.update(users=users)
        return User(id=kwargs["id"])

    def update(self, **kwargs) -> None:
        kwargs.pop("id", None)
        if self.name != kwargs["name"]:
            User.checkname(self._users, kwargs["name"])

        if (pwd := kwargs.get("password")) is None or pwd == "":
            kwargs["password"] = self._user["password"]
        else:
            kwargs["password"] = generate_password_hash(pwd)

        self._user.update(kwargs)
        self._saveset()

        return kwargs

    def delete(self) -> None:
        ca.settings.update(users=self._users)


class UsersException(Exception):
    """Users Exception."""


class UserAlreadyExists(UsersException):
    """Users Exception."""


class UserNotFound(UsersException):
    """Users Exception."""
