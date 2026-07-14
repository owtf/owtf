"""
JSON Web Token auth for Tornado.

Two decorators live here:

* ``@jwtauth`` — every request must carry a valid ``Authorization: Bearer <token>``
  header. If the header is missing, malformed, expired, or does not match a
  session in ``user_login_tokens``, the request is rejected and the wrapped
  handler is NEVER called.
* ``@admin_required`` — layers on top of ``@jwtauth``. First the token must
  be valid, then the resolved user must also be an admin (``is_admin=True``
  or on the ``ADMIN_EMAILS`` allow-list). Otherwise a 403 is returned and
  the handler is not called.

The key invariant: a failed auth check raises ``tornado.web.Finish`` so
Tornado's own machinery unwinds the request. That makes it impossible for
handler code (upload, delete, approve, etc.) to run behind a 401/403 response.
"""

import jwt
import tornado.web

from owtf.db.session import Session
from owtf.models.user_login_token import UserLoginToken
from owtf.settings import JWT_ALGORITHM, JWT_OPTIONS, JWT_SECRET_KEY


def _reject(handler, status, message):
    """Send an error response and stop the request.

    ``tornado.web.Finish`` is Tornado's canonical way to abort mid-request:
    Tornado catches it in its own dispatch code and flushes the response
    without ever calling the handler method. That's what makes this safe
    against the "wrote 401 but handler still ran" bug.
    """
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
            # _require_valid_jwt raises tornado.web.Finish on failure, which
            # Tornado handles upstream. We only reach handler_execute when
            # auth actually succeeded.
            _require_valid_jwt(self)
            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class


def get_user_id_from_request(handler):
    """Extract the user_id from the JWT in the Authorization header.

    Returns ``None`` if the header is missing, malformed or fails to decode.
    Does not raise — callers decide whether to reject the request.
    """
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


def user_is_admin(user) -> bool:
    """Return True if the user has admin rights.

    A user counts as admin if their ``is_admin`` column is True OR their
    email is on the ``ADMIN_EMAILS`` allow-list (covers accounts that
    existed before the column was added).
    """
    if user is None:
        return False
    if getattr(user, "is_admin", False):
        return True
    from owtf.settings import ADMIN_EMAILS

    email = (getattr(user, "email", "") or "").strip().lower()
    return email in ADMIN_EMAILS


def admin_required(handler_class):
    """Class decorator: require a valid JWT AND admin privileges.

    JWT is checked first (so a request with no token gets a 401, not a 403).
    Only after that does the admin check run. Both failure paths raise
    ``tornado.web.Finish`` so the wrapped handler never runs.
    """
    original_execute = handler_class._execute

    def _execute(self, transforms, *args, **kwargs):
        from owtf.models.user import User

        # 1. JWT check — 401 if missing/invalid.
        _require_valid_jwt(self)

        # 2. Admin check — 403 if user is not an admin.
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
