"""
tests/test_community_plugin_manager.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for owtf.managers.community_plugin.

These tests use an in-memory SQLite database so no PostgreSQL is required.

Run with:
    python -m pytest tests/test_community_plugin_manager.py -v
"""

import textwrap
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from owtf.db.model_base import Model
from owtf.managers.community_plugin import (
    _sanitise_filename,
    approve_community_plugin,
    delete_community_plugin,
    get_community_plugin,
    list_community_plugins,
    reject_community_plugin,
    upload_community_plugin,
)
from owtf.models.user_plugin import APPROVAL_APPROVED, APPROVAL_REJECTED

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GOOD_PLUGIN_SOURCE = textwrap.dedent(
    """
    DESCRIPTION = "A safe test plugin"

    def run(target_url):
        return {"target": target_url, "ok": True}
    """
).encode("utf-8")

BAD_PLUGIN_SOURCE = textwrap.dedent(
    """
    import os
    DESCRIPTION = "Dangerous"
    def run(target_url):
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
        # Mock sandbox to fail so the plugin is saved as pending (not auto-approved).
        # This isolates upload logic from sandbox behaviour.
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "sandbox mocked"
        mock_result.to_dict.return_value = {"success": False, "error": "sandbox mocked"}
        with patch("owtf.managers.community_plugin.SandboxRunner.run", return_value=mock_result):
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
        # Sandbox mocked to fail so the plugin stays in pending state.
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "sandbox mocked"
        mock_result.to_dict.return_value = {"success": False, "error": "sandbox mocked"}
        with patch("owtf.managers.community_plugin.SandboxRunner.run", return_value=mock_result):
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
