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
from owtf.models.user_plugin import APPROVAL_APPROVED
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


# ---------------------------------------------------------------------------
# Detail handler: ownership + approval gate
#
# Regression for the IDOR that viyatb flagged: a non-admin used to be
# able to read another user's pending or rejected plugin by guessing
# its id. Non-admin, non-owner requests for anything other than an
# approved plugin must now return 404, and the response body must not
# include reviewer-trail fields (rejection_reason, reviewed_by_user_id).
# ---------------------------------------------------------------------------


def _make_detail_handler(monkeypatch, caller_user_id, is_admin, plugin):
    """Build a CommunityPluginDetailHandler wired to return *plugin* from
    the DB and to see the caller as *caller_user_id* / *is_admin*."""
    monkeypatch.setattr(jwtauth_module, "Session", lambda: MagicMock())
    monkeypatch.setattr(
        jwtauth_module.UserLoginToken,
        "find_by_userid_and_token",
        staticmethod(lambda session, user_id, tok: MagicMock(id=1)),
    )
    fake_user = MagicMock(id=caller_user_id, is_admin=is_admin, email="user@example.com")
    monkeypatch.setattr(
        "owtf.models.user.User.find_by_id",
        staticmethod(lambda session, uid: fake_user),
    )
    monkeypatch.setattr(jwtauth_module, "ADMIN_EMAILS", set(), raising=False)

    handler = cp_module.CommunityPluginDetailHandler.__new__(cp_module.CommunityPluginDetailHandler)

    # Session.query(UserPlugin).get(id) returns the plugin fixture.
    session = MagicMock()
    session.query.return_value.get.return_value = plugin
    handler.session = session

    handler.request = MagicMock()
    handler.request.headers = {"Authorization": "Bearer " + _valid_token(caller_user_id)}
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


def _fake_plugin(plugin_id, owner_id, status, name="p"):
    """Return a stub UserPlugin whose serializers echo the interesting
    fields, so we can assert which serializer the handler picked."""
    p = MagicMock()
    p.id = plugin_id
    p.user_id = owner_id
    p.approval_status = status
    p.to_dict.return_value = {"id": plugin_id, "name": name, "view": "public"}
    p.to_owner_dict.return_value = {
        "id": plugin_id,
        "name": name,
        "view": "owner",
        "rejection_reason": "not good enough",
    }
    p.to_admin_dict.return_value = {
        "id": plugin_id,
        "name": name,
        "view": "admin",
        "rejection_reason": "not good enough",
        "reviewed_by_user_id": 999,
    }
    return p


def test_detail_non_admin_cannot_read_other_users_pending(monkeypatch):
    """Regression: guessing the id of someone else's pending plugin used
    to return the metadata dict. It must now 404."""
    from owtf.lib.exceptions import APIError

    plugin = _fake_plugin(plugin_id=7, owner_id=1, status="pending")
    handler = _make_detail_handler(monkeypatch, caller_user_id=42, is_admin=False, plugin=plugin)
    with pytest.raises(APIError) as exc:
        handler.get(7)
    assert exc.value.status_code == 404
    # And the serializers must never have been called, so no reviewer
    # trail could have leaked through the exception path either.
    plugin.to_dict.assert_not_called()
    plugin.to_owner_dict.assert_not_called()
    plugin.to_admin_dict.assert_not_called()


def test_detail_non_admin_cannot_read_other_users_rejected(monkeypatch):
    from owtf.lib.exceptions import APIError

    plugin = _fake_plugin(plugin_id=8, owner_id=1, status="rejected")
    handler = _make_detail_handler(monkeypatch, caller_user_id=42, is_admin=False, plugin=plugin)
    with pytest.raises(APIError) as exc:
        handler.get(8)
    assert exc.value.status_code == 404


def test_detail_non_admin_can_read_approved(monkeypatch):
    """Approved plugins are public. Any authenticated user gets the
    public serializer, without reviewer-trail fields."""
    plugin = _fake_plugin(plugin_id=9, owner_id=1, status=APPROVAL_APPROVED)
    handler = _make_detail_handler(monkeypatch, caller_user_id=42, is_admin=False, plugin=plugin)
    handler.get(9)
    plugin.to_dict.assert_called_once()
    plugin.to_owner_dict.assert_not_called()
    plugin.to_admin_dict.assert_not_called()


def test_detail_owner_sees_their_own_rejected_plugin(monkeypatch):
    """The uploader must still be able to fetch their own rejected
    plugin so the marketplace UI can show the rejection reason."""
    plugin = _fake_plugin(plugin_id=10, owner_id=42, status="rejected")
    handler = _make_detail_handler(monkeypatch, caller_user_id=42, is_admin=False, plugin=plugin)
    handler.get(10)
    plugin.to_owner_dict.assert_called_once()
    plugin.to_admin_dict.assert_not_called()


def test_detail_admin_sees_admin_view_of_pending_plugin(monkeypatch):
    """An admin reviewing a pending upload gets the admin serializer."""
    plugin = _fake_plugin(plugin_id=11, owner_id=1, status="pending")
    handler = _make_detail_handler(monkeypatch, caller_user_id=99, is_admin=True, plugin=plugin)
    handler.get(11)
    plugin.to_admin_dict.assert_called_once()


def test_detail_missing_plugin_returns_404(monkeypatch):
    from owtf.lib.exceptions import APIError

    handler = _make_detail_handler(monkeypatch, caller_user_id=1, is_admin=False, plugin=None)
    with pytest.raises(APIError) as exc:
        handler.get(123)
    assert exc.value.status_code == 404
