"""Class for raspimjpeg file."""
import os


class RaspiConfig:
    """Raspi config."""

    def __init__(self):
        """Init object."""
        self.path_file = None
        self.user_config = None

    def init_app(self, app=None, path_file=None):
        """Initialize application."""
        self.path_file = app.config["RASPI_CONFIG"] if app else path_file
        self._load()
        app.raspiconfig = self

    def refresh(self) -> None:
        """Reload configuration file."""
        try:
            self._load()
        except RaspiConfigError as error:
            raise error

    def _get_file_config(self, filename, config: dict[str, any] = None):
        config = {} if not config else config
        if os.path.isfile(filename):
            with open(filename, mode="r", encoding="utf-8") as file:
                for line in file.read().split("\n"):
                    if len(line) and line[0:1] != "#":
                        index = line.find(" ")
                        if index >= 0:
                            key = line[0:index]
                            value = line[index + 1 :]  # noqa: E203
                            if value == "true":
                                value = 1
                            if value == "false":
                                value = 0
                            config[key] = value
                        else:
                            config[line] = ""
                file.close()
        return config

    def _load(self) -> None:
        config_orig = self._get_file_config(self.path_file)
        self.user_config = config_orig.get("user_config", "")

        config = self._get_file_config(self.user_config, config_orig)
        if not isinstance(config, dict):
            raise RaspiConfigError("Raspi config, error loading")

        for key, value in config.items():
            setattr(self, key, value)

    def set_config(self, config: dict[str, any]) -> None:
        """Set raspimjpeg config."""
        lines = "#User config file\n"
        for key, value in config:
            lines += f"{key} {value}\n"

        with open(self.user_config, mode="w", encoding="utf-8") as file:
            file.write(lines)
            file.close()

        self._load()


class RaspiConfigError(Exception):
    """Error for Raspiconfig."""
