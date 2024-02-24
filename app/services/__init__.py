import os

from ..helpers.exceptions import ViewPiCamException
from ..helpers.utils import execute_cmd, get_locale, get_timezone
from .assets import css_custom, css_main, js_colors, js_custom, js_main, js_pipan
from .base import assets, babel, raspiconfig, settings, usrmgmt


def init_app(app):
    assets.init_app(app)
    babel.init_app(app, locale_selector=get_locale, timezone_selector=get_timezone)

    assets.register("css_custom", css_custom)
    assets.register("css_main", css_main)
    assets.register("js_custom", js_custom)
    assets.register("js_main", js_main)
    assets.register("js_pipan", js_pipan)
    assets.register("js_colors", js_colors)

    # !!! Important ordering !!!
    raspiconfig.init_app(app)
    settings.init_app(app)
    usrmgmt.init_app(app)

    # Custom log level
    if custom_level := settings.get("loglevel"):
        app.logger.setLevel(custom_level.upper())
    else:
        settings["loglevel"] = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Set timezone
    if offset := settings.get("gmt_offset"):
        try:
            execute_cmd(f"ln -sf /usr/share/zoneinfo/{offset} /etc/localtime")
        except ViewPiCamException as error:
            app.logger.error(error)
