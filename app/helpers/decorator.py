"""Authentication decorators."""

from functools import wraps

from flask import abort
from flask import current_app as ca
from flask_login import current_user


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
            if current_user and current_user.right in values:
                return function(*args, **kwargs)

            abort(401, "Access is denied")

        return wrapper

    return decorate
