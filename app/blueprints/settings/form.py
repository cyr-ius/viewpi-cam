from flask_wtf.form import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    validators,
    SubmitField,
    SelectField,
    BooleanField,
    widgets,
    FormField,
    FieldList,
)
from ...helpers.widgets import ButtonWidget
from ...helpers.settings import User, Button


class frm_button(FlaskForm):
    name = StringField(
        label="Name",
        render_kw={"class": "form-control form-control-sm", "placeholder": "Name"},
        validators=[validators.DataRequired()],
    )
    macro = StringField(
        label="Macro",
        render_kw={"class": "form-control form-control-sm", "placeholder": "Macro"},
        validators=[validators.DataRequired()],
    )
    css_class = StringField(
        label="Class",
        render_kw={"class": "form-control form-control-sm", "placeholder": "class"},
    )
    style = StringField(
        label="Style",
        render_kw={"class": "form-control form-control-sm", "placeholder": "Style"},
    )
    other = StringField(
        label="Other",
        render_kw={"class": "form-control form-control-sm", "placeholder": "Other"},
    )
    del_button = StringField(
        label='<i class="bi bi-dash-square-fill"></i>',
        render_kw={"class": "btn btn-sm btn-danger", "onclick": "del_button(this);"},
        validators=[validators.Optional()],
        widget=ButtonWidget(),
    )
    add_button = StringField(
        label='<i class="bi bi-plus-square-fill"></i>',
        render_kw={"class": "btn btn-sm btn-success", "onclick": "add_button(this);"},
        validators=[validators.Optional()],
        widget=ButtonWidget(),
    )


class frm_user_buttons(FlaskForm):
    user_buttons = FieldList(FormField(frm_button, default=Button), min_entries=1)


class frm_user(FlaskForm):
    RIGHTS = [(0, "Minimum"), (1, "Minimum+"), (2, "Medium"), (4, "Max")]
    user_id = StringField(
        label="User",
        validators=[validators.DataRequired()],
        render_kw={
            "class": "form-control form-control-sm",
            "placeholder": "Username",
        },
        description="User",
    )
    password = PasswordField(
        label="Password",
        validators=[validators.Optional()],
        render_kw={
            "class": "form-control form-control-sm",
            "placeholder": "Password",
            "onlostfocus": "$('#form-settings').trigger('submit');",
        },
        description="Password",
    )
    rights = SelectField(
        choices=RIGHTS,
        validators=[validators.DataRequired()],
        render_kw={
            "class": "form-select form-select-sm",
            "onchange": "$('#form-settings').trigger('submit');",
        },
        coerce=int,
        default=0,
    )
    del_user = StringField(
        label='<i class="bi bi-dash-square-fill"></i>',
        render_kw={"class": "btn btn-sm btn-danger", "onclick": "del_user(this);"},
        widget=ButtonWidget(),
    )
    add_user = StringField(
        label='<i class="bi bi-plus-square-fill"></i>',
        render_kw={"class": "btn btn-sm btn-success", "onclick": "add_user(this);"},
        widget=ButtonWidget(),
    )


class frm_users(FlaskForm):
    users = FieldList(FormField(frm_user, default=lambda: User()), min_entries=1)


class frm_token(FlaskForm):
    token = StringField(label="Token", validators=[validators.Optional()])
    copy = SubmitField(
        label='<i class="bi bi-clipboard"></i>',
        render_kw={"class": "btn btn-sm btn-outline-secondary"},
        widget=ButtonWidget(),
    )
    generate = SubmitField(
        label="Generate",
        render_kw={"class": "btn btn-sm btn-outline-secondary"},
        widget=ButtonWidget(),
    )
    reset = SubmitField(
        label="Reset",
        render_kw={"class": "btn btn-sm btn-outline-secondary"},
        widget=ButtonWidget(),
    )


class frm_settings(FlaskForm):
    servo = BooleanField(
        label="Servo blaster",
        render_kw={
            "class": "form-check form-switch",
            "onchange": "this.form.submit();",
            "value": 1,
        },
        widget=widgets.CheckboxInput(),
    )
    pipan = BooleanField(
        label="Pi Pan",
        render_kw={
            "class": "form-check form-switch",
            "onchange": "this.form.submit();",
            "value": 1,
        },
        widget=widgets.CheckboxInput(),
    )
    pilight = BooleanField(
        label="Pi Light",
        render_kw={
            "class": "form-check form-switch",
            "onchange": "this.form.submit();",
            "value": 1,
        },
        widget=widgets.CheckboxInput(),
    )
    UPRESETS = ["v2", "N-IMX219", "P-IMX219", "N-IMX219", "P-IMX219"]
    upreset = SelectField(
        label="UPreset",
        validators=[validators.DataRequired()],
        render_kw={
            "class": "form-select form-select-sm",
            "onchange": "this.form.submit();",
        },
        choices=UPRESETS,
        default="v2",
    )
