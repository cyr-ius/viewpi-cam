"""Blueprint Authentication."""
import pyotp
from flask import Blueprint
from flask import current_app as ca
from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..const import USERLEVEL_MAX
from ..helpers.decorator import auth_required

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
            if (username := request.form["username"]) and password:
                first_user = {
                    "id": 1,
                    "name": username,
                    "password": generate_password_hash(password),
                    "rights": USERLEVEL_MAX,
                }
                ca.settings.update(users=[first_user])
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
        username = request.form.get("username")
        password = request.form.get("password")
        if (user := ca.settings.get_object(attr="users", id=username, key="name")) and (
            check_password_hash(user.get("password"), password)
        ):
            session.clear()
            next_page = (
                next_page
                if (next_page := request.form.get("next"))
                else url_for("main.index")
            )

            if user.get("totp"):
                return render_template("totp.html", next=next_page, id=user.get("id"))

            session["username"] = username
            session["level"] = user.get("rights")

            return redirect(next_page)

        flash("User or password invalid.")

    return render_template("login.html")


@bp.route("/totp-verified", methods=["GET", "POST"])
def totpverified():
    """Totop verified."""
    id = int(request.args.get("id"))  # pylint: disable=W0622
    next = request.args.get("next")  # pylint: disable=W0622
    if request.method == "POST":
        id = int(request.form.get("id"))
        next = request.form.get("next")
        if dict_user := ca.settings.get_object("users", id):
            totp = pyotp.TOTP(dict_user["secret"])
            if totp.verify(request.form.get("secret")):
                session["username"] = dict_user.get("name")
                session["level"] = dict_user.get("rights")
                return redirect(next)
            flash("Code invalid.")

    return render_template("totp.html", id=id, next=next)


@bp.route("/logout", methods=["GET", "POST"])
@auth_required
def logout():
    """Logout  button."""
    session.clear()
    return redirect(url_for("auth.login"))
