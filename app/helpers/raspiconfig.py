import os


class RaspiConfig:
    """Raspi config."""

    def __init__(self):
        """Init object."""
        self.path_file = None

    def init_app(self, app=None, path_file=None):
        self.path_file = app.config["CONFIG_FILE1"] if app else path_file
        self._load()
        app.raspiconfig = self

    def refresh(self) -> None:
        try:
            self._load()
        except RaspiConfigError as error:
            raise error

    def _get_file_config(self, filename, config: dict[str, any] = None):
        config = {} if not config else config
        if os.path.isfile(filename):
            with open(filename, "r") as f:
                for line in f.read().split("\n"):
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
                f.close()
        return config

    def _load(self) -> None:
        config_orig = self._get_file_config(self.path_file)
        config = self._get_file_config(config_orig["user_config"], config_orig)
        if not isinstance(config, dict):
            raise RaspiConfigError("Raspi config, error loading")
        for k, v in config.items():
            setattr(self, k, v)

    def set_config(self, config: dict[str, any]) -> None:
        """Set raspimjpeg config."""
        lines = "#User config file\n"
        for k, v in config:
            lines += f"{k} {v}\n"

        with open(self.user_config, "w") as f:
            f.write(lines)
            f.close()

        self._load()


class RaspiConfigError(Exception):
    """Error for Raspiconfig."""

    pass
