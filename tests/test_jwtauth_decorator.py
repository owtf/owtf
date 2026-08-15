"""Tests for the @jwtauth and @admin_required decorators.

Key invariant: on auth failure, the wrapped handler body must NOT run.
Writing a 401 alone is not enough; Tornado keeps executing unless we
raise tornado.web.Finish.
"""

from unittest.mock import MagicMock

import jwt
import pytest
import tornado.web

# Register user models before importing the auth module (which pulls in
# UserLoginToken).
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
from owtf.api.handlers import jwtauth as jwtauth_module
from owtf.api.handlers.jwtauth import admin_required, jwtauth
from owtf.settings import JWT_ALGORITHM, JWT_SECRET_KEY


def make_fake_handler_class():
    """Minimal Tornado-like handler class the decorators can wrap."""

    class FakeHandler:
        did_real_work = False

        def __init__(self, headers=None):
            self._transforms = ["x"]
            self.status = None
            self.written = None
            self.request = MagicMock()
            self.request.headers = headers or {}

        def set_status(self, code):
            self.status = code

        def write(self, body):
            self.written = body

        def finish(self):
            pass

        def _execute(self, transforms, *args, **kwargs):
            FakeHandler.did_real_work = True
            return "handler ran"

    return FakeHandler


def test_missing_authorization_header_blocks_handler():
    Handler = make_fake_handler_class()
    Decorated = jwtauth(Handler)
    h = Decorated(headers={})

    with pytest.raises(tornado.web.Finish):
        h._execute([])

    assert Handler.did_real_work is False
    assert h.status == 401
    assert h.written["success"] is False


def test_malformed_authorization_header_blocks_handler():
    Handler = make_fake_handler_class()
    Decorated = jwtauth(Handler)
    h = Decorated(headers={"Authorization": "NotBearer abc"})

    with pytest.raises(tornado.web.Finish):
        h._execute([])

    assert Handler.did_real_work is False
    assert h.status == 401


def test_single_word_authorization_header_blocks_handler():
    """Guards against the original bug: len(parts) == 1 used to fall through."""
    Handler = make_fake_handler_class()
    Decorated = jwtauth(Handler)
    h = Decorated(headers={"Authorization": "Bearer"})

    with pytest.raises(tornado.web.Finish):
        h._execute([])

    assert Handler.did_real_work is False
    assert h.status == 401


def test_invalid_jwt_blocks_handler():
    Handler = make_fake_handler_class()
    Decorated = jwtauth(Handler)
    h = Decorated(headers={"Authorization": "Bearer not.a.real.jwt"})

    with pytest.raises(tornado.web.Finish):
        h._execute([])

    assert Handler.did_real_work is False
    assert h.status == 401


def test_valid_jwt_but_no_session_row_blocks_handler(monkeypatch):
    """Well-formed token without a matching login row must still be rejected."""
    Handler = make_fake_handler_class()
    Decorated = jwtauth(Handler)

    token = jwt.encode({"user_id": 42}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    # Session().close() should be safe; find_by_userid_and_token returns None.
    monkeypatch.setattr(jwtauth_module, "Session", lambda: MagicMock())
    monkeypatch.setattr(
        jwtauth_module.UserLoginToken,
        "find_by_userid_and_token",
        staticmethod(lambda session, user_id, tok: None),
    )

    h = Decorated(headers={"Authorization": f"Bearer {token}"})

    with pytest.raises(tornado.web.Finish):
        h._execute([])

    assert Handler.did_real_work is False
    assert h.status == 401


def test_valid_jwt_with_session_row_allows_handler(monkeypatch):
    Handler = make_fake_handler_class()
    Decorated = jwtauth(Handler)

    token = jwt.encode({"user_id": 42}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    monkeypatch.setattr(jwtauth_module, "Session", lambda: MagicMock())
    monkeypatch.setattr(
        jwtauth_module.UserLoginToken,
        "find_by_userid_and_token",
        staticmethod(lambda session, user_id, tok: MagicMock(id=1)),
    )

    h = Decorated(headers={"Authorization": f"Bearer {token}"})
    result = h._execute([])

    assert Handler.did_real_work is True
    assert result == "handler ran"


def test_admin_required_rejects_non_admin(monkeypatch):
    Handler = make_fake_handler_class()
    Decorated = admin_required(Handler)

    token = jwt.encode({"user_id": 42}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    monkeypatch.setattr(jwtauth_module, "Session", lambda: MagicMock())
    monkeypatch.setattr(
        jwtauth_module.UserLoginToken,
        "find_by_userid_and_token",
        staticmethod(lambda session, user_id, tok: MagicMock(id=1)),
    )
    fake_user = MagicMock(is_admin=False, email="normal@example.com")
    monkeypatch.setattr(
        "owtf.models.user.User.find_by_id",
        staticmethod(lambda session, uid: fake_user),
    )
    monkeypatch.setattr(jwtauth_module, "ADMIN_EMAILS", set(), raising=False)

    h = Decorated(headers={"Authorization": f"Bearer {token}"})

    with pytest.raises(tornado.web.Finish):
        h._execute([])

    assert Handler.did_real_work is False
    assert h.status == 403


def test_admin_required_allows_admin(monkeypatch):
    Handler = make_fake_handler_class()
    Decorated = admin_required(Handler)

    token = jwt.encode({"user_id": 42}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    monkeypatch.setattr(jwtauth_module, "Session", lambda: MagicMock())
    monkeypatch.setattr(
        jwtauth_module.UserLoginToken,
        "find_by_userid_and_token",
        staticmethod(lambda session, user_id, tok: MagicMock(id=1)),
    )
    fake_user = MagicMock(is_admin=True, email="admin@example.com")
    monkeypatch.setattr(
        "owtf.models.user.User.find_by_id",
        staticmethod(lambda session, uid: fake_user),
    )

    h = Decorated(headers={"Authorization": f"Bearer {token}"})
    result = h._execute([])

    assert Handler.did_real_work is True
    assert result == "handler ran"


def test_admin_required_blocks_unauthenticated():
    """No token: must be rejected by the inner @jwtauth layer."""
    Handler = make_fake_handler_class()
    Decorated = admin_required(Handler)
    h = Decorated(headers={})

    with pytest.raises(tornado.web.Finish):
        h._execute([])

    assert Handler.did_real_work is False
    assert h.status == 401
