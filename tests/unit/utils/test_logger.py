"""Tests for OWTF's root logger handler lifecycle."""

import logging

from owtf.utils.logger import OWTFLogger


def test_enable_logging_closes_replaced_handlers(tmp_path, monkeypatch):
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    old_handler = logging.FileHandler(tmp_path / "old.log")
    root_logger.handlers = [old_handler]
    monkeypatch.setattr("owtf.utils.logger.get_logs_dir", lambda: str(tmp_path))
    monkeypatch.setattr("owtf.utils.logger.get_log_path", lambda name: str(tmp_path / f"{name}.log"))

    try:
        OWTFLogger().enable_logging(process_name="worker")
        assert old_handler.stream is None
    finally:
        for handler in root_logger.handlers:
            handler.close()
        root_logger.handlers = original_handlers
        old_handler.close()


def test_disable_console_logging_is_safe_without_handlers():
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    root_logger.handlers = []

    try:
        OWTFLogger().disable_console_logging()
    finally:
        root_logger.handlers = original_handlers


def test_disable_console_logging_removes_only_stream_handler():
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    file_handler = logging.NullHandler()
    stream_handler = logging.StreamHandler()
    root_logger.handlers = [file_handler, stream_handler]

    try:
        OWTFLogger().disable_console_logging()
        assert root_logger.handlers == [file_handler]
        assert stream_handler not in root_logger.handlers
    finally:
        root_logger.handlers = original_handlers
        file_handler.close()
        stream_handler.close()
