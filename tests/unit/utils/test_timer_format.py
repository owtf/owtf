"""Regression coverage for human-readable elapsed times."""

import datetime

from owtf.utils.timer import Timer


def test_timedelta_retains_hours_minutes_seconds_and_milliseconds():
    elapsed = datetime.timedelta(hours=1, minutes=2, seconds=3, milliseconds=456)

    assert Timer().get_time_as_str(elapsed) == "1h,  2m,  3s, 456ms"


def test_seconds_string_retains_all_duration_components():
    assert Timer().get_time_human("3723.456") == "1h,  2m,  3s, 456ms"


def test_short_duration_omits_zero_hours_and_minutes():
    assert Timer().get_time_as_str(datetime.timedelta(seconds=4, milliseconds=7)) == "4s,   7ms"


def test_fractional_seconds_are_scaled_as_milliseconds():
    assert Timer().get_time_human("4.7") == "4s, 700ms"
