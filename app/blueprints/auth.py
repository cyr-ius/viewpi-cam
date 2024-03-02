"""Blueprint Authentication."""

from datetime import datetime as dt
from datetime import timezone

import jwt
import pyotp
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask import current_app as ca
from flask_babel import lazy_gettext as _
from werkzeug.security import check_password_hash, generate_password_hash

from ..helpers.decorator import auth_required
from ..helpers.utils import reverse
from ..models import Users, db

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@bp.before_app_request
def before_app_request():
    """Execute before request."""
    if Users.query.count() == 0:
        session.clear()


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Register page."""
    if request.method == "POST" and Users.query.count() == 0:
        if (password := request.form.get("password")) == request.form.get("password_2"):
            next_page = (
                next_page
                if (next_page := request.form.get("next"))
                else url_for("main.index")
            )
            if (name := request.form["username"]) and password:
                user = Users(
                    name=name,
                    secret=generate_password_hash(password),
                    right=ca.config["USERLEVEL"]["max"],
                )
                db.session.add(user)
                db.session.commit()
                if reverse(next_page) is False:
                    abort(404)
                return redirect(next_page)
            flash_msg = _("User or password is empty.")
        else:
            flash_msg = _("User or password invalid.")

        flash(flash_msg)

    has_registered = Users.query.count() == 0
    return render_template(
        "login.html", register=has_registered, next=request.args.get("next")
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if Users.query.count() == 0:
        return redirect(url_for("auth.register", next=request.args.get("next")))
    if request.method == "POST":
        if (
            user := Users.query.filter_by(name=request.form.get("username"))
        ) and user.count() == 1:
            user = user.one()
            if check_password_hash(user.secret, request.form.get("password")):
                ca.logger.debug("Password is correct")
                session.clear()
                next_page = (
                    next_page
                    if (next_page := request.form.get("next"))
                    else url_for("main.index")
                )

                if user.totp:
                    session["totp"] = user.totp
                    return render_template("totp.html", next=next_page, id=user.id)

                _load_session(user)

                if reverse(next_page) is False:
                    abort(404)

                return redirect(next_page)
            flash(_("User or password invalid."))
        flash(_("User or password invalid."))

    return render_template("login.html")


@bp.route("/totp-verified", methods=["GET", "POST"])
def totpverified():
    """Totop verified."""
    if session.get("totp") and request.method == "POST":
        id = int(request.form.get("id"))  # pylint: disable=W0622
        next_page = request.form.get("next")
        if user := db.get_or_404(Users, id):
            totp = pyotp.TOTP(user.secret)
            if totp.verify(request.form.get("secret")):
                _load_session(user)
                if reverse(next_page) is False:
                    abort(404)
                return redirect(next_page)
    flash(_("Access id denied."))

    return render_template("totp.html", id=id, next=next)


@bp.route("/logout", methods=["GET", "POST"])
@auth_required
def logout():
    """Logout  button."""
    session.clear()
    return redirect(url_for("auth.login"))


def _generate_jwt(user: Users) -> str:
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


def _load_session(user: Users) -> None:
    """Load session object."""
    session["id"] = user.id
    session["username"] = user.name
    session["level"] = user.right
    session["locale"] = user.locale
    session["bearer_token"] = _generate_jwt(user)
