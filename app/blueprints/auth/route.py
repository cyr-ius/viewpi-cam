"""Blueprint Authentication."""
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.helpers.decorator import auth_required
from app.helpers.settings import SettingsException

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@bp.before_app_request
def before_app_request():
    """Execute before request."""
    if hasattr(current_app.settings, "users") and len(current_app.settings.users) == 0:
        session.clear()
    g.user = session.get("user_id")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Register page."""
    if request.method == "POST" and len(current_app.settings.users) == 0:
        if (pwd := request.form.get("password")) == request.form.get("password_2"):
            next_page = (
                next_page
                if (next_page := request.form.get("next"))
                else url_for("main.index")
            )
            try:
                current_app.settings.set_user(
                    user_id=request.form["user_id"],
                    password=pwd,
                    rights=current_app.config["USERLEVEL_MAX"],
                )
                return redirect(next_page)
            except SettingsException as error:
                current_app.logger.error(error)
                flash_msg = "Error while registering user (view log)"
        else:
            flash_msg = "User or password invalid."

        flash(flash_msg)

    has_registered = len(current_app.settings.users) == 0
    return render_template(
        "login.html", register=has_registered, next=request.args.get("next")
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if not current_app.settings.users or len(current_app.settings.users) == 0:
        return redirect(url_for("auth.register", next=request.args.get("next")))
    if request.method == "POST":
        user = request.form.get("user_id")
        pwd = request.form.get("password")
        if current_app.settings.check_password(user, pwd):
            session.clear()
            session["user_id"] = user
            session["user_level"] = current_app.settings.get_user(user).get("rights")
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
