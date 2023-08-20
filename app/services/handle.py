# import base64
from flask import render_template, jsonify


def handle_bad_request(e):
    return render_template("errors/400.html", code=400, message=e), 400


def handle_access_forbidden(e):
    return render_template("errors/403.html", code=403, message=e), 403


def handle_page_not_found(e):
    return render_template("errors/404.html", code=404, message=e), 404


def handle_internal_server_error(e):
    return render_template("errors/500.html", code=500, message=e), 500


def bad_gateway(e):
    return render_template("errors/502.html", code=502, message=e), 502


def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    return (
        jsonify(
            error={
                "errors": e.args,
                "code": 500,
                "message": str(e.args[0]),
                "meta": {"type": "exception"},
            }
        ),
        500,
    )