from flask_assets import Bundle, Filter
from webassets.filter import get_filter
import re


class ConcatFilter(Filter):
    """Filter that merges files, placing a semicolon between them.

    Fixes issues caused by missing semicolons at end of JS assets, for example
    with last statement of jquery.pjax.js.
    """

    def concat(self, out, hunks, **kw):
        out.write(";".join([h.data() for h, info in hunks]))


bs_icons = (
    get_filter(
        "cssrewrite",
        replace=lambda url: re.sub(
            r"./fonts/",
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/fonts/",
            url,
        ),
    ),
)

css_main = Bundle(
    "https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,600,700,300italic,400italic,600italic",
    "https://fonts.googleapis.com/css?family=Roboto+Mono:400,300,700",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
    Bundle(
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.min.css",
        filters=bs_icons,
    ),
    output="css/main.css",
)

css_custom = Bundle(
    "../app/ressources/css/custom.css", filters="cssmin", output="css/custom.css"
)


js_main = Bundle(
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js",
    output="js/main.js",
)

js_pipan = Bundle("../app/ressources/js/pipan.js", filters="rjsmin", output="js/pipan.js")

js_custom = Bundle(
    "../app/ressources/js/color_modes.js",
    "../app/ressources/js/custom.js",
    filters="rjsmin",
    output="js/custom.js",
)
