"""Motion functions."""

import configparser

import requests
from flask import abort
from flask import current_app as ca
from requests.adapters import HTTPAdapter

from ..helpers.utils import get_pid


def check_motion():
    return get_pid("motion") is not None


def get_motion() -> configparser.ConfigParser:
    """Get motion parameters."""
    try:
        rsp = requests.get(f"{ca.config['MOTION_URL']}/config/list")
        rsp.raise_for_status()
        return parse_ini(rsp.text())
    except (ValueError, requests.RequestException) as error:
        abort(422, str(error))


def set_motion(key, value) -> None:
    """set motion parameter."""
    try:
        rsp = requests.get(f"{ca.config['MOTION_URL']}/config/set?{key}={value}")
        rsp.raise_for_status()
    except (ValueError, requests.RequestException) as error:
        abort(422, str(error))


def write_motion() -> None:
    """set motion parameter."""
    try:
        rsp = requests.get(f"{ca.config['MOTION_URL']}/config/write")
        rsp.raise_for_status()
    except (ValueError, requests.RequestException) as error:
        abort(422, str(error))


def pause_motion() -> None:
    """set motion parameter."""
    try:
        rsp = requests.get(f"{ca.config['MOTION_URL']}/config/pause")
        rsp.raise_for_status()
    except (ValueError, requests.RequestException) as error:
        abort(422, str(error))


def start_motion() -> None:
    """set motion parameter."""
    try:
        rsp = requests.get(f"{ca.config['MOTION_URL']}/config/start")
        rsp.raise_for_status()
    except (ValueError, requests.RequestException) as error:
        abort(422, str(error))


def restart_motion() -> requests.Response:
    """set motion parameter."""
    try:
        rsp = requests.get(f"{ca.config['MOTION_URL']}/config/restart")
        rsp.raise_for_status()

        rsp = requests.get(
            f"{ca.config['MOTION_URL']}/config/list", HTTPAdapter(max_retries=10)
        )
        rsp.raise_for_status()
    except (ValueError, requests.RequestException) as error:
        abort(422, str(error))
    else:
        return parse_ini(rsp.text())


def parse_ini(raw_config: str) -> configparser.ConfigParser:
    """Parse motion file."""
    config = configparser.ConfigParser()
    config.read_string(raw_config)
    return config
