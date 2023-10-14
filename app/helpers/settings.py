"""Settings class."""
from dataclasses import dataclass
from typing import Any

from .jsondb import JsonDB


@dataclass
class Settings(JsonDB):
    """Object fo settings."""

    def init_app(self, app=None, path_file=None) -> None:
        path = app.config["FILE_SETTINGS"] if app else path_file
        default = app.config["DEFAULT_INIT"]
        super().__init__(path, default)
        app.settings = self

    def has_username(self, name: str) -> bool:
        """User is exists."""
        for user in self.users:
            if user["name"] == name:
                return True
        return False

    def get_user(self, name: str) -> dict[str, Any] | None:
        """Return user infos."""
        for user in self.users:
            if user["name"] == name:
                return user

    def get_user_byid(self, id: int) -> dict[str, Any] | None:  # pylint: disable=W0622
        """Return user infos."""
        for user in self.users:
            if user["id"] == id:
                return user
