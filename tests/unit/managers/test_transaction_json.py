import base64
import json
from datetime import datetime

import pytest

from owtf.models.command import Command  # noqa: F401
from owtf.models.grep_output import GrepOutput  # noqa: F401
from owtf.models.plugin import Plugin  # noqa: F401
from owtf.models.plugin_output import PluginOutput  # noqa: F401
from owtf.models.session import Session  # noqa: F401
from owtf.models.test_group import TestGroup as _TestGroup  # noqa: F401
from owtf.models.transaction import Transaction
from owtf.models.url import Url  # noqa: F401
from owtf.models.work import Work  # noqa: F401


@pytest.mark.parametrize("as_bytes", [False, True])
def test_binary_body_is_json_safe_and_not_encoded_twice(as_bytes):
    raw = b"\x00\xff\x80binary"
    encoded = base64.b64encode(raw)
    row = Transaction(
        id=1,
        local_timestamp=datetime(2026, 1, 1),
        binary_response=True,
        response_body=encoded if as_bytes else encoded.decode("ascii"),
    )
    result = row.to_dict(include_raw_data=True)
    assert base64.b64decode(result["response_body"]) == raw
    assert json.loads(json.dumps(result))["response_body"] == encoded.decode("ascii")


@pytest.mark.parametrize("body", ["snowman \u2603", "snowman \u2603".encode("utf-8")])
def test_text_body_is_json_safe(body):
    row = Transaction(id=1, local_timestamp=datetime(2026, 1, 1), binary_response=False, response_body=body)
    assert json.loads(json.dumps(row.to_dict(include_raw_data=True)))["response_body"] == "snowman \u2603"


def test_summary_omits_raw_body_without_mutating_model():
    row = Transaction(id=1, local_timestamp=datetime(2026, 1, 1), binary_response=True, response_body=b"AA==")
    assert "response_body" not in row.to_dict()
    assert row.response_body == b"AA=="
