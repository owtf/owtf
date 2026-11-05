"""Each request timer must retain its own start and end timestamps."""

import datetime
from unittest.mock import patch

from owtf.utils.timer import Timer


def test_starting_another_timer_does_not_replace_first_start():
    first = Timer()
    second = Timer()
    first_start = datetime.datetime(2026, 1, 1, 12, 0, 0)
    second_start = datetime.datetime(2026, 1, 1, 12, 0, 1)

    with patch.object(Timer, "get_current_date_time", side_effect=[first_start, second_start]):
        first.start_timer("Request")
        second.start_timer("Request")

    assert first.get_start_date_time("Request") == first_start
    assert second.get_start_date_time("Request") == second_start


def test_ending_one_timer_does_not_set_another_timer_end():
    first = Timer()
    second = Timer()
    first.start_timer("Request")
    second.start_timer("Request")

    first.end_timer("Request")

    assert "end" not in second.timers["Request"]
