"""Fifo helper."""

import os

from flask import current_app as ca

from .exceptions import ViewPiCamException
from .utils import execute_cmd, write_log


def open_pipe(pipename: str):
    """Open pipe."""
    if not os.path.exists(pipename):
        write_log(f"Making Pipe to receive capture commands {pipename}")
        execute_cmd(f"mkfifo {pipename}")
        execute_cmd(f"chmod 666 {pipename}")
    else:
        write_log(f"Capture Pipe already exists ({pipename})")

    try:
        pipe = os.open(pipename, os.O_RDONLY | os.O_NONBLOCK)
        return pipe
    except OSError as error:
        write_log(f"Error open pipe {pipename} {str(error)}")
    except ViewPiCamException as error:
        write_log(error)


def send_motion(cmd: str) -> None:
    """Send command to pipe."""
    try:
        pipe = os.open(ca.raspiconfig.motion_pipe, os.O_WRONLY | os.O_NONBLOCK)
        os.write(pipe, f"{cmd}\n".encode())
        os.close(pipe)
        write_log(f"Motion - Send {cmd}")
    except Exception as error:  # pylint: disable=W0718
        write_log(f"Motion - {error}")


def check_motion(pipe):
    """Read motion pipe."""
    if isinstance(pipe, bool):
        return ""
    try:
        ret = os.read(pipe, 1).decode("utf-8").replace("\n", "")
    except Exception:  # pylint: disable=W0718
        ret = ""
    return ret
