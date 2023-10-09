"""Blueprint Authentication."""
from flask import Blueprint
from flask import current_app as ca
from flask import flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..helpers.decorator import auth_required

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@bp.before_app_request
def before_app_request():
    """Execute before request."""
    if hasattr(ca.settings, "users") and len(ca.settings.users) == 0:
        session.clear()
    g.user = session.get("username")


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
                    "rights": ca.config["USERLEVEL_MAX"],
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
        if (user := ca.settings.get_user(username)) and (
            check_password_hash(user.get("password"), password)
        ):
            session.clear()
            session["username"] = username
            session["user_level"] = user.get("rights")
            next_page = (
                next_page
                if (next_page := request.form.get("next"))
                else url_for("main.index")
            )
            return redirect(next_page)

        flash("User or password invalid.")

    return render_template("login.html")


@bp.route("/logout", methods=["GET", "POST"])
@auth_required
def logout():
    """Logout  button."""
    session.clear()
    return redirect(url_for("auth.login"))
