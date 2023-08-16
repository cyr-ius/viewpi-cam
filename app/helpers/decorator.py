from functools import wraps
from flask import redirect, url_for, request, g, current_app


def auth_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = current_app.settings.get("token")
        url_token = request.args.get("token")
        if g.user is None and (token != url_token):
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorator


class ViewPiCamException(Exception):
    """ViewPi Cam exception."""

    pass
