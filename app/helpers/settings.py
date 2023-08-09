import hashlib
import os
from abc import ABC

from flask import current_app, json

from ..const import SCHEDULE_FIFOIN, SCHEDULE_FIFOOUT


class Settings:
    """Object fo settings."""

    def __init__(self):
        """Init object."""
        self.path_file = None
        self.bk_config = f"{self.path_file}.backup"
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

            self._save_settings()
        else:
            self._get_settings()

        app.settings = self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._save_settings()

    def refresh(self):
        self._get_settings()

    def backup(self):
        self._save_settings(path_file=self.bk_config)

    def restore(self):
        self._get_settings(path_file=self.bk_config)
        self._save_settings()

    def save(self):
        self._save_settings()

    @property
    def data(self):
        return self.__dict__

    def has_user(self, user_id):
        for user in self.users:
            if user.user_id == user_id:
                return True
        return False

    def check_password(self, user_id: str, password: str) -> bool:
        if self.has_user(user_id):
            salt = current_app.config["SECRET_KEY"]
            hashed = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return hashed.hex() == self.get_user(user_id).password
        return False

    def get_user(self, user_id, return_index=False):
        for idx, user in enumerate(self.users):
            if user.user_id == user_id:
                return idx if return_index else user

    def del_user(self, user_id: str) -> None:
        user = self.get_user(user_id)
        self.users.remove(user)

    def set_user(self, **kwargs):
        if idx := self.get_user(kwargs.get("user_id"), True):
            self.users.pop(idx)

        user = User(kwargs)
        self.users.append(user.__dict__)
        self._save_settings()
        self._get_settings()

    def _save_settings(self, path_file=None):
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

    def _get_settings(self, path_file=None):
        """Load settings from json file."""
        path_file = path_file if path_file else self.path_file
        try:
            with open(path_file, "r") as f:
                settings = json.load(f)

            for name, attr in settings.items():
                if name in ("users", "ubuttons"):
                    attr = [User(item) for item in attr]
                setattr(self, name, attr)
        except Exception as error:
            raise SettingsException(f"Error to load settings file ({error})") from error


class MetaObject(ABC):
    """Meta object for settings."""

    def __init__(self, data_dict: dict[str, any] = None):
        """Init."""
        if isinstance(data_dict, dict):
            for k, v in data_dict.items():
                setattr(self, k, v)


class Button(MetaObject):
    """Button class."""


class User(MetaObject):
    """User class."""

    def __init__(self, user: dict[str, any] = None):
        """Initialize."""
        if user and (pwd := user.get("password")) and user.pop("force_pwd", False):
            user["password"] = self._hash_password(pwd)
        super().__init__(user)

    def __setattr__(self, __name, __value):
        """Set attribut."""
        if __name == "password" and __value == "":
            __value = getattr(self, "password", __value)
        self.__dict__[__name] = __value

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
