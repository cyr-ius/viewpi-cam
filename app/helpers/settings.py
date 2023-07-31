from typing import Any
from flask import current_app, json
from .filer import get_file_config, file_exists
from ..const import SCHEDULE_FIFOIN, SCHEDULE_FIFOOUT
import hashlib


class Settings:
    """Object fo settings."""

    def __init__(self):
        """Init object."""
        self.path_file = None
        self.users = []

    def init_app(self, app=None, path_file=None):
        self.path_file = app.config["FILE_SETTINGS"] if app else path_file
        if not file_exists(self.path_file):
            raspi_config_orig = get_file_config({}, app.config["CONFIG_FILE1"])
            config = get_file_config(
                raspi_config_orig, raspi_config_orig["user_config"]
            )

            default_config = app.config["DEFAULT_INIT"]
            default_config.update(
                {
                    SCHEDULE_FIFOIN: config["motion_pipe"],
                    SCHEDULE_FIFOOUT: config["control_file"],
                }
            )
            self._save_settings(**default_config)

        self._get_settings()

    @property
    def data(self):
        data = self.__dict__.copy()
        users = []
        for user in self._users:
            users.append(user.__dict__)
        data["users"] = users

        return self.__dict__

    def dict_users(self, users_dict):
        users = []
        for k, v in users_dict.items():
            users.append({"user_id": k, **v})
        return users

    def get(self, key, default=None):
        """Return value from settings."""
        return self._get_settings().get(key, default)

    def set(self, **kwargs):
        data = {}
        settings = self._get_settings()
        for k, v in kwargs.items():
            if "days[" in k:
                index = int(k.replace("days[", "").replace("][]", ""))
                settings.setdefault("days", {}).update({index: data.getlist(k)})
            elif "[]" in k:
                settings.update({k.replace("[]", ""): data.getlist(k)})
            elif k is not None:
                settings.update({k: v})
            else:
                settings.pop(k)

        self._save_settings(**settings)

    def has_user(self, user_id):
        for user in self.users:
            if user.get("user_id") == user_id:
                return True
        return False

    def get_user(self, user_id):
        for user in self.users:
            if user.get("user_id") == user_id:
                return user
        return {}

    def set_user(self, user_id, **kwargs):
        users = self.users
        kwargs["user_id"] = user_id
        if (pwd := kwargs.get("password")) and pwd != "":
            kwargs["password"] = self._hash_password(pwd)
        else:
            kwargs.pop("password", None)

        if self.has_user(user_id):
            user = self.get_user(user_id)
            users.remove(user)
            user.update(kwargs)
            kwargs = user

        users.append(kwargs)
        self.users = users

    def del_user(self, user_id):
        users = self.users
        if self.has_user(user_id):
            user = self.get_user(user_id)
            users.remove(user)
        self.users = users

    def save(self):
        self._save_settings(**self.data)

    def _save_settings(self, **kwargs):
        """Save settings to  json."""
        with open(self.path_file, "w") as f:
            json.dump(kwargs, f)
            f.close()

    def _get_settings(self):
        with open(self.path_file, "r") as f:
            settings = json.load(f)

        for name, attr in settings.items():
            setattr(self, name, attr)
        return settings

    @property
    def users(self):
        return self._users

    @users.getter
    def users(self):
        return [User(user) for user in self._users]

    @users.setter
    def users(self, value):
        self.__dict__["users"] = value
        self._users = value


class User:
    def __init__(self, user=None):
        """Init."""
        if isinstance(user, dict):
            for k, v in user.items():
                setattr(self, k, v)

    def __setattr__(self, __name: str, __value: Any) -> None:
        """Set attribut."""
        if __name == "password" and __value != "":
            __value = self._hash_password(__value)
        self.__dict__[__name] = __value

    def _hash_password(self, password: str) -> bool:
        salt = current_app.config["SECRET_KEY"]
        hashed = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return hashed.hex()

    def check_password(self, user_id: str, password: str) -> bool:
        if self.has_user(user_id):
            salt = current_app.config["SECRET_KEY"]
            hashed = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return hashed.hex() == self.get_user(user_id).get("password")
        return False


class Button:
    pass
