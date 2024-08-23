from ..helpers.utils import get_locale, get_timezone
from .base import (
    babel,
    handle_access_forbidden,
    handle_bad_gateway,
    handle_bad_request,
    handle_internal_server_error,
    handle_page_not_found,
    login_manager,
    raspiconfig,
)


def init_app(app):
    babel.init_app(app, locale_selector=get_locale, timezone_selector=get_timezone)
    raspiconfig.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(403, handle_access_forbidden)
    app.register_error_handler(404, handle_page_not_found)
    app.register_error_handler(500, handle_internal_server_error)
    app.register_error_handler(502, handle_bad_gateway)
