"""Blueprint Authentication."""

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
from flask_login import login_required, login_user, logout_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from ..helpers.utils import reverse
from ..models import Users, db

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Register page."""
    users_count = db.session.execute(
        db.select(func.count("*")).select_from(Users)
    ).scalar()
    if request.method == "POST" and users_count == 1:
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

    has_registered = users_count == 1
    return render_template(
        "login.html", register=has_registered, next=request.args.get("next")
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    users_count = db.session.execute(
        db.select(func.count("*")).select_from(Users)
    ).scalar()

    if users_count == 1:
        return redirect(url_for("auth.register", next=request.args.get("next")))

    if request.method == "POST":
        next = request.form.get("next")
        if next and reverse(next) is False:
            abort(404)
        remember = request.form.get("remember") == "on"
        if (
            user := db.session.scalars(
                db.select(Users).filter_by(name=request.form.get("username"))
            ).first()
        ) and user.check_password(request.form.get("password")):
            if user.otp_confirmed:
                session["user_id"] = user.id
                return render_template(
                    "totp.html", next=next, remember=remember, id=user.id
                )
            login_user(user, remember=remember)
            return redirect(next or url_for("main.index"))
        flash(_("User or password invalid."))

    return render_template("login.html")


@bp.route("/totp-verified", methods=["GET", "POST"])
def totpverified():
    """Totop verified."""
    if request.method == "POST" and session.pop("user_id") == (
        id := int(request.form.get("id"))
    ):
        if (next := request.form("next")) and reverse(next) is False:
            abort(404)
        if (user := db.session.get(Users, id)) and user.check_otp_secret(
            request.form.get("secret")
        ):
            remember = request.form.get("remember")
            login_user(user, remember=remember)
            return redirect(next or url_for("main.index"))
        flash(_("OTP Code is invalid."))

    return render_template("totp.html", id=id, next=next, remember=remember)


@bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Logout button."""
    logout_user()

    return redirect(url_for("auth.login"))
