"""
tests/test_plugin_manager_integration.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration tests for the community-plugin ↔ OWTF plugin-manager bridge.

Covers:
  - ``get_community_plugin_dicts`` returns the right shape for approved plugins
  - ``get_all_plugin_dicts`` merges community plugins into the built-in list
  - ``get_all_plugin_dicts`` filters community plugins by group / type
  - ``get_all_plugin_dicts(include_community=False)`` excludes them
  - ``PluginRunner._run_community_plugin`` loads the plugin via the module loader
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

# Register the users table (+ companions) so the user_plugins → users foreign
# keys can resolve when ``create_all`` runs against the in-memory engine.
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.plugin_output  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401

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
# for_api stripping — regression for the file_path leak on /api/v1/plugins/
#
# The trust model says file_path never leaves the server. The legacy
# ``PluginDataHandler`` calls ``get_all_plugin_dicts`` and hands the
# result straight back to the client. Anything that must not be
# serialised has to be dropped before it gets that far, so
# ``get_community_plugin_dicts`` and ``get_all_plugin_dicts`` must strip
# the runner-only fields when the caller opts in with ``for_api=True``.
# ---------------------------------------------------------------------------


class TestForApiStripsInternalFields:
    _INTERNAL = ("source", "file_path", "execution_timeout", "memory_limit")

    def test_get_community_plugin_dicts_default_keeps_runner_fields(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        _make_user_plugin(session, "runner_default_p", suffix="_for_api_a")
        result = get_community_plugin_dicts(session)
        p = result[0]
        for field in self._INTERNAL:
            assert field in p, "runner path must keep '{}'".format(field)

    def test_get_community_plugin_dicts_for_api_strips_runner_fields(self, session):
        from owtf.managers.plugin import get_community_plugin_dicts

        _make_user_plugin(session, "api_strip_p", suffix="_for_api_b")
        result = get_community_plugin_dicts(session, for_api=True)
        assert len(result) == 1
        p = result[0]
        for field in self._INTERNAL:
            assert field not in p, "API path must not expose '{}'".format(field)
        # Public metadata is still there.
        assert p["name"] == "api_strip_p_for_api_b"
        assert p["group"] == "web"
        assert p["descrip"].startswith("Test plugin")

    def test_get_all_plugin_dicts_for_api_strips_community_fields(self, session):
        """The legacy /api/v1/plugins/ endpoint calls this with for_api=True.
        Any community plugin in the response must have file_path scrubbed."""
        from owtf.managers.plugin import get_all_plugin_dicts

        _make_user_plugin(session, "list_endpoint_p", suffix="_for_api_c")

        empty_query = MagicMock()
        empty_query.all.return_value = []
        with patch("owtf.managers.plugin.plugin_gen_query", return_value=empty_query):
            result = get_all_plugin_dicts(session, for_api=True)

        # Every entry in the response must be clean of the runner-only
        # fields, no matter where it came from.
        for entry in result:
            for field in self._INTERNAL:
                assert field not in entry, "leaked '{}' in {!r}".format(field, entry)

    def test_get_all_plugin_dicts_default_still_has_runner_fields(self, session):
        """The worklist / runner path uses the default (for_api=False) and
        must still receive file_path so it can locate the plugin on disk."""
        from owtf.managers.plugin import get_all_plugin_dicts

        _make_user_plugin(session, "runner_path_p", suffix="_for_api_d")

        empty_query = MagicMock()
        empty_query.all.return_value = []
        with patch("owtf.managers.plugin.plugin_gen_query", return_value=empty_query):
            result = get_all_plugin_dicts(session)

        community = [p for p in result if p.get("source") == "community"]
        assert community, "expected at least one community entry on the runner path"
        for entry in community:
            for field in self._INTERNAL:
                assert field in entry, "runner path lost '{}'".format(field)


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
    def test_loads_module_from_plugin_file_path(self):
        plugin = {
            "name": "test_plugin",
            "file_path": "/tmp/test_plugin.py",
            "source": "community",
        }
        runner = _make_runner()

        mock_mod = MagicMock()
        mock_mod.run.return_value = [{"type": "community_output", "output": {"findings": ["x"]}}]

        with patch("owtf.plugin.runner.target_manager") as mock_tm:
            mock_tm.get_target_url.return_value = "http://example.com"
            with patch.object(runner, "get_module", return_value=mock_mod) as mock_get:
                output = runner._run_community_plugin(plugin)

        mock_get.assert_called_once_with("", "test_plugin.py", "/tmp/")
        mock_mod.run.assert_called_once_with(plugin)
        assert output[0]["output"]["findings"] == ["x"]

    def test_propagates_plugin_exception(self):
        plugin = {
            "name": "broken_plugin",
            "file_path": "/tmp/broken.py",
            "source": "community",
        }
        runner = _make_runner()

        mock_mod = MagicMock()
        mock_mod.run.side_effect = RuntimeError("plugin crashed")

        with patch("owtf.plugin.runner.target_manager") as mock_tm:
            mock_tm.get_target_url.return_value = "http://example.com"
            with patch.object(runner, "get_module", return_value=mock_mod):
                with pytest.raises(RuntimeError, match="plugin crashed"):
                    runner._run_community_plugin(plugin)

    def test_uses_explicit_target_url_when_provided(self):
        plugin = {
            "name": "explicit_target_plugin",
            "file_path": "/tmp/explicit.py",
            "source": "community",
            "target_url": "http://override.example.com",
        }
        runner = _make_runner()

        mock_mod = MagicMock()
        mock_mod.run.return_value = []

        with patch("owtf.plugin.runner.target_manager") as mock_tm:
            mock_tm.get_target_url.return_value = "http://from-manager.example.com"
            with patch.object(runner, "get_module", return_value=mock_mod):
                runner._run_community_plugin(plugin)

        mock_mod.run.assert_called_once_with(plugin)


# ---------------------------------------------------------------------------
# PluginRunner.run_plugin routing
# ---------------------------------------------------------------------------


class TestRunPluginRouting:
    def test_community_plugin_goes_to_community_path(self):
        plugin = {
            "source": "community",
            "name": "community_routed",
            "file_path": "/tmp/community_routed.py",
        }
        runner = _make_runner()

        with patch.object(
            runner,
            "_run_community_plugin",
            return_value=[{"type": "community_output", "output": {}}],
        ) as mock_community:
            with patch.object(runner, "get_module") as mock_module:
                runner.run_plugin("/some/plugin/dir", plugin)

        mock_community.assert_called_once_with(plugin)
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

        with patch.object(runner, "_run_community_plugin") as mock_community:
            with patch.object(runner, "get_module", return_value=mock_mod):
                runner.run_plugin("/plugins/web", plugin)

        mock_community.assert_not_called()
        mock_mod.run.assert_called_once_with(plugin)

    def test_missing_source_key_treated_as_builtin(self):
        """A plugin dict with no 'source' key must take the built-in path."""
        plugin = {
            "type": "grep",
            "file": "Some_Grep_Plugin@OGP-001.py",
            "group": "web",
            "name": "some_grep_plugin",
        }
        runner = _make_runner()

        mock_mod = MagicMock()
        mock_mod.run.return_value = []

        with patch.object(runner, "_run_community_plugin") as mock_community:
            with patch.object(runner, "get_module", return_value=mock_mod):
                runner.run_plugin("/plugins/web", plugin)

        mock_community.assert_not_called()
