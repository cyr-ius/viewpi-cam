"""Blueprint Authentication."""

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask import current_app as ca
from flask_babel import lazy_gettext as _
from flask_login import login_required, login_user, logout_user
from werkzeug.security import generate_password_hash

from ..helpers.utils import reverse
from ..models import Users, db

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Register page."""
    if request.method == "POST" and Users.query.count() == 1:
        next = request.form.get("next")
        if next and reverse(next) is False:
            abort(404)

        if (password := request.form.get("password")) == request.form.get("password_2"):
            if (name := request.form["username"]) and password:
                user = Users(
                    name=name,
                    secret=generate_password_hash(password),
                    right=ca.config["USERLEVEL"]["max"],
                )
                user.create_user()

                return redirect(url_for("main.index", next=next))

            flash_msg = _("User or password is empty.")
        else:
            flash_msg = _("User or password invalid.")

        flash(flash_msg)

    has_registered = Users.query.count() == 1
    return render_template(
        "login.html", register=has_registered, next=request.args.get("next")
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if Users.query.count() == 1:
        return redirect(url_for("auth.register", next=request.args.get("next")))
    if request.method == "POST":
        next = request.form.get("next")
        if next and reverse(next) is False:
            abort(404)
        remember = request.form.get("remember") == "on"

        if (
            user := Users.query.filter_by(name=request.form.get("username"))
        ) and user.count() == 1:
            user = user.one()
            if user.check_password(request.form.get("password")):
                g.first_auth = True

                if user.otp_confirmed:
                    return render_template(
                        "totp.html", next=next, id=user.id, remember=remember
                    )

                login_user(user, remember=remember)
                response = make_response(redirect(next or url_for("main.index")))
                response.set_cookie(
                    "api_token",
                    value=user.generate_jwt(),
                    httponly=True,
                    samesite="strict",
                )

                return response

            flash(_("User or password invalid."))
        flash(_("User or password invalid."))

    return render_template("login.html")


@bp.route("/totp-verified", methods=["GET", "POST"])
def totpverified():
    """Totop verified."""
    if g.first_auth and request.method == "POST":
        id = int(request.form.get("id"))  # pylint: disable=W0622
        next = request.form.get("next")
        if next and reverse(next) is False:
            abort(404)

        if (user := db.get_or_404(Users, id)) and user.check_otp_secret(
            request.form.get("secret")
        ):
            login_user(user)
            response = make_response(redirect(next or url_for("main.index")))
            response.set_cookie(
                "api_token", value=user.generate_jwt(), httponly=True, samesite="strict"
            )
            return response
        flash(_("Access id denied."))

    return render_template("totp.html", id=id, next=next)


@bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Logout  button."""
    logout_user()
    response = make_response(redirect(url_for("auth.login")))
    response.set_cookie("api_token", "", expires=0)
    return response
