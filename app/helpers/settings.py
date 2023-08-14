import hashlib
import os

from flask import current_app, json
from ..const import SCHEDULE_FIFOIN, SCHEDULE_FIFOOUT


class Settings:
    """Object fo settings."""

    def __init__(self):
        """Init object."""
        self.path_file = None
        self.users = []
        self.ubuttons = []

    def init_app(self, app=None, path_file=None):
        self.path_file = app.config["FILE_SETTINGS"] if app else path_file
        if not os.path.isfile(self.path_file):
            default_config = app.config["DEFAULT_INIT"]
            default_config.update(
                {
                    SCHEDULE_FIFOIN: app.raspiconfig.motion_pipe,
                    SCHEDULE_FIFOOUT: app.raspiconfig.control_file,
                }
            )

            for name, attr in default_config.items():
                setattr(self, name, attr)

            self._save()
        else:
            self._load()

        app.settings = self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._save()
        self._load()

    def refresh(self):
        try:
            self._load()
        except SettingsException as error:
            raise error

    def backup(self):
        try:
            self._save(path_file=f"{self.path_file}.backup")
        except SettingsException as error:
            raise SettingsException(
                f"Error to backup settings file ({error})"
            ) from error

    def restore(self):
        try:
            self._load(path_file=f"{self.path_file}.backup")
            self._save()
        except SettingsException as error:
            raise SettingsException(
                f"Error to restore settings file ({error})"
            ) from error

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
        self._save()

    def set_user(self, **kwargs):
        user_list = self.get_user(kwargs.get("user_id"))
        if user_list:
            self.users.remove(user_list)
        if user_list and kwargs["password"] == "":
            kwargs["password"] = user_list["password"]
        else:
            kwargs["password"] = self._hash_password(kwargs["password"])

        self.users.append(kwargs)
        self._save()

    @staticmethod
    def _hash_password(password: str) -> bool:
        salt = current_app.config["SECRET_KEY"]
        hashed = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return hashed.hex()

    def _save(self, path_file=None):
        """Save settings to json file."""
        path_file = path_file if path_file else self.path_file
        try:
            with open(path_file, "w") as f:
                json.dump(
                    self, f, default=lambda o: o.__dict__, sort_keys=True, indent=4
                )
                f.close()
        except Exception as error:
            raise SettingsException(f"Error to save settings file ({error})") from error

    def _load(self, path_file=None):
        """Load settings from json file."""
        path_file = path_file if path_file else self.path_file
        try:
            with open(path_file, "r") as f:
                settings = json.load(f)
            for name, attr in settings.items():
                setattr(self, name, attr)
        except Exception as error:
            raise SettingsException(f"Error to load settings file ({error})") from error


class SettingsException(Exception):
    """Exception for settings class."""

    pass
