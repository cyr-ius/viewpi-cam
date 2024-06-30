from http import HTTPStatus

import jwt
from flask import current_app as ca
from flask import redirect, render_template, request, url_for
from flask_assets import Environment
from flask_babel import Babel
from flask_login import LoginManager
from flask_restx import abort

from ..models.schema import Users
from .raspiconfig import RaspiConfig

assets = Environment()
babel = Babel()
login_manager = LoginManager()
raspiconfig = RaspiConfig()


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


@login_manager.user_loader
def load_user(user_id):
    return Users.query.filter_by(alternative_id=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    if request.blueprint == "api":
        abort(HTTPStatus.UNAUTHORIZED, "API token is incorrect.")
    return redirect(url_for("auth.login", next=request.path))


@login_manager.request_loader
def load_user_from_request(request):
    cam_token = request.args.get("cam_token")
    if cam_token and request.blueprint == "camera":
        user = Users.query.filter_by(id=0, cam_token=cam_token).first()
        if user:
            return user

    api_token = request.headers.get("X-API-KEY") or request.cookies.get("JWToken")
    if api_token and request.blueprint == "api":
        try:
            jwt_content = jwt.decode(
                api_token, ca.config["SECRET_KEY"], algorithms=["HS256"]
            )
        except (jwt.ImmatureSignatureError, jwt.ExpiredSignatureError):
            abort(422, "API token expired")
        except jwt.DecodeError:
            abort(401, "API token is incorrect.")

        user = Users.query.filter_by(id=0, name=jwt_content.get("iss")).first()
        if user:
            return user

    # finally, return None if both methods did not login the user
    return None
