import logging
from unittest.mock import Mock

import pytest

from owtf.config import Config
from owtf.db import session as db_session
from owtf.models.error import Error


@pytest.fixture
def params(monkeypatch):
    # Importing params also constructs the shared instance, which opens a database session.
    session = Mock()
    with monkeypatch.context() as patch:
        patch.setattr(db_session, "get_scoped_session", lambda: session)
        from owtf.plugin import params as module

        patch.setattr(module, "get_scoped_session", lambda: session)
        plugin_params = module.PluginParams()

    monkeypatch.setattr(Error, "add_error", Mock())
    monkeypatch.setattr(module, "config_handler", Config())
    yield plugin_params
    module.owtf_start.disconnect(plugin_params.handle_signal)


@pytest.fixture
def plugin():
    return {"code": "OWTF-ADoS-001", "type": "aux", "file": "Direct_DoS_Launcher@OWTF-ADoS-001.py"}


@pytest.fixture
def schema():
    return {
        "Description": "Example auxiliary plugin",
        "Mandatory": {"RHOST": "target host", "RPORT": "target port"},
        "Optional": {"REPEAT_DELIM": "delimiter"},
    }


def test_get_args_accepts_existing_plugin_call_and_expands_repeated_values(params, schema, plugin):
    params.raw_args = ["RHOST=first.example,second.example", "RPORT=80,81", "REPEAT_DELIM=,"]

    assert params.get_args(schema, plugin) == [
        {"RHOST": "first.example", "RPORT": "80", "REPEAT_DELIM": ","},
        {"RHOST": "second.example", "RPORT": "80", "REPEAT_DELIM": ","},
        {"RHOST": "first.example", "RPORT": "81", "REPEAT_DELIM": ","},
        {"RHOST": "second.example", "RPORT": "81", "REPEAT_DELIM": ","},
    ]
    assert plugin["argError"] is False


def test_get_args_lists_declared_options_and_usage(params, schema, plugin, caplog):
    params.raw_args = ["O"]

    with caplog.at_level(logging.INFO), pytest.raises(SystemExit, match="User is only viewing options"):
        params.get_args(schema, plugin)

    assert "Example auxiliary plugin" in caplog.text
    assert "mandatory parameters:" in caplog.text
    assert "Optional parameters:" in caplog.text
    assert "Usage: RHOST=? RPORT=? REPEAT_DELIM=?" in caplog.text


def test_process_args_preserves_values_after_first_equals(params):
    params.raw_args = ["RHOST=myRHOST.local", "URL=http://example.test/?URL=y", "EMPTY="]

    assert params.process_args() is True
    assert params.args == {"RHOST": "myRHOST.local", "URL": "http://example.test/?URL=y", "EMPTY": ""}


def test_set_args_basic_records_resolved_values_without_inserting_defaults(params, plugin):
    params.raw_args = ["RHOST=127.0.0.1"]
    assert params.process_args() is True
    resolved = {"RHOST": "127.0.0.1", "RPORT": "8080"}

    assert params.set_args_basic(resolved, plugin) == [resolved]
    assert plugin["args"] == "RHOST=127.0.0.1 RPORT=8080"
    assert params.args == {"RHOST": "127.0.0.1"}


def test_get_args_uses_each_plugins_own_config_default(params, schema, plugin):
    from owtf.plugin.params import config_handler

    params.raw_args = ["RHOST=127.0.0.1"]
    other_plugin = {**plugin, "code": "OWTF-OTHER-001"}
    config_handler.set_val("RPORT", "80")
    config_handler.set_val("OWTF-ADoS-001_aux_RPORT", "8080")

    assert params.get_args(schema, plugin) == [{"RHOST": "127.0.0.1", "RPORT": "8080"}]
    assert params.get_args(schema, other_plugin) == [{"RHOST": "127.0.0.1", "RPORT": "80"}]
    assert plugin["args"] == "RHOST=127.0.0.1 RPORT=8080"
    assert other_plugin["args"] == "RHOST=127.0.0.1 RPORT=80"


@pytest.mark.parametrize(
    ("raw_args", "error_message"),
    [
        (["RHOST"], "arguments should be in NAME=VALUE format"),
        (["RHOST=127.0.0.1"], "requires argument: 'RPORT'"),
    ],
)
def test_get_args_reports_errors_with_its_session(params, schema, plugin, raw_args, error_message):
    params.raw_args = raw_args

    assert params.get_args(schema, plugin) == []
    assert plugin["argError"] is True
    Error.add_error.assert_called_once()
    session, message, trace = Error.add_error.call_args.args
    assert session is params.session
    assert error_message in message
    assert trace == "user"
