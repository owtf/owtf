"""
tests/test_plugin_manager_integration.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration tests for the community-plugin ↔ OWTF plugin-manager bridge.

Covers:
  - ``get_community_plugin_dicts`` returns the right shape for approved plugins
  - ``get_all_plugin_dicts`` merges community plugins into the built-in list
  - ``get_all_plugin_dicts`` filters community plugins by group / type
  - ``get_all_plugin_dicts(include_community=False)`` excludes them
  - ``PluginRunner._run_community_plugin`` delegates to SandboxRunner
  - ``PluginRunner.run_plugin`` routes community vs built-in correctly

These tests use an in-memory SQLite database limited to just the
``user_plugins`` table (the same pattern used in
``test_community_plugin_manager.py``), so no PostgreSQL is required.

Run with:
    python -m pytest tests/test_plugin_manager_integration.py -v
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import owtf.models.plugin_output  # noqa: F401

# Import related models before anything else so SQLAlchemy can resolve
# Plugin.works → Work and Plugin.outputs → PluginOutput when mappers
# are configured on first use.  Without these imports, creating a
# UserPlugin() instance triggers mapper configuration for the whole
# registry and fails with "failed to locate a name 'Work'".
import owtf.models.work  # noqa: F401
from owtf.models.user_plugin import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    UserPlugin,
)

# ---------------------------------------------------------------------------
# DB fixtures — only the user_plugins table, no Postgres needed
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def db_engine():
    """In-memory SQLite engine with only the user_plugins table."""
    engine = create_engine("sqlite:///:memory:")
    # Create only the table we actually query in these tests.
    UserPlugin.__table__.create(engine, checkfirst=True)
    yield engine
    UserPlugin.__table__.drop(engine)


@pytest.fixture()
def session(db_engine):
    """Transactional session that rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    s = Session()
    yield s
    s.close()
    transaction.rollback()
    connection.close()


def _make_user_plugin(
    session,
    name,
    group="web",
    plugin_type="passive",
    status=APPROVAL_APPROVED,
    suffix="",
):
    """Insert a UserPlugin and return it."""
    up = UserPlugin(
        name=name + suffix,
        description="Test plugin {}".format(name),
        category="recon",
        group=group,
        type=plugin_type,
        author="tester",
        file_path="/tmp/plugins/{}.py".format(name),
        approval_status=status,
        execution_timeout=120,
        memory_limit=134217728,
    )
    session.add(up)
    session.flush()
    return up


# ---------------------------------------------------------------------------
# get_community_plugin_dicts
# ---------------------------------------------------------------------------


