"""
tests/test_community_plugin_manager.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for owtf.managers.community_plugin.

These tests use an in-memory SQLite database so no PostgreSQL is required.

Run with:
    python -m pytest tests/test_community_plugin_manager.py -v
"""

import textwrap

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importing the User model (and its companions) registers the ``users`` table
# on the shared metadata so the user_plugins → users foreign keys resolve when
# ``create_all`` runs against the in-memory SQLite engine.
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
from owtf.db.model_base import Model
from owtf.managers.community_plugin import (
    _sanitise_filename,
    approve_community_plugin,
    delete_community_plugin,
    get_community_plugin,
    get_community_plugin_source,
    list_community_plugins,
    list_owner_plugins,
    reject_community_plugin,
    upload_community_plugin,
)
from owtf.models.user_plugin import APPROVAL_APPROVED, APPROVAL_REJECTED, UserPlugin

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GOOD_PLUGIN_SOURCE = textwrap.dedent(
    """
    DESCRIPTION = "A safe test plugin"

    def run(PluginInfo):
        return {"target": PluginInfo.get("target_url"), "ok": True}
    """
).encode("utf-8")

BAD_PLUGIN_SOURCE = textwrap.dedent(
    """
    import os
    DESCRIPTION = "Dangerous"
    def run(PluginInfo):
        os.system("rm -rf /")
        return {}
    """
).encode("utf-8")


@pytest.fixture()
def session(tmp_path, monkeypatch):
    """Provide a fresh in-memory SQLite session and redirect COMMUNITY_PLUGINS_DIR."""
    monkeypatch.setattr("owtf.managers.community_plugin.COMMUNITY_PLUGINS_DIR", str(tmp_path))
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


# ---------------------------------------------------------------------------
# Tests: filename sanitisation
# ---------------------------------------------------------------------------


class TestSanitiseFilename:
    def test_normal_name_unchanged(self):
        assert _sanitise_filename("my_plugin") == "my_plugin"

    def test_special_chars_replaced(self):
        result = _sanitise_filename("my plugin!@#")
        assert "!" not in result
        assert "@" not in result

    def test_empty_gives_plugin(self):
        assert _sanitise_filename("") == "plugin"

    def test_leading_dot_stripped(self):
        assert not _sanitise_filename(".hidden").startswith(".")

    def test_truncated_to_100(self):
        result = _sanitise_filename("a" * 200)
        assert len(result) <= 100


# ---------------------------------------------------------------------------
# Tests: upload
# ---------------------------------------------------------------------------


