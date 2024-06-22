"""Motion functions."""

import configparser

import requests
from flask import current_app as ca
from requests.adapters import HTTPAdapter

from ..helpers.utils import get_pid


def check_motion():
    return get_pid("*/motion") == 0


def get_motion() -> configparser.ConfigParser:
    """Get motion parameters."""
    rsp_txt = get(f"{ca.config['MOTION_URL']}/config/list")
    return parse_ini(rsp_txt)


def set_motion(key: str, value: [str | bool | int | float]) -> None:
    """set motion parameter."""
    get(f"{ca.config['MOTION_URL']}/config/set?{key}={value}")


def write_motion() -> None:
    """set motion parameter."""
    get(f"{ca.config['MOTION_URL']}/config/write")


def pause_motion() -> None:
    """set motion parameter."""
    get(f"{ca.config['MOTION_URL']}/config/pause")


def start_motion() -> None:
    """set motion parameter."""
    get(f"{ca.config['MOTION_URL']}/config/start")


def restart_motion() -> requests.Response:
    """set motion parameter."""
    get(f"{ca.config['MOTION_URL']}/config/restart")
    rsp_text = get(
        f"{ca.config['MOTION_URL']}/config/list", HTTPAdapter(max_retries=10)
    )
    return parse_ini(rsp_text)


def get(url: str) -> str | None:
    """Get request."""
    try:
        rsp = requests.get(url)
        rsp.raise_for_status()
    except (ValueError, requests.RequestException) as error:
        raise MotionError(error) from error
    return rsp.text()


def parse_ini(raw_config: str) -> configparser.ConfigParser:
    """Parse motion file."""
    config = configparser.ConfigParser()
    config.read_string(raw_config)
    return config


class MotionError(Exception):
    """Error for Motion config."""
