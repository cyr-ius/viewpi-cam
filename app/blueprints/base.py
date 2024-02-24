from flask import redirect, render_template, request, session, url_for


def handle_bad_request(error):
    """Bad request."""
    return render_template("errors/400.html", code=400, message=error), 400


def handle_access_forbidden(error):
    """Access forbidden."""
    return render_template("errors/403.html", code=403, message=error), 403


def handle_page_not_found(error):
    """Page not found."""
    return render_template("errors/404.html", code=404, message=error), 404


def handle_internal_server_error(error):
    """Internal error."""
    return render_template("errors/500.html", code=500, message=error), 500


def handle_bad_gateway(error):
    """Bad gateway."""
    return render_template("errors/502.html", code=502, message=error), 502


def handle_unauthorized_access(error):
    session["next"] = request.script_root + request.path
    return redirect(url_for("auth.login"))
