"""The API should not rebuild the database engine and schema on every request."""

from unittest.mock import MagicMock, patch

from owtf.db import session as db_session


def test_get_db_engine_reuses_initialized_engine():
    engine = MagicMock()
    db_session.get_db_engine.cache_clear()
    try:
        with patch.object(db_session, "create_engine", return_value=engine) as create_engine:
            with patch.object(db_session.Model.metadata, "create_all") as create_all:
                with patch.object(db_session, "upgrade_add_fingerprint_column") as upgrade:
                    assert db_session.get_db_engine() is engine
                    assert db_session.get_db_engine() is engine

        create_engine.assert_called_once()
        create_all.assert_called_once_with(engine)
        upgrade.assert_called_once_with(engine)
    finally:
        db_session.get_db_engine.cache_clear()
