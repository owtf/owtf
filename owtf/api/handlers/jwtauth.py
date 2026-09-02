"""
JWT auth decorators for Tornado handlers.

@jwtauth requires a valid Bearer token. @admin_required layers an admin
check on top. Failed auth finishes the response in the wrapper so the
handler never runs after a 401/403.
"""

import jwt

from owtf.db.session import Session
from owtf.models.user_login_token import UserLoginToken
from owtf.settings import JWT_ALGORITHM, JWT_OPTIONS, JWT_SECRET_KEY


def _reject(handler, status, message):
    """Write and finish an authentication failure response."""
    handler.set_status(status)
    handler.write({"success": False, "message": message})
    handler.finish()


def _require_valid_jwt(handler):
    """Return the authenticated user id, or finish the response and return None."""
    auth = handler.request.headers.get("Authorization")
    if not auth:
        _reject(handler, 401, "Missing authorization")
        return None

    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        _reject(handler, 401, "Invalid header authorization")
        return None

    token = parts[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, options=JWT_OPTIONS, algorithms=[JWT_ALGORITHM])
    except Exception:
        _reject(handler, 401, "Unauthorized")
        return None

    user_id = payload.get("user_id")
    if user_id is None:
        _reject(handler, 401, "Unauthorized")
        return None

    session = Session()
    try:
        user_token = UserLoginToken.find_by_userid_and_token(session, user_id, token)
    finally:
        session.close()
    if user_token is None:
        _reject(handler, 401, "Unauthorized")
        return None
    return user_id


def jwtauth(handler_class):
    """Class decorator: require a valid JWT before the handler runs."""

    def wrap_execute(handler_execute):
        def _execute(self, transforms, *args, **kwargs):
            self._transforms = transforms
            if _require_valid_jwt(self) is None:
                return None
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
    """True if the user row has is_admin set. ADMIN_EMAILS is a one-time
    seed at registration only; the auth path reads users.is_admin, so
    demoting a user with owtf-admin sticks across logins."""
    return bool(user and getattr(user, "is_admin", False))


def admin_required(handler_class):
    """Class decorator: require a valid JWT and an admin user. 401 first, then 403."""
    original_execute = handler_class._execute

    def _execute(self, transforms, *args, **kwargs):
        from owtf.models.user import User

        self._transforms = transforms
        user_id = _require_valid_jwt(self)
        if user_id is None:
            return None

        session = Session()
        try:
            user = User.find_by_id(session, user_id)
            if not user_is_admin(user):
                _reject(self, 403, "Admin privileges required")
                return None
        finally:
            session.close()

        return original_execute(self, transforms, *args, **kwargs)

    handler_class._execute = _execute
    return handler_class
