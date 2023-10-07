"""Settings class."""
from dataclasses import dataclass

from .jsondb import JsonDB


@dataclass
class Settings(JsonDB):
    """Object fo settings."""

    def init_app(self, app=None, path_file=None) -> None:
        path = app.config["FILE_SETTINGS"] if app else path_file
        default = app.config["DEFAULT_INIT"]
        super().__init__(path, default)
        app.settings = self
