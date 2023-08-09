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
from .form import frm_login, frm_register

bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")


@bp.before_app_request
def before_app_request():
    if not current_app.settings.users:
        g.first_run = True

    g.user = session.get("user_id")


@bp.route("/register", methods=["GET", "POST"])
def register():
    form = frm_register()
    if g.first_run and form.validate_on_submit():
        if (pwd := request.form.get("password")) == request.form.get("password_2"):
            current_app.settings.set_user(
                user_id=request.form["user_id"],
                password=pwd,
                rights=current_app.config["USERLEVEL_MAX"],
                force_pwd=True,
            )
            next = next if (next := request.form.get("next")) else url_for("main.index")
            return redirect(next)

        flash("User or password invalid.")
    return render_template("login.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = frm_login()
    if not current_app.settings.users:
        return redirect(url_for("auth.register", next=request.args.get("next")))
    if request.method == "POST":
        user = request.form.get("user_id")
        pwd = request.form.get("password")
        if current_app.settings.check_password(user, pwd):
            session.clear()
            session["user_id"] = user
            session["user_level"] = current_app.settings.get_user(user).rights
            next = next if (next := request.form.get("next")) else url_for("main.index")
            return redirect(next)

        flash("User or password invalid.")

    return render_template("login.html", form=form)


@bp.route("/logout", methods=["GET", "POST"])
@auth_required
def logout():
    session.clear()
    return redirect(url_for("main.index"))
