"""Authentication decorators."""
from functools import wraps

import jwt
from flask import abort
from flask import current_app as ca
from flask import redirect, request, session, url_for

from ..const import USERLEVEL_MAX


def auth_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if session.get("username"):
            return function(*args, **kwargs)
        return redirect(url_for("auth.login", next=request.url))

    return wrapper


def role_required(rights: str | list[str]):
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
    @wraps(function)
    def wrapper(*args, **kwargs):
        if (btoken := session.get("bearer_token")) and jwt.decode(
            btoken, ca.config["SECRET_KEY"], algorithms=["HS256"]
        ):
            return function(*args, **kwargs)
        if (btoken := request.headers.get("X_API_KEY")) and jwt.decode(
            btoken, ca.config["SECRET_KEY"], algorithms=["HS256"]
        ):
            session["accept"] = True
            session["level"] = USERLEVEL_MAX
            return function(*args, **kwargs)
        abort(422, "Please provide an API token")

    return wrapper


def token_cam_accept(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if cam_token := request.args.get("cam_token"):
            if ca.settings.get("cam_token") == cam_token:
                return function.__wrapped__(*args, **kwargs)
            abort(403, "The provided Camera token is not valid")
        return function(*args, **kwargs)

    return wrapper
