"""
JSON Web Token auth for Tornado
"""

import jwt

from owtf.db.session import Session
from owtf.models.user_login_token import UserLoginToken
from owtf.settings import JWT_ALGORITHM, JWT_OPTIONS, JWT_SECRET_KEY


def jwtauth(handler_class):
    """Decorator to handle Tornado JWT Authentication"""

    def wrap_execute(handler_execute):
        def require_auth(handler, kwargs):
            auth = handler.request.headers.get("Authorization")
            if auth:
                parts = auth.split()

                if parts[0].lower() != "bearer" or len(parts) == 1 or len(parts) > 2:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write({"success": False, "message": "Invalid header authorization"})
                    handler.finish()

                token = parts[1]
                try:
                    payload = jwt.decode(token, JWT_SECRET_KEY, options=JWT_OPTIONS, algorithms=[JWT_ALGORITHM])
                    user_id = payload.get("user_id", None)
                    session = Session()
                    user_token = UserLoginToken.find_by_userid_and_token(session, user_id, token)
                    if user_id is None or user_token is None:
                        handler._transforms = []
                        handler.set_status(401)
                        handler.write({"success": False, "message": "Unauthorized"})
                        handler.finish()

                except Exception:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write({"success": False, "message": "Unauthorized"})
                    handler.finish()
            else:
                handler._transforms = []
                handler.write({"success": False, "message": "Missing authorization"})
                handler.finish()

            return True

        def _execute(self, transforms, *args, **kwargs):
            try:
                require_auth(self, kwargs)
            except Exception:
                return False

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
    """Decorator for endpoints restricted to platform admins.

    Layers on top of ``@jwtauth``: first the JWT must be valid, then the
    resolved user must have ``is_admin = True`` or be on the
    ``ADMIN_EMAILS`` allow-list in settings.
    """
    handler_class = jwtauth(handler_class)
    original_execute = handler_class._execute

    def _execute(self, transforms, *args, **kwargs):
        from owtf.db.session import Session
        from owtf.models.user import User

        user_id = get_user_id_from_request(self)
        session = Session()
        try:
            user = User.find_by_id(session, user_id) if user_id else None
            if not user_is_admin(user):
                self._transforms = []
                self.set_status(403)
                self.write({"success": False, "message": "Admin privileges required"})
                self.finish()
                return False
        finally:
            session.close()
        return original_execute(self, transforms, *args, **kwargs)

    handler_class._execute = _execute
    return handler_class
