"""Settings class."""
from dataclasses import dataclass
from typing import Any

from .jsondb import JsonDB


@dataclass
class Settings(JsonDB):
    """Object for settings."""

    def init_app(self, app=None, path_file=None) -> None:
        path = app.config["FILE_SETTINGS"] if app else path_file
        default = app.config["DEFAULT_INIT"]
        super().__init__(path, default)
        app.settings = self

    def has_object(
        self, attr: str, id: int, key: str = "id"  # pylint: disable=W0622
    ) -> dict[str, Any] | None:
        """User is exists."""
        for item in getattr(self, attr, []):
            if item.get(key) == id:
                return True
        return False

    def get_object(
        self, attr: str, id: int, key: str = "id"  # pylint: disable=W0622
    ) -> dict[str, Any] | None:
        """Search for a dictionary key value \
            in an array of dictionaries and returns the identified dictionary."""
        for item in getattr(self, attr, []):
            if item.get(key) == id:
                return item
