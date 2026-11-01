from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def requester():
    # The module-level requester normally creates a database session at import.
    with patch("owtf.db.session.get_scoped_session", return_value=MagicMock()):
        from owtf.requester.base import Requester

        return Requester.__new__(Requester)


@pytest.mark.parametrize(
    "body",
    [
        "username=alice&password=secret",
        "token=a=b==",
        "name=Alice+Smith&path=%2Fadmin%3Fx%3D1",
        "item=one&item=two&empty=",
        '{"message": "hello=world"}',
        "message=café",
    ],
)
def test_string_post_body_is_preserved(requester, body):
    assert requester.get_post(body) == body.encode("utf-8")


@pytest.mark.parametrize("body", [b"token=a=b==", bytearray(b"x=1&x=2")])
def test_binary_post_body_is_preserved(requester, body):
    assert requester.get_post(body) is body


def test_mapping_post_body_is_urlencoded(requester):
    assert requester.get_post({"name": "Alice Smith", "path": "/admin"}) == (b"name=Alice+Smith&path=%2Fadmin")


@pytest.mark.parametrize("body", [None, ""])
def test_absent_post_body_stays_absent(requester, body):
    assert requester.get_post(body) is None
