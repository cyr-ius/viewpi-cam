from flask_wtf.form import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, validators, SubmitField


class frm_login(FlaskForm):
    user = StringField(label="Username", validators=[validators.DataRequired()])
    password = PasswordField(
        label="Password",
        validators=[validators.DataRequired()],
    )
    next = HiddenField()
    submit = SubmitField(label="Sign in", render_kw={"class": "btn btn-primary"})


class frm_register(frm_login):
    password_2 = PasswordField(
        label="Password",
        validators=[
            validators.DataRequired(),
            validators.EqualTo("password", message="Password must match"),
        ],
    )
