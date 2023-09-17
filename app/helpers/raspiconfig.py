"""Class for raspimjpeg file."""
import os
import stat
import time
from subprocess import Popen


# pylint: disable=E1101
class RaspiConfig:
    """Raspi config."""

    def __init__(self):
        """Init object."""
        self.path_file = None
        self.user_config = None
        self.logging = None
        self.bin = None

    def init_app(self, app=None, path_file=None):
        """Initialize application."""
        self.path_file = app.config["RASPI_CONFIG"] if app else path_file
        self.bin = app.config.get("RASPI_BINARY", "raspimjpeg")
        self.logging = app.logger
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

    def run(self) -> None:
        """Execute binary file."""
        if os.path.isfile(self.bin):
            # Create FIFO
            if not os.path.isfile(self.control_file):
                os.mkfifo(self.control_file, mode=0o600)
            if not os.path.isfile(self.motion_pipe):
                os.mkfifo(self.motion_pipe, mode=0o600)
            # Execute binary
            Popen(self.bin)
            self.logging.info("Start raspimjpeg")
        else:
            self.logging.error(f"Error: File not found ({self.bin})")

    def send(self, cmd: str) -> None:
        """Send command to pipe."""
        try:
            pipe = os.open(self.motion_pipe, os.O_WRONLY | os.O_NONBLOCK)
            os.write(pipe, f"{cmd}\n".encode("utf-8"))
            os.close(pipe)
            msg = {"type": "success", "message": f"Send {cmd} successful"}
        except Exception as error:  # pylint: disable=W0718
            msg = {"type": "error", "message": f"{error}"}
        finally:
            os.sync()
            time.sleep(0.1)
            self.refresh()

        return msg


class RaspiConfigError(Exception):
    """Error for Raspiconfig."""