class TestGetCommunityPluginDicts:
    def test_returns_empty_when_no_approved_plugins(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        result = get_community_plugin_dicts(session)
        assert result == []

    def test_excludes_pending_plugins(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        _make_user_plugin(session, "pending_plugin", status=APPROVAL_PENDING)
        result = get_community_plugin_dicts(session)
        assert result == []

    def test_excludes_rejected_plugins(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        _make_user_plugin(session, "rejected_plugin", status=APPROVAL_REJECTED)
        result = get_community_plugin_dicts(session)
        assert result == []

    def test_returns_approved_plugin(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        up = _make_user_plugin(session, "my_scanner", group="web", plugin_type="active")
        result = get_community_plugin_dicts(session)
        assert len(result) == 1
        p = result[0]
        assert p["name"] == "my_scanner"
        assert p["group"] == "web"
        assert p["type"] == "active"
        assert p["source"] == "community"
        assert p["file_path"] == up.file_path

    def test_dict_has_required_runner_fields(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        _make_user_plugin(session, "header_check")
        result = get_community_plugin_dicts(session)
        p = result[0]
        for field in (
            "key",
            "group",
            "type",
            "title",
            "name",
            "code",
            "file",
            "descrip",
            "attr",
            "min_time",
            "source",
            "file_path",
            "execution_timeout",
            "memory_limit",
        ):
            assert field in p, "missing field: {}".format(field)

    def test_key_format_matches_builtin_convention(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        _make_user_plugin(session, "test_key_plugin", plugin_type="semi_passive")
        result = get_community_plugin_dicts(session)
        p = result[0]
        # Built-in plugins use "{type}@{code}" as the key
        assert p["key"].startswith("semi_passive@community_")

    def test_code_is_community_prefixed(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        up = _make_user_plugin(session, "code_check_plugin")
        result = get_community_plugin_dicts(session)
        p = result[0]
        assert p["code"] == "community_{}".format(up.id)

    def test_title_is_humanised(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        _make_user_plugin(session, "http_header_checker")
        result = get_community_plugin_dicts(session)
        p = result[0]
        assert p["title"] == "Http Header Checker"

    def test_multiple_approved_plugins_all_returned(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        _make_user_plugin(session, "plugin_alpha")
        _make_user_plugin(session, "plugin_beta")
        result = get_community_plugin_dicts(session)
        names = {p["name"] for p in result}
        assert "plugin_alpha" in names
        assert "plugin_beta" in names

    def test_timeout_and_memory_forwarded(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        up = _make_user_plugin(session, "resource_plugin")
        result = get_community_plugin_dicts(session)
        p = result[0]
        assert p["execution_timeout"] == up.execution_timeout
        assert p["memory_limit"] == up.memory_limit


# ---------------------------------------------------------------------------
# get_all_plugin_dicts with include_community
#
# We mock plugin_gen_query so the test doesn't need the full OWTF schema
# (Plugin, TestGroup, Target, etc.) in the in-memory SQLite database.
# The community merging logic is what we want to verify here.
# ---------------------------------------------------------------------------


class TestGetAllPluginDictsWithCommunity:
    def _run_with_empty_builtins(self, session, criteria=None, include_community=True):
        """Run get_all_plugin_dicts with built-in plugin query mocked to empty."""
        from owtf.managers.plugin import get_all_plugin_dicts

        empty_query = MagicMock()
        empty_query.all.return_value = []
        with patch("owtf.managers.plugin.plugin_gen_query", return_value=empty_query):
            return get_all_plugin_dicts(session, criteria=criteria, include_community=include_community)

    def test_community_plugins_present_by_default(self, session):
        _make_user_plugin(session, "merged_plugin", suffix="_merged")
        result = self._run_with_empty_builtins(session)
        names = [p.get("name") for p in result]
        assert "merged_plugin_merged" in names

    def test_community_plugins_absent_when_disabled(self, session):
        _make_user_plugin(session, "no_show_plugin")
        result = self._run_with_empty_builtins(session, include_community=False)
        names = [p.get("name") for p in result]
        assert "no_show_plugin" not in names

    def test_group_filter_applies_to_community(self, session):
        _make_user_plugin(session, "web_plugin_a", group="web", suffix="_groupfilter")
        _make_user_plugin(session, "aux_plugin_a", group="auxiliary", suffix="_groupfilter")
        result = self._run_with_empty_builtins(session, criteria={"group": "web"})
        names = {p.get("name") for p in result}
        assert "web_plugin_a_groupfilter" in names
        assert "aux_plugin_a_groupfilter" not in names

    def test_type_filter_applies_to_community(self, session):
        _make_user_plugin(session, "passive_p", plugin_type="passive", suffix="_typefilter")
        _make_user_plugin(session, "active_p", plugin_type="active", suffix="_typefilter")
        result = self._run_with_empty_builtins(session, criteria={"type": "passive"})
        names = {p.get("name") for p in result}
        assert "passive_p_typefilter" in names
        assert "active_p_typefilter" not in names

    def test_community_entries_carry_source_marker(self, session):
        _make_user_plugin(session, "source_marker_plugin")
        result = self._run_with_empty_builtins(session)
        community_entries = [p for p in result if p.get("source") == "community"]
        assert len(community_entries) >= 1

    def test_list_filter_applies_to_community(self, session):
        """Criteria with list values should also filter community plugins."""
        _make_user_plugin(session, "active_list_p", plugin_type="active", suffix="_list")
        _make_user_plugin(session, "grep_list_p", plugin_type="grep", suffix="_list")
        result = self._run_with_empty_builtins(session, criteria={"type": ["active", "passive"]})
        names = {p.get("name") for p in result}
        assert "active_list_p_list" in names
        assert "grep_list_p_list" not in names


# ---------------------------------------------------------------------------
# PluginRunner._run_community_plugin
#
# PluginRunner imports owtf.db.session at module level and connects to
# Postgres on first use.  We patch get_scoped_session before instantiation.
# ---------------------------------------------------------------------------


def _make_runner():
    """Return a PluginRunner with minimum attributes, bypassing the DB."""
    with patch("owtf.db.session.get_scoped_session", return_value=MagicMock()):
        with patch("owtf.utils.signals.owtf_start"):
            from owtf.plugin.runner import PluginRunner

            runner = PluginRunner.__new__(PluginRunner)
            runner.plugin_count = 0
            runner.simulation = False
            return runner


class TestRunCommunityPlugin:
    def test_delegates_to_sandbox_runner(self):
        from owtf.plugin.sandbox import SandboxResult

        plugin = {
            "name": "test_plugin",
            "file_path": "/tmp/test_plugin.py",
            "execution_timeout": 60,
            "memory_limit": 134217728,
            "source": "community",
        }
        fake_result = SandboxResult(
            success=True,
            output={"findings": ["header missing"]},
            exit_code=0,
            elapsed_seconds=0.5,
        )
        runner = _make_runner()

        # Patch the reference in runner.py (where it was imported), not the source module.
        with patch("owtf.plugin.runner.target_manager") as mock_tm:
            mock_tm.get_target_url.return_value = "http://example.com"
            with patch("owtf.plugin.sandbox.SandboxRunner.run", return_value=fake_result) as mock_run:
                output = runner._run_community_plugin(plugin)

        mock_run.assert_called_once_with(
            plugin_path="/tmp/test_plugin.py",
            target_url="http://example.com",
            timeout=60,
            memory_limit=134217728,
        )
        assert isinstance(output, list)
        assert len(output) == 1
        assert output[0]["type"] == "community_output"
        assert output[0]["output"]["success"] is True

    def test_failed_sandbox_still_returns_output_list(self):
        from owtf.plugin.sandbox import SandboxResult

        plugin = {
            "name": "broken_plugin",
            "file_path": "/tmp/broken.py",
            "execution_timeout": 30,
            "memory_limit": 134217728,
            "source": "community",
        }
        fake_result = SandboxResult(
            success=False,
            error="plugin crashed",
            exit_code=1,
            elapsed_seconds=0.1,
        )
        runner = _make_runner()

        with patch("owtf.plugin.runner.target_manager") as mock_tm:
            mock_tm.get_target_url.return_value = "http://example.com"
            with patch("owtf.plugin.sandbox.SandboxRunner.run", return_value=fake_result):
                output = runner._run_community_plugin(plugin)

        assert isinstance(output, list)
        assert output[0]["output"]["success"] is False
        assert "crashed" in output[0]["output"]["error"]

    def test_timed_out_plugin_returns_timed_out_flag(self):
        from owtf.plugin.sandbox import SandboxResult

        plugin = {
            "name": "slow_plugin",
            "file_path": "/tmp/slow.py",
            "execution_timeout": 5,
            "memory_limit": 134217728,
            "source": "community",
        }
        fake_result = SandboxResult(
            success=False,
            error="Plugin execution timed out after 5s",
            exit_code=-9,
            elapsed_seconds=5.0,
            timed_out=True,
        )
        runner = _make_runner()

        with patch("owtf.plugin.runner.target_manager") as mock_tm:
            mock_tm.get_target_url.return_value = "http://example.com"
            with patch("owtf.plugin.sandbox.SandboxRunner.run", return_value=fake_result):
                output = runner._run_community_plugin(plugin)

        assert output[0]["output"]["timed_out"] is True

    def test_uses_default_timeout_when_not_in_plugin_dict(self):
        """Falls back gracefully when execution_timeout is not set."""
        from owtf.plugin.sandbox import SandboxResult

        plugin = {
            "name": "no_timeout_plugin",
            "file_path": "/tmp/no_timeout.py",
            "source": "community",
            # no execution_timeout key
        }
        fake_result = SandboxResult(success=True, output={})
        runner = _make_runner()

        with patch("owtf.plugin.runner.target_manager") as mock_tm:
            mock_tm.get_target_url.return_value = "http://example.com"
            with patch("owtf.plugin.sandbox.SandboxRunner.run", return_value=fake_result) as mock_run:
                runner._run_community_plugin(plugin)

        _call_kwargs = mock_run.call_args.kwargs
        assert _call_kwargs["timeout"] == 300  # default


# ---------------------------------------------------------------------------
# PluginRunner.run_plugin routing
# ---------------------------------------------------------------------------


class TestRunPluginRouting:
    def test_community_plugin_goes_to_sandbox(self):
        plugin = {
            "source": "community",
            "name": "sandbox_routed",
            "file_path": "/tmp/sandbox_routed.py",
            "execution_timeout": 60,
            "memory_limit": 134217728,
        }
        runner = _make_runner()

        with patch.object(
            runner,
            "_run_community_plugin",
            return_value=[{"type": "community_output", "output": {}}],
        ) as mock_sandbox:
            with patch.object(runner, "get_module") as mock_module:
                runner.run_plugin("/some/plugin/dir", plugin)

        mock_sandbox.assert_called_once_with(plugin)
        mock_module.assert_not_called()

    def test_builtin_plugin_goes_to_get_module(self):
        plugin = {
            "type": "passive",
            "file": "Http_Header_Checker@OHTTHC-001.py",
            "group": "web",
            "name": "http_header_checker",
        }
        runner = _make_runner()

        mock_mod = MagicMock()
        mock_mod.run.return_value = [{"type": "HtmlOutput", "output": {"html": "<p>ok</p>"}}]

        with patch.object(runner, "_run_community_plugin") as mock_sandbox:
            with patch.object(runner, "get_module", return_value=mock_mod):
                runner.run_plugin("/plugins/web", plugin)

        mock_sandbox.assert_not_called()
        mock_mod.run.assert_called_once_with(plugin)

    def test_missing_source_key_treated_as_builtin(self):
        """A plugin dict with no 'source' key must not go to the sandbox."""
        plugin = {
            "type": "grep",
            "file": "Some_Grep_Plugin@OGP-001.py",
            "group": "web",
            "name": "some_grep_plugin",
            # no 'source' key
        }
        runner = _make_runner()

        mock_mod = MagicMock()
        mock_mod.run.return_value = []

        with patch.object(runner, "_run_community_plugin") as mock_sandbox:
            with patch.object(runner, "get_module", return_value=mock_mod):
                runner.run_plugin("/plugins/web", plugin)

        mock_sandbox.assert_not_called()
