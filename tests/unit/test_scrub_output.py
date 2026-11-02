import pytest

from owtf.utils.strings import scrub_output


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("\x1b[2Kimportant message\n", "important message\n"),
        ("\x1b[2Kscan complete\n", "scan complete\n"),
        ("\x1b[1Gfirst line\nsecond message\n", "first line\nsecond message\n"),
        ("before\x1b[?25lhidden cursor\x1b[?25hafter", "beforehidden cursorafter"),
        ("\x1b[31mred\x1b[0m normal", "red normal"),
        ("\x1b[38;2;255;0;0mred\x1b[0m", "red"),
        ("\x1b[mdefault", "default"),
        ("message without terminal escapes\n", "message without terminal escapes\n"),
        ("café\n東京", "café\n東京"),
        ("", ""),
    ],
)
def test_scrub_output_removes_csi_sequences_without_consuming_text(output, expected):
    assert scrub_output(output) == expected
