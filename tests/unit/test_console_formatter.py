import io
import logging

import pytest

from owtf.utils.formatters import ConsoleFormatter


@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR])
def test_console_formatting_does_not_change_later_handler_output(level):
    console_output = io.StringIO()
    file_output = io.StringIO()
    console_handler = logging.StreamHandler(console_output)
    console_handler.setFormatter(ConsoleFormatter())
    file_handler = logging.StreamHandler(file_output)
    file_handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger = logging.Logger("formatter-test", level=logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.log(level, "Operation %s", "finished")

    assert file_output.getvalue() == f"{logging.getLevelName(level)}:Operation finished\n"


def test_formatting_the_same_record_twice_does_not_stack_prefixes():
    record = logging.LogRecord("formatter-test", logging.INFO, __file__, 1, "Operation %s", ("finished",), None)
    formatter = ConsoleFormatter()

    assert formatter.format(record) == formatter.format(record)


def test_console_output_retains_its_color_and_prefix():
    record = logging.LogRecord("formatter-test", logging.INFO, __file__, 1, "Operation %s", ("finished",), None)

    assert ConsoleFormatter().format(record) == "\033[94m[+] Operation finished\033[0m"
