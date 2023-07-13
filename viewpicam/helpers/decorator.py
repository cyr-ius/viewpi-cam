from functools import wraps
from flask import session, redirect, url_for
from .filer import get_settings


def auth_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if session.get("valid_access", False) is False or len(get_settings()) == 0:
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)

    return decorator
