from ..helpers.utils import get_locale, get_timezone
from .assets import css_custom, css_main, js_colors, js_custom, js_main, js_pipan
from .base import assets, babel, raspiconfig


def init_app(app):
    assets.init_app(app)
    babel.init_app(app, locale_selector=get_locale, timezone_selector=get_timezone)
    raspiconfig.init_app(app)

    assets.register("css_custom", css_custom)
    assets.register("css_main", css_main)
    assets.register("js_custom", js_custom)
    assets.register("js_main", js_main)
    assets.register("js_pipan", js_pipan)
    assets.register("js_colors", js_colors)
