"""Use Flask-Asssets for build and minified css and js."""

from flask_assets import Bundle

css_main = Bundle(
    "https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,600,700,300italic,400italic,600italic",  # noqa
    "https://fonts.googleapis.com/css?family=Roboto+Mono:400,300,700",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
    Bundle(
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.min.css",  # noqa
        filters="datauri",
    ),
    output="css/main.css",
)

css_custom = Bundle(
    "../app/resources/css/custom.css", filters="cssmin", output="css/custom.css"
)


js_main = Bundle(
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/js-cookie/2.0.4/js.cookie.min.js",
    output="js/main.js",
)

js_pipan = Bundle(
    "../app/resources/js/pipan.js", filters="jinja2,rjsmin", output="js/pipan.js"
)

js_colors = Bundle(
    "../app/resources/js/colorconverter.js",
    "../app/resources/js/color_modes.js",
    filters="rjsmin",
    output="js/colors.js",
)

js_custom = Bundle(
    "../app/resources/js/custom.js", filters="jinja2,rjsmin", output="js/custom.js"
)
