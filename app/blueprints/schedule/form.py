from flask_wtf.form import FlaskForm
from wtforms import (
    SelectField,
    StringField,
    IntegerField,
    FloatField,
    BooleanField,
)
from wtforms.validators import Optional, NumberRange
from wtforms.widgets import CheckboxInput


class frm_schedule(FlaskForm):
    DAYMODE = {"1": "All Days", "0": "Sun bases", "2": "Fixed Times"}
    fifo_in = StringField(label="Fifo in")
    fifo_out = StringField(label="Fifo out")
    autocamera_interval = IntegerField(label="Autocamera interval")
    autocapture_interval = IntegerField(label="Autocapture interval")
    cmd_poll = IntegerField(label="CMD Poll")
    dawnstart_minutes = IntegerField(label="Dawn start")
    daymode = SelectField(label="Day mode", choices=DAYMODE, default="1")
    daystart_minutes = IntegerField(label="Day start")
    duskend_minutes = IntegerField(label="Dusk end")
    purgevideo_hours = IntegerField(label="Purge video")
    gmt_offset = StringField(label="GMT Offset")
    latitude = FloatField(label="Latittude")
    longitude = FloatField(label="Longitude")
    management_command = StringField(label="Mgmt command")
    management_interval = IntegerField(label="Mgmt interval")
    max_capture = IntegerField(label="Max captures")
    mode_poll = IntegerField(label="Mode poll")
    purgeimage_hours = IntegerField(label="Purge image")
    purgelapse_hours = IntegerField(label="Purge elapse", validators=[Optional()])
    purgespace_level = IntegerField(
        label="Purge space level",
        validators=[Optional(), NumberRange(min=1, max=65535)],
    )
    purgespace_modeex = SelectField(label="Purge mode")


class frm_days_mode(FlaskForm):
    commands_on = []
    commands_off = []
    days = []
    for j in range(0, 14):
        days.insert(j, [])
        for i in range(0, 7):
            days[j].insert(i, BooleanField(widget=CheckboxInput()))
        commands_on.insert(j, StringField())
        commands_off.insert(j, StringField())
