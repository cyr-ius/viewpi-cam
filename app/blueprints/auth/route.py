from flask import (
    Blueprint,
    request,
    flash,
    current_app,
    render_template,
    url_for,
    redirect,
    session,
    g,
)
from ...helpers.decorator import auth_required

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@bp.before_app_request
def before_app_request():
    if hasattr(current_app.settings, "users") and len(current_app.settings.users) == 0:
        session.clear()
    g.user = session.get("user_id")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST" and len(current_app.settings.users) == 0:
        if (pwd := request.form.get("password")) == request.form.get("password_2"):
            next = next if (next := request.form.get("next")) else url_for("main.index")
            state = current_app.settings.set_user(
                user_id=request.form["user_id"],
                password=pwd,
                rights=current_app.config["USERLEVEL_MAX"],
            )
            if state is True:
                return redirect(next)

        flash("User or password invalid.")

    register = len(current_app.settings.users) == 0
    return render_template(
        "login.html", register=register, next=request.args.get("next")
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    if not current_app.settings.users or len(current_app.settings.users) == 0:
        return redirect(url_for("auth.register", next=request.args.get("next")))
    if request.method == "POST":
        user = request.form.get("user_id")
        pwd = request.form.get("password")
        if current_app.settings.check_password(user, pwd):
            session.clear()
            session["user_id"] = user
            session["user_level"] = current_app.settings.get_user(user).get("rights")
            next = next if (next := request.form.get("next")) else url_for("main.index")
            return redirect(next)

        flash("User or password invalid.")

    return render_template("login.html")


@bp.route("/logout", methods=["GET", "POST"])
@auth_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))