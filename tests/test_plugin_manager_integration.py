"""End-to-end tests for approving a community plugin and running it.

Under the option-A design, an approved community plugin is mirrored into
the ``plugins`` table so it participates in the standard worklist FK,
the standard worker lookup path, and the standard runner dispatch. The
tests exercise that whole flow:

    approve_community_plugin  ->  plugins row exists
                              ->  add_work accepts the plugin_key
                              ->  get_work_for_target returns the Work with .plugin populated
                              ->  PluginRunner.run_plugin routes to _run_community_plugin
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Register every model so create_all can build a self-consistent schema.
import owtf.models.api_token  # noqa: F401
import owtf.models.command  # noqa: F401
import owtf.models.config  # noqa: F401
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.error  # noqa: F401
import owtf.models.grep_output  # noqa: F401
import owtf.models.plugin_output  # noqa: F401
import owtf.models.resource  # noqa: F401
import owtf.models.session  # noqa: F401
import owtf.models.target  # noqa: F401
import owtf.models.test_group  # noqa: F401
import owtf.models.transaction  # noqa: F401
import owtf.models.url  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
import owtf.models.work  # noqa: F401
from owtf.db.model_base import Model
from owtf.managers.community_plugin import (
    _plugin_code,
    _plugin_key,
    approve_community_plugin,
    delete_community_plugin,
    reject_community_plugin,
)
from owtf.managers.plugin import get_all_plugin_dicts, plugin_gen_query
from owtf.managers.poutput import poutput_gen_query
from owtf.models.plugin import Plugin
from owtf.models.plugin_output import PluginOutput
from owtf.models.target import Target
from owtf.models.test_group import TestGroup as GroupModel
from owtf.models.user_plugin import APPROVAL_APPROVED, APPROVAL_PENDING, UserPlugin
from owtf.models.work import Work


@pytest.fixture()
def engine():
    """Fresh in-memory SQLite engine with every relevant table."""
    eng = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(eng)
    yield eng


@pytest.fixture()
def session(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def _make_user_plugin(session, tmp_path, name="test_plugin", status=APPROVAL_PENDING):
    path = tmp_path / "{}.py".format(name)
    path.write_text("DESCRIPTION='x'\ndef run(PluginInfo):\n    return [{'ok': True}]\n")
    up = UserPlugin(
        name=name,
        description="test",
        group="web",
        type="passive",
        author="tester",
        file_path=str(path),
        approval_status=status,
        execution_timeout=30,
    )
    session.add(up)
    session.commit()
    session.refresh(up)
    return up


class TestApproveSyncsToPluginsTable:
    def test_approve_inserts_matching_plugins_row(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        approve_community_plugin(session, up.id)

        row = session.query(Plugin).filter_by(key=_plugin_key(up)).first()
        assert row is not None
        assert row.source == "community"
        assert row.file_path == up.file_path
        assert row.group == up.group
        assert row.type == up.type
        assert row.name == up.name
        assert row.code == _plugin_code(up)
        assert row.key == "passive@COMMUNITY-{}".format(up.id)

        test_group = session.query(GroupModel).get(row.code)
        assert test_group is not None
        assert test_group.descrip == up.description

    def test_re_approve_updates_existing_row(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path, status=APPROVAL_APPROVED)
        approve_community_plugin(session, up.id)
        approve_community_plugin(session, up.id)
        rows = session.query(Plugin).filter_by(key=_plugin_key(up)).all()
        assert len(rows) == 1

    def test_reject_removes_the_plugins_row(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        approve_community_plugin(session, up.id)
        assert session.query(Plugin).filter_by(key=_plugin_key(up)).count() == 1

        reject_community_plugin(session, up.id, "no thanks")
        assert session.query(Plugin).filter_by(key=_plugin_key(up)).count() == 0
        assert session.query(GroupModel).get(_plugin_code(up)) is None

    def test_reject_without_prior_approval_is_a_noop_on_plugins(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        reject_community_plugin(session, up.id, "not approved yet")
        assert session.query(Plugin).filter_by(key=_plugin_key(up)).count() == 0

    def test_delete_removes_the_plugins_row(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        approve_community_plugin(session, up.id)
        delete_community_plugin(session, up.id)
        assert session.query(Plugin).filter_by(key=_plugin_key(up)).count() == 0
        assert session.query(GroupModel).get(_plugin_code(up)) is None


class TestPluginGenQuerySeesApprovedCommunityPlugins:
    def test_query_returns_community_plugin_with_test_group(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        approve_community_plugin(session, up.id)

        keys = [p.key for p in plugin_gen_query(session, {}).all()]
        assert _plugin_key(up) in keys

    def test_group_filter_still_works(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        approve_community_plugin(session, up.id)
        got = plugin_gen_query(session, {"group": "web"}).all()
        assert any(p.key == _plugin_key(up) for p in got)

    def test_get_all_plugin_dicts_includes_source_and_file_path(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        approve_community_plugin(session, up.id)
        dicts = get_all_plugin_dicts(session)
        entry = next(d for d in dicts if d.get("key") == _plugin_key(up))
        assert entry["source"] == "community"
        assert entry["file_path"] == up.file_path

    def test_selects_by_name_or_stable_code(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        approve_community_plugin(session, up.id)

        by_name = get_all_plugin_dicts(session, {"code": up.name})
        by_code = get_all_plugin_dicts(session, {"code": [_plugin_code(up)]})

        assert [plugin["key"] for plugin in by_name] == [_plugin_key(up)]
        assert [plugin["key"] for plugin in by_code] == [_plugin_key(up)]


class TestWorklistEndToEnd:
    """The regression viyatb pointed at: approve, then queue, then fetch."""

    def test_add_work_accepts_community_plugin_key(self, session, tmp_path):
        up = _make_user_plugin(session, tmp_path)
        approve_community_plugin(session, up.id)

        # SQLite does not enforce FKs by default, so this asserts the ORM
        # backref path and the value round-trip. Real postgres FK
        # enforcement lives in TestWorklistEndToEndPostgres below, gated
        # on TEST_POSTGRES_URL so it only runs where a live server is
        # available.
        work = Work(target_id=None, plugin_key=_plugin_key(up), active=True)
        session.add(work)
        session.commit()

        got = session.query(Work).filter_by(plugin_key=_plugin_key(up)).one()
        assert got.plugin is not None
        assert got.plugin.source == "community"
        assert got.plugin.file_path == up.file_path


@pytest.mark.usefixtures("_stub_scoped_session")
class TestExecutionAndReportEndToEnd:
    def test_approved_plugin_executes_and_is_available_to_reports(self, session, tmp_path):
        from owtf.managers.target import target_manager
        from owtf.plugin.runner import PluginRunner

        up = _make_user_plugin(session, tmp_path, name="reportable_plugin")
        approve_community_plugin(session, up.id)
        plugin = get_all_plugin_dicts(session, {"code": up.name})[0]

        target = Target(target_url="https://example.com", host_ip="127.0.0.1", port_number="443")
        session.add(target)
        session.commit()
        session.refresh(target)

        runner = PluginRunner()
        runner.plugin_group = "web"
        runner.only_plugins_list = [_plugin_code(up)]
        runner.except_plugins_list = []
        runner.force_overwrite = False
        runner.simulation = False
        target_manager.target_id = target.id
        target_manager.target_config = {"target_url": target.target_url}
        target_manager.path_config = {"partial_url_output_path": str(tmp_path / "partial")}

        with (
            patch.object(runner, "rank_plugin", return_value=-1),
            patch("owtf.plugin.runner.get_output_dir_target", return_value=str(tmp_path)),
        ):
            output = runner.process_plugin(session, None, plugin)

        assert output == [{"ok": True}]
        saved = session.query(PluginOutput).filter_by(plugin_key=_plugin_key(up)).one()
        assert saved.plugin_code == _plugin_code(up)
        assert saved.to_dict(inc_output=True)["output"] == output

        report_rows = poutput_gen_query(
            session,
            {"plugin_code": _plugin_code(up)},
            target.id,
        ).all()
        assert [row.id for row in report_rows] == [saved.id]
        assert GroupModel.get_by_code(session, _plugin_code(up))["descrip"] == up.description


@pytest.mark.usefixtures("_stub_scoped_session")
class TestExecutionTimeoutFlowsFromWorkRowIntoRunner:
    """viyatb's PR-4 blocker: the mirror must carry execution_timeout so a
    real queued run sees the configured bound instead of timeout=0.

    Path exercised end to end:
        UserPlugin.execution_timeout
          -> approve_community_plugin  (mirrors into plugins.execution_timeout)
          -> Work row referencing the mirror
          -> _derive_work_dict(work)
          -> work_dict["plugin"]["execution_timeout"]
          -> PluginRunner._run_community_plugin reads plugin["execution_timeout"]
    """

    def test_derive_work_dict_carries_execution_timeout(self, session, tmp_path):
        from owtf.managers.worklist import _derive_work_dict

        up = _make_user_plugin(session, tmp_path, name="timed_plugin")
        # Confirm the source-of-truth value the uploader configured.
        assert up.execution_timeout == 30

        approve_community_plugin(session, up.id)

        work = Work(target_id=None, plugin_key=_plugin_key(up), active=True)
        session.add(work)
        session.commit()
        session.refresh(work)

        work_dict = _derive_work_dict(work)
        # This is exactly the dict the worker hands to the runner.
        assert work_dict["plugin"]["source"] == "community"
        assert work_dict["plugin"]["file_path"] == up.file_path
        assert work_dict["plugin"]["execution_timeout"] == 30, (
            "mirror must carry execution_timeout so the runner enforces "
            "the configured bound instead of falling back to 0"
        )

    def test_runner_reads_the_timeout_the_work_dict_carries(self, session, tmp_path):
        """Read the same value the runner does, from the same dict shape."""
        from owtf.managers.worklist import _derive_work_dict

        up = _make_user_plugin(session, tmp_path, name="timed_plugin_runner")
        up.execution_timeout = 120
        session.commit()
        approve_community_plugin(session, up.id)

        work = Work(target_id=None, plugin_key=_plugin_key(up), active=True)
        session.add(work)
        session.commit()
        session.refresh(work)

        plugin_dict = _derive_work_dict(work)["plugin"]
        # This is the exact expression PluginRunner._run_community_plugin uses.
        timeout = int(plugin_dict.get("execution_timeout") or 0)
        assert timeout == 120, "runner would fall back to timeout=0 without this"


@pytest.mark.skipif(
    not os.environ.get("TEST_POSTGRES_URL"),
    reason="TEST_POSTGRES_URL is not set; skipping live postgres FK check",
)
class TestWorklistEndToEndPostgres:
    """Prove the FK is satisfied on real postgres, which does enforce it.

    Set TEST_POSTGRES_URL to a psycopg2 URL for an empty scratch database
    to run these, for example::

        TEST_POSTGRES_URL=postgresql+psycopg2://owtf:owtf@127.0.0.1:5432/owtf_test pytest
    """

    @pytest.fixture()
    def pg_engine(self):
        from owtf.db.upgrade import run_startup_upgrades

        url = os.environ["TEST_POSTGRES_URL"]
        eng = create_engine(url)
        Model.metadata.drop_all(eng)
        Model.metadata.create_all(eng)
        run_startup_upgrades(eng)
        yield eng
        Model.metadata.drop_all(eng)
        eng.dispose()

    @pytest.fixture()
    def pg_session(self, pg_engine):
        Session = sessionmaker(bind=pg_engine)
        s = Session()
        yield s
        s.close()

    def test_add_work_with_unknown_plugin_key_violates_fk(self, pg_session):
        from sqlalchemy.exc import IntegrityError

        pg_session.add(Work(target_id=None, plugin_key="does_not_exist@community_999", active=True))
        with pytest.raises(IntegrityError):
            pg_session.commit()
        pg_session.rollback()

    def test_add_work_with_approved_plugin_key_is_accepted(self, pg_session, tmp_path):
        up = _make_user_plugin(pg_session, tmp_path)
        approve_community_plugin(pg_session, up.id)

        pg_session.add(Work(target_id=None, plugin_key=_plugin_key(up), active=True))
        pg_session.commit()

        got = pg_session.query(Work).filter_by(plugin_key=_plugin_key(up)).one()
        assert got.plugin is not None
        assert got.plugin.source == "community"


@pytest.fixture()
def _stub_scoped_session():
    """Stop PluginRunner from opening a real DB connection.

    ``owtf.plugin.runner`` builds a module-level ``runner = PluginRunner()``
    singleton, and ``PluginRunner.__init__`` calls ``get_scoped_session()``.
    Both the module import and every direct construction need the stub, so
    we patch the source (``owtf.db.session.get_scoped_session``) before the
    runner module is imported for the first time. None of the tests below
    exercise ``self.session``.
    """
    with patch("owtf.db.session.get_scoped_session"):
        yield


@pytest.mark.usefixtures("_stub_scoped_session")
class TestRunnerDispatchOnPluginDict:
    def test_run_plugin_routes_to_community_when_source_is_community(self, tmp_path):
        from owtf.plugin.runner import PluginRunner

        plugin = {
            "source": "community",
            "name": "x",
            "type": "passive",
            "group": "web",
            "file_path": str(tmp_path / "x.py"),
            "target_url": "https://example.com",
        }
        r = PluginRunner()
        with patch.object(r, "_run_community_plugin", return_value=[{"ok": True}]) as spy:
            out = r.run_plugin(None, plugin)
        spy.assert_called_once_with(plugin)
        assert out == [{"ok": True}]

    def test_run_plugin_takes_builtin_path_when_source_is_missing(self, tmp_path):
        from owtf.plugin.runner import PluginRunner

        r = PluginRunner()
        plugin = {"type": "passive", "group": "web", "file": "x.py"}
        fake_mod = MagicMock()
        fake_mod.run.return_value = [{"builtin": True}]
        with patch.object(r, "get_module", return_value=fake_mod):
            out = r.run_plugin("/plugins", plugin)
        assert out == [{"builtin": True}]


@pytest.mark.usefixtures("_stub_scoped_session")
class TestCommunityPluginTimeoutEnforcement:
    def test_alarm_kills_a_slow_plugin_on_the_main_thread(self, tmp_path):
        """A community plugin that ignores its execution_timeout must be
        interrupted by the SIGALRM watchdog when the runner is called
        from the main thread (the test-run request path)."""
        from owtf.plugin.runner import CommunityPluginTimeout, PluginRunner

        slow = tmp_path / "slow.py"
        slow.write_text(
            "import time\nDESCRIPTION='slow'\ndef run(PluginInfo):\n    time.sleep(5)\n    return [{'never': True}]\n"
        )
        r = PluginRunner()
        with pytest.raises(CommunityPluginTimeout):
            r._run_community_plugin(
                {
                    "name": "slow",
                    "file_path": str(slow),
                    "type": "passive",
                    "group": "web",
                    "execution_timeout": 1,
                }
            )
