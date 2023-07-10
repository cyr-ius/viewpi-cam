from functools import wraps
from flask import session, redirect, url_for


def auth_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if session.get("valid_access", False) is False:
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)

    return decorator