class TestUploadPlugin:
    def test_valid_upload_succeeds(self, session):
        result = upload_community_plugin(
            session=session,
            name="Test Plugin",
            description="A test",
            group="web",
            plugin_type="passive",
            author="testuser",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="test_plugin.py",
        )
        assert result["success"]
        assert result["plugin"]["name"] == "Test Plugin"
        assert result["plugin"]["approval_status"] == "pending"

    def test_dangerous_plugin_rejected(self, session):
        result = upload_community_plugin(
            session=session,
            name="Evil Plugin",
            description="Bad",
            group="web",
            plugin_type="active",
            author="attacker",
            file_body=BAD_PLUGIN_SOURCE,
            original_filename="evil.py",
        )
        assert not result["success"]
        assert len(result["violations"]) > 0

    def test_duplicate_name_rejected(self, session):
        upload_community_plugin(
            session=session,
            name="Dup Plugin",
            description="First",
            group="web",
            plugin_type="passive",
            author="user1",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="dup.py",
        )
        result = upload_community_plugin(
            session=session,
            name="Dup Plugin",
            description="Second",
            group="web",
            plugin_type="passive",
            author="user2",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="dup2.py",
        )
        assert not result["success"]
        assert any("already exists" in e for e in result["errors"])

    def test_invalid_group_rejected(self, session):
        result = upload_community_plugin(
            session=session,
            name="Bad Group",
            description="x",
            group="invalid_group",
            plugin_type="passive",
            author="user",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="p.py",
        )
        assert not result["success"]
        assert any("group" in e.lower() for e in result["errors"])

    def test_non_py_extension_rejected(self, session):
        result = upload_community_plugin(
            session=session,
            name="Bad Ext",
            description="x",
            group="web",
            plugin_type="passive",
            author="user",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="plugin.sh",
        )
        assert not result["success"]
        assert any("type" in e.lower() or ".sh" in e or ".py" in e for e in result["errors"])

    def test_file_too_large_rejected(self, session, monkeypatch):
        monkeypatch.setattr("owtf.managers.community_plugin.PLUGIN_UPLOAD_MAX_SIZE", 10)
        result = upload_community_plugin(
            session=session,
            name="Big Plugin",
            description="x",
            group="web",
            plugin_type="passive",
            author="user",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="big.py",
        )
        assert not result["success"]
        assert any("size" in e.lower() or "exceed" in e.lower() for e in result["errors"])

    def test_missing_name_rejected(self, session):
        result = upload_community_plugin(
            session=session,
            name="",
            description="Some description",
            group="web",
            plugin_type="passive",
            author="user",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="p.py",
        )
        assert not result["success"]
        assert any("name" in e.lower() for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: list / get
# ---------------------------------------------------------------------------


class TestListGetPlugin:
    def _upload(self, session, name="Plugin A"):
        result = upload_community_plugin(
            session=session,
            name=name,
            description="desc",
            group="web",
            plugin_type="passive",
            author="author",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="p.py",
        )
        return result["plugin"]["id"]

    def test_list_empty(self, session):
        data = list_community_plugins(session)
        assert data["total"] == 0
        assert data["plugins"] == []

    def test_list_approved_plugins(self, session):
        pid = self._upload(session)
        approve_community_plugin(session, pid)
        data = list_community_plugins(session, status="approved")
        assert data["total"] == 1
        assert data["plugins"][0]["id"] == pid

    def test_pending_not_in_approved_list(self, session):
        self._upload(session)
        data = list_community_plugins(session, status="approved")
        assert data["total"] == 0

    def test_get_plugin_by_id(self, session):
        pid = self._upload(session)
        plugin = get_community_plugin(session, pid)
        assert plugin is not None
        assert plugin["id"] == pid

    def test_get_nonexistent_plugin_returns_none(self, session):
        assert get_community_plugin(session, 99999) is None


# ---------------------------------------------------------------------------
# Tests: approve / reject
# ---------------------------------------------------------------------------


class TestApproveReject:
    def _upload(self, session):
        result = upload_community_plugin(
            session=session,
            name="ApprovMe",
            description="desc",
            group="web",
            plugin_type="passive",
            author="author",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="p.py",
        )
        return result["plugin"]["id"]

    def test_approve_changes_status(self, session):
        pid = self._upload(session)
        updated = approve_community_plugin(session, pid)
        assert updated["approval_status"] == APPROVAL_APPROVED

    def test_reject_stores_reason(self, session):
        pid = self._upload(session)
        updated = reject_community_plugin(session, pid, "Dangerous code pattern")
        assert updated["approval_status"] == APPROVAL_REJECTED
        assert "Dangerous" in updated["rejection_reason"]

    def test_approve_nonexistent_returns_none(self, session):
        assert approve_community_plugin(session, 99999) is None


# ---------------------------------------------------------------------------
# Tests: delete
# ---------------------------------------------------------------------------


class TestDeletePlugin:
    def test_delete_removes_record(self, session, tmp_path):
        result = upload_community_plugin(
            session=session,
            name="ToDelete",
            description="desc",
            group="web",
            plugin_type="passive",
            author="author",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="p.py",
        )
        pid = result["plugin"]["id"]
        ok = delete_community_plugin(session, pid)
        assert ok
        assert get_community_plugin(session, pid) is None

    def test_delete_nonexistent_returns_false(self, session):
        assert not delete_community_plugin(session, 99999)


# ---------------------------------------------------------------------------
# Tests: serializers never leak file_path
# ---------------------------------------------------------------------------


def _upload(session, name="LeakCheck", user_id=None):
    return upload_community_plugin(
        session=session,
        name=name,
        description="d",
        group="web",
        plugin_type="passive",
        author="a",
        file_body=GOOD_PLUGIN_SOURCE,
        original_filename="p.py",
        user_id=user_id,
    )["plugin"]["id"]


class TestSerializersNeverLeakFilePath:
    """file_path is a server-side implementation detail. It must never
    appear in any JSON serializer, regardless of audience (public,
    owner, admin, or the wrapped manager calls that build API bodies)."""

    def test_public_dict_has_no_file_path(self, session):
        pid = _upload(session, name="Pub")
        d = get_community_plugin(session, pid)
        assert "file_path" not in d

    def test_admin_dict_has_no_file_path(self, session):
        pid = _upload(session, name="Adm")
        d = get_community_plugin(session, pid, as_admin=True)
        assert "file_path" not in d
        # But admins do see the reviewer trail fields.
        assert "reviewed_by_user_id" in d
        assert "execution_timeout" in d

    def test_list_response_has_no_file_path(self, session):
        pid = _upload(session, name="Listed")
        approve_community_plugin(session, pid)
        data = list_community_plugins(session, status="approved")
        assert data["plugins"], "expected at least one plugin"
        for p in data["plugins"]:
            assert "file_path" not in p

    def test_upload_result_has_no_file_path(self, session):
        result = upload_community_plugin(
            session=session,
            name="UploadShape",
            description="d",
            group="web",
            plugin_type="passive",
            author="a",
            file_body=GOOD_PLUGIN_SOURCE,
            original_filename="u.py",
        )
        assert result["success"]
        assert "file_path" not in result["plugin"]

    def test_approve_response_has_no_file_path(self, session):
        pid = _upload(session, name="ApproveShape")
        d = approve_community_plugin(session, pid, reviewer_id=1)
        assert "file_path" not in d

    def test_reject_response_has_no_file_path(self, session):
        pid = _upload(session, name="RejectShape")
        d = reject_community_plugin(session, pid, "nope", reviewer_id=1)
        assert "file_path" not in d
        assert d["rejection_reason"] == "nope"

    def test_owner_dict_carries_rejection_reason(self, session):
        pid = _upload(session, name="OwnerReject", user_id=42)
        reject_community_plugin(session, pid, "unsafe pattern", reviewer_id=1)
        owner = list_owner_plugins(session, user_id=42)
        assert owner["total"] == 1
        entry = owner["plugins"][0]
        assert "file_path" not in entry
        assert entry["rejection_reason"] == "unsafe pattern"


# ---------------------------------------------------------------------------
# Tests: source endpoint reads file server-side without leaking the path
# ---------------------------------------------------------------------------


class TestSourceEndpoint:
    def test_returns_source_without_file_path(self, session):
        pid = _upload(session, name="ShowSrc")
        data = get_community_plugin_source(session, pid)
        assert data is not None
        assert data["plugin_id"] == pid
        assert data["source_code"] is not None
        assert "DESCRIPTION" in data["source_code"]
        assert "file_path" not in data

    def test_missing_plugin_returns_none(self, session):
        assert get_community_plugin_source(session, 99999) is None

    def test_missing_file_on_disk_returns_none_source(self, session, tmp_path):
        pid = _upload(session, name="GhostFile")
        # Yank the file out from under the plugin, then confirm we
        # return None source_code instead of crashing.
        plugin = session.query(UserPlugin).get(pid)
        import os

        os.remove(plugin.file_path)
        data = get_community_plugin_source(session, pid)
        assert data is not None
        assert data["source_code"] is None
        assert "file_path" not in data


# ---------------------------------------------------------------------------
# Tests: owner listing does not spill other users' work
# ---------------------------------------------------------------------------


class TestOwnerListingIsolation:
    def test_only_returns_current_users_plugins(self, session):
        _upload(session, name="MinePluginA", user_id=1)
        _upload(session, name="MinePluginB", user_id=1)
        _upload(session, name="TheirsPluginC", user_id=2)

        mine = list_owner_plugins(session, user_id=1)
        theirs = list_owner_plugins(session, user_id=2)
        stranger = list_owner_plugins(session, user_id=999)

        mine_names = {p["name"] for p in mine["plugins"]}
        theirs_names = {p["name"] for p in theirs["plugins"]}

        assert mine_names == {"MinePluginA", "MinePluginB"}
        assert theirs_names == {"TheirsPluginC"}
        assert stranger["total"] == 0
