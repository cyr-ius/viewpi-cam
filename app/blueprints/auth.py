"""Blueprint Authentication."""
from datetime import datetime as dt
from datetime import timezone

import jwt
import pyotp
from flask import Blueprint
from flask import current_app as ca
from flask import flash, redirect, render_template, request, session, url_for

from ..const import USERLEVEL_MAX
from ..helpers.decorator import auth_required
from ..helpers.users import User, UserNotFound

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@bp.before_app_request
def before_app_request():
    """Execute before request."""
    if hasattr(ca.settings, "users") and len(ca.settings.users) == 0:
        session.clear()


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Register page."""
    if request.method == "POST" and (
        ca.settings.get("users") is None or len(ca.settings.users) == 0
    ):
        if (password := request.form.get("password")) == request.form.get("password_2"):
            next_page = (
                next_page
                if (next_page := request.form.get("next"))
                else url_for("main.index")
            )
            if (name := request.form["username"]) and password:
                User.create(name=name, password=password, right=USERLEVEL_MAX)
                return redirect(next_page)
            flash_msg = "User or password is empty."
        else:
            flash_msg = "User or password invalid."

        flash(flash_msg)

    has_registered = ca.settings.get("users") is None or len(ca.settings.users) == 0
    return render_template(
        "login.html", register=has_registered, next=request.args.get("next")
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if ca.settings.get("users") is None or len(ca.settings.users) == 0:
        return redirect(url_for("auth.register", next=request.args.get("next")))
    if request.method == "POST":
        try:
            user = User(name=request.form.get("username"))
            if user.check_password(request.form.get("password")):
                session.clear()
                next_page = (
                    next_page
                    if (next_page := request.form.get("next"))
                    else url_for("main.index")
                )

                if user.totp:
                    session["totp"] = user.totp
                    return render_template("totp.html", next=next_page, id=user.id)

                session["username"] = user.name
                session["level"] = user.right
                session["bearer_token"] = _generate_jwt(user)

                return redirect(next_page)
            flash("User or password invalid.")
        except UserNotFound:
            flash("User or password invalid.")

    return render_template("login.html")


@bp.route("/totp-verified", methods=["GET", "POST"])
def totpverified():
    """Totop verified."""
    if session.get("totp") and request.method == "POST":
        id = int(request.form.get("id"))  # pylint: disable=W0622
        next = request.form.get("next")  # pylint: disable=W0622
        try:
            user = User(id=id)
            totp = pyotp.TOTP(user.secret)
            if totp.verify(request.form.get("secret")):
                session["username"] = user.name
                session["level"] = user.right
                session["bearer_token"] = _generate_jwt(user)
                return redirect(next)
        except UserNotFound:
            pass

    flash("Acccess id denied.")

    return render_template("totp.html", id=id, next=next)


@bp.route("/logout", methods=["GET", "POST"])
@auth_required
def logout():
    """Logout  button."""
    session.clear()
    return redirect(url_for("auth.login"))


def _generate_jwt(user):
    lifetime = dt.now(tz=timezone.utc) + ca.config["PERMANENT_SESSION_LIFETIME"]
    return jwt.encode(
        {
            "iis": user.name,
            "id": user.id,
            "iat": dt.now(tz=timezone.utc),
            "exp": lifetime,
        },
        ca.config["SECRET_KEY"],
        algorithm="HS256",
    )
