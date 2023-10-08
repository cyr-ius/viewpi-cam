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

    def has_username(self, username: str) -> bool:
        """User is exists."""
        for user in self.users:
            if user["name"] == username:
                return True
        return False

    def get_user(self, username: str) -> dict[str, Any] | None:
        """Return user infos."""
        for user in self.users:
            if user["name"] == username:
                return user
