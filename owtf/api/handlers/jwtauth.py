"""
JWT auth decorators for Tornado handlers.

@jwtauth requires a valid Bearer token. @admin_required layers an admin
check on top. Failed auth raises tornado.web.Finish so the wrapped
handler never runs after a 401/403.
"""

import jwt
import tornado.web

from owtf.db.session import Session
from owtf.models.user_login_token import UserLoginToken
from owtf.settings import JWT_ALGORITHM, JWT_OPTIONS, JWT_SECRET_KEY


def _reject(handler, status, message):
    """Abort the request. Raises tornado.web.Finish so the handler body never runs."""
    handler._transforms = []
    handler.set_status(status)
    handler.write({"success": False, "message": message})
    raise tornado.web.Finish()


def _require_valid_jwt(handler):
    """Verify the Authorization header. Raises tornado.web.Finish on failure."""
    auth = handler.request.headers.get("Authorization")
    if not auth:
        _reject(handler, 401, "Missing authorization")

    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        _reject(handler, 401, "Invalid header authorization")

    token = parts[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, options=JWT_OPTIONS, algorithms=[JWT_ALGORITHM])
    except Exception:
        _reject(handler, 401, "Unauthorized")

    user_id = payload.get("user_id")
    if user_id is None:
        _reject(handler, 401, "Unauthorized")

    session = Session()
    try:
        user_token = UserLoginToken.find_by_userid_and_token(session, user_id, token)
    finally:
        session.close()
    if user_token is None:
        _reject(handler, 401, "Unauthorized")


def jwtauth(handler_class):
    """Class decorator: require a valid JWT before the handler runs."""

    def wrap_execute(handler_execute):
        def _execute(self, transforms, *args, **kwargs):
            _require_valid_jwt(self)
            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class


def get_user_id_from_request(handler):
    """Extract user_id from the JWT, or None if missing/malformed. Never raises."""
    auth = handler.request.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    try:
        payload = jwt.decode(parts[1], JWT_SECRET_KEY, options=JWT_OPTIONS, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except Exception:
        return None


def user_is_admin(user):
    """True if the user row has is_admin set. ADMIN_EMAILS only seeds this flag
    at registration and login; it is never consulted per request."""
    return bool(user and getattr(user, "is_admin", False))


def admin_required(handler_class):
    """Class decorator: require a valid JWT and an admin user. 401 first, then 403."""
    original_execute = handler_class._execute

    def _execute(self, transforms, *args, **kwargs):
        from owtf.models.user import User

        _require_valid_jwt(self)

        user_id = get_user_id_from_request(self)
        session = Session()
        try:
            user = User.find_by_id(session, user_id) if user_id else None
            if not user_is_admin(user):
                _reject(self, 403, "Admin privileges required")
        finally:
            session.close()

        return original_execute(self, transforms, *args, **kwargs)

    handler_class._execute = _execute
    return handler_class
