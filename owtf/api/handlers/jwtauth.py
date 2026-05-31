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


def admin_required(handler_class):
    """Decorator for endpoints that should be restricted to admin users.

    TODO: enforce an admin role check once the role system is confirmed with
    mentors.  For now this is identical to @jwtauth (authentication required).
    """
    return jwtauth(handler_class)
