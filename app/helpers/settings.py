"""Settings class."""
import hashlib
from dataclasses import dataclass

from flask import current_app

from .jsondb import JsonDB


@dataclass
class Settings(JsonDB):
    """Object fo settings."""

    def init_app(self, app=None, path_file=None):
        path = app.config["FILE_SETTINGS"] if app else path_file
        default = app.config["DEFAULT_INIT"]
        super().__init__(path, default)
        app.settings = self

    def has_user(self, user_id):
        """Return user exist."""
        return self.users.get(user_id) is not None

    def check_password(self, user_id: str, password: str) -> bool:
        if self.has_user(user_id):
            salt = current_app.config["SECRET_KEY"]
            hashed = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return hashed.hex() == self.get_user(user_id).get("password")
        return False

    def get_user(self, user_id: str) -> dict[str, any]:
        """Return user infos."""
        return self.users.get(user_id)

    def del_user(self, user_id: str) -> None:
        """Delete user."""
        self.users.pop(user_id, None)
        return self.update(users=self.users)

    def set_user(self, **kwargs):
        """Set user."""
        uid = kwargs.pop("user_id", None)
        if self.users.get(uid) is not None and kwargs["password"] == "":
            kwargs["password"] = self.users.get(uid)["password"]
        else:
            kwargs["password"] = self._hash_password(kwargs["password"])
        self.users.update({uid: kwargs})
        return self.update(users=self.users)

    @staticmethod
    def _hash_password(password: str) -> bool:
        salt = current_app.config["SECRET_KEY"]
        hashed = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return hashed.hex()


class SettingsException(Exception):
    """Exception for settings class."""
