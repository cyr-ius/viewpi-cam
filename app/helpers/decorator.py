"""Authentication decorators."""
from functools import wraps

import jwt
from flask import abort
from flask import current_app as ca
from flask import redirect, request, session, url_for

from ..const import USERLEVEL_MAX


def auth_required(function):
    """Authenticate decorator."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        if session.get("username"):
            return function(*args, **kwargs)
        return redirect(url_for("auth.login", next=request.url))

    return wrapper


def role_required(rights: str | list[str]):
    """Role decorator."""

    def decorate(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            listrights = [rights] if not isinstance(rights, list) else rights
            values = [
                ca.config["USERLEVEL"][item]
                for item in listrights
                if item in ca.config["USERLEVEL"].keys()
            ]
            if session.get("level") in values:
                return function(*args, **kwargs)
            abort(403, "Access is denied")

        return wrapper

    return decorate


def token_required(function):
    """Token decorator."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        token = session.get("bearer_token") or request.headers.get("Authorization")
        if token:
            try:
                content = jwt.decode(
                    token, ca.config["SECRET_KEY"], algorithms=["HS256"]
                )
            except (jwt.ImmatureSignatureError, jwt.ExpiredSignatureError):
                abort(422, "API token expired")
            else:
                if content.get("iis") == "system":
                    session["level"] = USERLEVEL_MAX
                return function(*args, **kwargs)
        abort(422, "Please provide an API token")

    return wrapper


def token_cam_accept(function):
    """Token camera decorator."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        if cam_token := request.args.get("cam_token"):
            if ca.settings.get("cam_token") == cam_token:
                return function.__wrapped__(*args, **kwargs)
            abort(403, "The provided Camera token is not valid")
        return function(*args, **kwargs)

    return wrapper
