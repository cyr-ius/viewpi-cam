"""Users class."""
from dataclasses import dataclass
from typing import Any

import pyotp
from flask import current_app as ca
from werkzeug.security import check_password_hash, generate_password_hash


@dataclass
class Usrmgmt:
    """Class Users."""

    users = {}

    @property
    def next_id(self) -> int:
        return 1 if len(self.users.keys()) == 0 else int(max(self.users.keys())) + 1

    def init_app(self, app):
        """Initialiaz app."""
        with app.app_context():
            self.load()
        app.usrmgmt = self

    def get_users(self) -> list:
        """Return users list."""
        return [user.__dict__ for user in self.users.values()]

    def get_user(self, id: int) -> dict[str, Any]:  # pylint: disable=W0622
        """Return user dictionary."""
        return self.users.get(id).__dict__

    def save(self) -> None:
        """Save to jsondb."""
        ca.settings.update(users=self.users)

    def load(self) -> None:
        """Load from jsondb and map to object."""
        for id, user in ca.settings.get("users", {}).items():  # pylint: disable=W0622
            self.users.update({int(id): User(**user)})

    def create(self, name: str, password: str, right: int, **kwargs: Any) -> None:
        """Create user."""
        kwargs.pop("id", None)
        self.checkname(name)
        hashpwd = generate_password_hash(password)
        user = User(self.next_id, name, hashpwd, int(right))
        for k, v in kwargs.items():
            setattr(user, k, v)
        self.users.update({user.id: user})
        self.save()
        return user

    def get(
        self, id: int = None, name: str = None  # pylint: disable=W0622
    ) -> object | None:
        """Get user object."""

        def search_name(name):
            for user in self.get_users():
                if user["name"] == name:
                    return self.users.get(user["id"])

        return self.users.get(id) or search_name(name)

    def delete(self, id: int) -> None:  # pylint: disable=W0622
        """Delete user."""
        self.users.pop(id)
        self.save()

    def checkname(self, name) -> None:
        """Check name exist."""
        for user in self.users.values():
            if user.name == name:
                raise UserNameExists("User name is already exists, please change.")


@dataclass
class User(Usrmgmt):
    """Class user."""

    id: int = None
    name: str = None
    hashpwd: str = None
    right: int = None
    secret: str = None
    totp: bool = False
    locale: str = "en"

    def set_secret(self) -> None:
        """Set otp code."""
        if self.totp is False:
            self.secret = pyotp.random_base32()
            self.users.update({self.id: self})
            self.save()

    def delete_secret(self) -> None:
        """Remove otp code."""
        del self.totp
        del self.secret
        self._saveset()

    def validate_secret(self, code: str) -> bool:
        """Validate otp code."""
        self.totp = self.check_totp(code)
        self._saveset()
        return self.totp

    def check_password(self, password: str) -> bool:
        """Check password."""
        return check_password_hash(self.hashpwd, password)

    def check_totp(self, code: str) -> bool:
        """Check otp code."""
        totp = pyotp.TOTP(self.secret)
        return totp.verify(code)

    def update(self, **kwargs) -> None:
        if (name := kwargs.get("name")) and self.name != name:
            self.checkname(kwargs["name"])
        if pwd := kwargs.pop("password", None):
            kwargs["hashpwd"] = generate_password_hash(pwd)
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._saveset()
        return self

    def _saveset(self) -> None:
        self.users.update({self.id: self})
        self.save()


class UsrmgmtException(Exception):
    """Usrmgmt Exception."""


class UserNameExists(Exception):
    """Users Exception."""
