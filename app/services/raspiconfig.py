"""Class for raspimjpeg file."""

import os
import time
from subprocess import Popen
from typing import Any

from ..helpers.exceptions import ViewPiCamException
from ..helpers.utils import execute_cmd, write_log


# pylint: disable=E1101
class RaspiConfig:
    """Raspi config."""

    def __init__(self):
        """Init object."""
        self.path_file = None
        self.user_config = None
        self.raspi_config = None
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

    def _get_file_config(
        self, filename: str, config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        config = {} if not config else config
        if os.path.isfile(filename):
            with open(filename, encoding="utf-8") as file:
                for line in file.read().split("\n"):
                    if len(line) and line[0:1] != "#":
                        index = line.find(" ")
                        if index >= 0:
                            key = line[0:index]
                            value = line[index + 1 :]  # noqa: E203
                            config[key] = value
                            if value == "true":
                                config[key] = 1
                            if value == "false":
                                config[key] = 0
                        else:
                            config[line] = ""
                file.close()
        return config

    def _load(self) -> None:
        config_orig = self._get_file_config(self.path_file)
        self.user_config = config_orig.get("user_config", "")

        self.raspi_config = self._get_file_config(self.user_config, config_orig)
        if not isinstance(self.raspi_config, dict):
            raise RaspiConfigError("Raspi config, error loading")

        for key, value in self.raspi_config.items():
            setattr(self, key, value)

        self._generate_folder()

    def _generate_folder(self) -> None:
        """Create files & folders."""
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.control_file), exist_ok=True)
        os.makedirs(self.media_path, exist_ok=True)
        os.makedirs(self.macros_path, exist_ok=True)
        os.makedirs(self.boxing_path, exist_ok=True)

    def set_config(self, config: dict[str, Any]) -> None:
        """Set raspimjpeg config."""
        user_config = self._get_file_config(self.user_config)
        user_config.update(**config)
        lines = "#User config file\n"
        for key, value in user_config.items():
            lines += f"{key} {value}\n"

        with open(self.user_config, mode="w", encoding="utf-8") as file:
            file.write(lines)
            file.close()

        self._load()

    def start(self) -> None:
        """Execute binary file."""
        if os.path.isfile(self.bin):
            # Create FIFO
            try:
                if not os.path.exists(self.control_file):
                    os.mkfifo(self.control_file, mode=0o600)
                if not os.path.exists(self.motion_pipe):
                    os.mkfifo(self.motion_pipe, mode=0o600)
            except Exception as error:
                raise RaspiConfigError(
                    f"Error while fifo creating ({error})"
                ) from error

            # Create /dev/shm/mjpeg/status_mjpeg
            if not os.path.isfile(self.status_file):
                try:
                    execute_cmd(f"touch {self.status_file}")
                except ViewPiCamException:
                    self.logging.error("Error: touch status file")

            # Execute binary
            Popen(self.bin)
        else:
            self.logging.error(f"Error: File not found ({self.bin})")

    def send(self, cmd: str) -> None:
        """Send command to pipe."""
        try:
            pipe = os.open(self.control_file, os.O_WRONLY | os.O_NONBLOCK)
            os.write(pipe, f"{cmd}\n".encode())
            os.close(pipe)
            write_log(f"Control - Send {cmd}")
        except Exception as error:  # pylint: disable=W0718
            write_log(f"[Raspiconfig] {error}", "error")
            raise RaspiConfigError(error) from error
        finally:
            os.sync()
            time.sleep(0.1)
            self.refresh()

    def stop(self) -> None:
        """Kill raspimjpeg."""
        try:
            execute_cmd("killall raspimjpeg")
        except ViewPiCamException as error:
            self.logging.error(error)


class RaspiConfigError(Exception):
    """Error for Raspiconfig."""
