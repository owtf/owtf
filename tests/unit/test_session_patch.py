"""Session PATCH rejects malformed requests before calling session managers."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from owtf.api.handlers.session import OWTFSessionHandler
from owtf.lib.exceptions import APIError


def handler_with_target(target_id=None):
    return SimpleNamespace(
        get_argument=lambda name, default=None: target_id if name == "target_id" else default,
        session=object(),
        success=Mock(),
    )


@pytest.mark.parametrize("action", ["add", "remove"])
def test_patch_rejects_noninteger_target_id(action):
    handler = handler_with_target("abc")

    with pytest.raises(APIError) as exc:
        OWTFSessionHandler.patch(handler, "1", action)

    assert exc.value.status_code == 400
    handler.success.assert_not_called()


def test_patch_rejects_missing_action():
    handler = handler_with_target("2")

    with pytest.raises(APIError) as exc:
        OWTFSessionHandler.patch(handler, "1")

    assert exc.value.status_code == 400
    handler.success.assert_not_called()


@pytest.mark.parametrize("action", ["add", "remove"])
def test_patch_rejects_missing_target_id(action):
    handler = handler_with_target()

    with pytest.raises(APIError) as exc:
        OWTFSessionHandler.patch(handler, "1", action)

    assert exc.value.status_code == 400
    handler.success.assert_not_called()


@pytest.mark.parametrize(
    ("action", "manager_name"),
    [("add", "add_target_to_session"), ("remove", "remove_target_from_session")],
)
def test_patch_passes_valid_target_id_to_manager(action, manager_name):
    handler = handler_with_target("2")

    with patch(f"owtf.api.handlers.session.{manager_name}") as manager:
        OWTFSessionHandler.patch(handler, "1", action)

    manager.assert_called_once_with(handler.session, 2, session_id=1)
    handler.success.assert_called_once_with(None)


def test_patch_activates_session_without_target_id():
    handler = handler_with_target()

    with patch("owtf.api.handlers.session.Session.set_by_id") as set_by_id:
        OWTFSessionHandler.patch(handler, "1", "activate")

    set_by_id.assert_called_once_with(handler.session, 1)
    handler.success.assert_called_once_with(None)
