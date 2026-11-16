"""The error-note API updates an error row and rejects invalid requests."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import tornado.web
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from owtf.lib.exceptions import InvalidErrorReference
from owtf.models.error import Error

_ERROR_HANDLER_CLASS = None


def error_handler_class():
    global _ERROR_HANDLER_CLASS
    if _ERROR_HANDLER_CLASS is not None:
        return _ERROR_HANDLER_CLASS
    # Importing the plugin-output manager creates a session; keep this test offline.
    with patch("owtf.db.session.get_scoped_session", return_value=Mock()):
        from owtf.api.handlers.misc import ErrorDataHandler

    _ERROR_HANDLER_CLASS = ErrorDataHandler
    return _ERROR_HANDLER_CLASS


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Error.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_update_error_persists_user_message(session):
    error = Error(owtf_message="scan failed", traceback="trace")
    session.add(error)
    session.commit()

    Error.update_error(session, error.id, "Reviewed by operator")

    session.expire_all()
    assert session.query(Error).filter_by(id=error.id).one().user_message == "Reviewed by operator"


def test_update_error_rejects_missing_id(session):
    with pytest.raises(InvalidErrorReference):
        Error.update_error(session, 999, "Reviewed by operator")


def test_patch_passes_user_message_to_model():
    ErrorDataHandler = error_handler_class()
    handler = SimpleNamespace(
        request=SimpleNamespace(arguments={"user_message": ["Reviewed by operator"]}),
        session=object(),
        finish=Mock(),
    )

    with patch.object(Error, "update_error") as update:
        ErrorDataHandler.patch(handler, "42")

    update.assert_called_once_with(handler.session, "42", "Reviewed by operator")
    handler.finish.assert_called_once_with()


def test_patch_rejects_missing_message():
    ErrorDataHandler = error_handler_class()
    handler = SimpleNamespace(
        request=SimpleNamespace(arguments={}),
        session=object(),
        finish=Mock(),
    )

    with pytest.raises(tornado.web.HTTPError) as exc:
        ErrorDataHandler.patch(handler, "42")

    assert exc.value.status_code == 400
    handler.finish.assert_not_called()


def test_patch_rejects_unknown_error_id():
    ErrorDataHandler = error_handler_class()
    handler = SimpleNamespace(
        request=SimpleNamespace(arguments={"user_message": ["Reviewed by operator"]}),
        session=object(),
        finish=Mock(),
    )

    with patch.object(Error, "update_error", side_effect=InvalidErrorReference("missing")):
        with pytest.raises(tornado.web.HTTPError) as exc:
            ErrorDataHandler.patch(handler, "999")

    assert exc.value.status_code == 400
    handler.finish.assert_not_called()
