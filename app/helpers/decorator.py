"""Authentication decorators."""
from functools import partial, wraps
from typing import overload

from flask import abort, current_app, redirect, request, session, url_for


@overload
def auth_required(func):
    ...


@overload
def auth_required(*, token_accept=False):
    ...


def auth_required(func=None, *, token_accept=False):
    def wrapper(func, *args, **kwargs):
        if session.get("username"):
            return func(*args, **kwargs)
        if token_accept is True and (token := request.args.get("token")):
            if token == current_app.settings.get("token"):
                return func(*args, **kwargs)
        return redirect(url_for("auth.login", next=request.url))

    # Without arguments `func` is passed directly to the decorator
    if func is not None:
        if not callable(func):
            raise TypeError("Not a callable. Did you use a non-keyword argument?")
        return wraps(func)(partial(wrapper, func))

    # With arguments, we need to return a function that accepts the function
    def decorator(func):
        return wraps(func)(partial(wrapper, func))

    return decorator


def token_required(function):
    @wraps(function)
    def decorator(*args, **kwargs):
        if session.get("username"):
            return function(*args, **kwargs)
        if api_key := request.headers.get("X_API_KEY"):
            if api_key == current_app.settings.get("token"):
                return function(*args, **kwargs)
            else:
                abort(403, "The provided API key is not valid")
        else:
            abort(422, "Please provide an API key")

    return decorator
