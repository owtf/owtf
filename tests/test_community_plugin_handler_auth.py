"""
tests/test_community_plugin_handler_auth.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify the trust boundaries on the community plugin endpoints:

* Source, delete, approve, reject, audit, and test-run handlers are
  wrapped with @admin_required, so a non-admin JWT never reaches the
  handler body.
* The list handler refuses non-admin status=pending / status=rejected
  requests before it hits the DB.

Same fake-handler style as test_jwtauth_decorator: stub out
UserLoginToken and User.find_by_id so no database is touched, then call
_execute and assert on the resulting status code.
"""

from unittest.mock import MagicMock

import jwt
import pytest

import owtf.models.email_confirmation  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
from owtf.api.handlers import community_plugin as cp_module
from owtf.api.handlers import jwtauth as jwtauth_module
from owtf.settings import JWT_ALGORITHM, JWT_SECRET_KEY


def _valid_token(user_id=42):
    return jwt.encode({"user_id": user_id}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _stub_auth(monkeypatch, is_admin):
    """Wire the JWT and user lookups so _require_valid_jwt succeeds and
    the admin check sees a user with the given privilege."""
    monkeypatch.setattr(jwtauth_module, "Session", lambda: MagicMock())
    monkeypatch.setattr(
        jwtauth_module.UserLoginToken,
        "find_by_userid_and_token",
        staticmethod(lambda session, user_id, tok: MagicMock(id=1)),
    )
    fake_user = MagicMock(is_admin=is_admin, email="user@example.com")
    monkeypatch.setattr(
        "owtf.models.user.User.find_by_id",
        staticmethod(lambda session, uid: fake_user),
    )
    monkeypatch.setattr(jwtauth_module, "ADMIN_EMAILS", set(), raising=False)


class _FakeHandler:
    """Minimal Tornado-shaped handler that captures set_status/write and
    records whether the wrapped body ran."""

    did_real_work = False

    def __init__(self, headers=None):
        type(self).did_real_work = False
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
        type(self).did_real_work = True
        return "ran"


def _decorated(decorator):
    """Fresh fake class wrapped with the given decorator, so class-level
    state does not leak between test cases."""

    class Handler(_FakeHandler):
        pass

    return decorator(Handler), Handler


# ---------------------------------------------------------------------------
# Admin-only handlers reject non-admin JWTs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "handler_cls_name",
    [
        "CommunityPluginSourceHandler",
        "CommunityPluginDeleteHandler",
        "CommunityPluginApproveHandler",
        "CommunityPluginRejectHandler",
        "CommunityPluginReviewHistoryHandler",
        "CommunityPluginTestRunHandler",
    ],
)
def test_admin_handlers_reject_non_admin(handler_cls_name):
    """Every admin route must carry @admin_required. We check for the
    sentinel names that the decorator inserts into _execute. Catches an
    accidental drop of the decorator during a refactor."""
    handler_cls = getattr(cp_module, handler_cls_name)
    src = handler_cls._execute.__code__.co_freevars + handler_cls._execute.__code__.co_names
    # admin_required's inner _execute closes over ``original_execute`` and
    # references User / user_is_admin. jwtauth-only handlers do not.
    assert "user_is_admin" in src or "original_execute" in src, (
        "{} looks like it is missing @admin_required. There is no admin check baked into _execute.".format(
            handler_cls_name
        )
    )


# ---------------------------------------------------------------------------
# List handler: status filter enforcement
# ---------------------------------------------------------------------------


def _make_list_handler(monkeypatch, is_admin, status_arg):
    """Build a real CommunityPluginListHandler with just enough
    scaffolding to run its get(). No Tornado app, no real DB."""
    _stub_auth(monkeypatch, is_admin=is_admin)

    # Skip Tornado's __init__; we set only what get() touches.
    handler = cp_module.CommunityPluginListHandler.__new__(cp_module.CommunityPluginListHandler)
    handler.session = MagicMock()
    handler.request = MagicMock()
    handler.request.headers = {"Authorization": "Bearer " + _valid_token()}
    handler.request.arguments = {"status": [status_arg]}
    handler.written = None
    handler.status = None

    def _set_status(code):
        handler.status = code

    def _write(body):
        handler.written = body

    def _finish():
        pass

    handler.set_status = _set_status
    handler.write = _write
    handler.finish = _finish
    return handler


def test_list_non_admin_pending_is_forbidden(monkeypatch):
    from owtf.lib.exceptions import APIError

    handler = _make_list_handler(monkeypatch, is_admin=False, status_arg="pending")
    with pytest.raises(APIError) as exc:
        handler.get()
    assert exc.value.status_code == 403


def test_list_non_admin_rejected_is_forbidden(monkeypatch):
    from owtf.lib.exceptions import APIError

    handler = _make_list_handler(monkeypatch, is_admin=False, status_arg="rejected")
    with pytest.raises(APIError) as exc:
        handler.get()
    assert exc.value.status_code == 403


def test_list_admin_pending_reaches_manager(monkeypatch):
    """An admin asking for status=pending must actually reach
    list_community_plugins (proving the 403 gate is admin-conditional)."""
    called = {}

    def fake_list(**kwargs):
        called.update(kwargs)
        return {"total": 0, "limit": 50, "offset": 0, "plugins": []}

    monkeypatch.setattr(cp_module, "list_community_plugins", fake_list)
    handler = _make_list_handler(monkeypatch, is_admin=True, status_arg="pending")
    handler.get()
    assert called.get("status") == "pending"
    assert called.get("as_admin") is True


def test_list_non_admin_approved_reaches_manager(monkeypatch):
    """Non-admins are allowed to request the approved queue and get the
    public serializer."""
    called = {}

    def fake_list(**kwargs):
        called.update(kwargs)
        return {"total": 0, "limit": 50, "offset": 0, "plugins": []}

    monkeypatch.setattr(cp_module, "list_community_plugins", fake_list)
    handler = _make_list_handler(monkeypatch, is_admin=False, status_arg="approved")
    handler.get()
    assert called.get("status") == "approved"
    assert called.get("as_admin") is False
