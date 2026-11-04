import logging
import time

import pytest

from owtf.utils.formatters import FileFormatter


@pytest.fixture
def record():
    value = logging.LogRecord(
        "formatter-test", logging.WARNING, "/tmp/worker.py", 17, "Finished %s", ("job",), None, "process_output"
    )
    value.created = 0
    value.msecs = 0
    return value


def test_default_file_output_includes_level_time_and_source_context(record):
    formatter = FileFormatter()
    formatter.converter = time.gmtime

    assert formatter.format(record) == (
        "[WARNING] [1970-01-01 00:00:00,000] [File 'worker.py', line 17, in process_output] - Finished job"
    )


def test_file_output_honors_a_custom_date_format(record):
    formatter = FileFormatter(datefmt="%Y")
    formatter.converter = time.gmtime

    assert formatter.format(record) == "[WARNING] [1970] [File 'worker.py', line 17, in process_output] - Finished job"


def test_file_output_honors_an_explicit_keyword_format(record):
    assert FileFormatter(fmt="%(levelname)s:%(message)s").format(record) == "WARNING:Finished job"


def test_file_output_honors_an_explicit_positional_format(record):
    assert FileFormatter("%(levelname)s:%(message)s").format(record) == "WARNING:Finished job"
