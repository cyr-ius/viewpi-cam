from functools import wraps
from flask import redirect, url_for, request, g, current_app


def auth_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if (argtoken := request.args.get("token")) is not None:
            if argtoken != current_app.settings.get("token"):
                return redirect(url_for("auth.login", next=request.url))
        elif g.user is None:
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorator


class ViewPiCamException(Exception):
    """ViewPi Cam exception."""

    pass
