from functools import wraps
from flask import redirect, url_for, request, g


def auth_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorator


class ViewPiCamException(Exception):
    """ViewPi Cam exception."""

    pass
