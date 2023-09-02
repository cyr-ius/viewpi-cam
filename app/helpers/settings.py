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
        for user in self.users:
            if user.get("user_id") == user_id:
                return True
        return False

    def check_password(self, user_id: str, password: str) -> bool:
        if self.has_user(user_id):
            salt = current_app.config["SECRET_KEY"]
            hashed = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return hashed.hex() == self.get_user(user_id).get("password")
        return False

    def get_user(self, user_id):
        for user in self.users:
            if user.get("user_id") == user_id:
                return user

    def del_user(self, user_id: str) -> None:
        user = self.get_user(user_id)
        self.users.remove(user)
        return self.update(users=self.users)

    def set_user(self, **kwargs):
        user_list = self.get_user(kwargs.get("user_id"))
        if user_list:
            self.users.remove(user_list)
        if user_list and kwargs["password"] == "":
            kwargs["password"] = user_list["password"]
        else:
            kwargs["password"] = self._hash_password(kwargs["password"])

        self.users.append(kwargs)
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

    pass
