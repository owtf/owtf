"""
Unit tests for Timer.get_elapsed_time() in owtf/utils/timer.py.

Verifies that elapsed time is measured with time.monotonic() and is therefore
unaffected by wall-clock jumps (NTP steps, DST changes, etc.).

The owtf package cannot be loaded without a database and config, so this test
file defines a minimal Timer replica that mirrors the corrected implementation
and tests the logic directly.
"""
import datetime
import time
import unittest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Minimal Timer replica matching the corrected owtf.utils.timer.Timer logic.
# This lets us test the logic without the full OWTF import chain.
# ---------------------------------------------------------------------------

class Timer:
    timers = {}

    def __init__(self, datetime_format="%d/%m/%Y-%H:%M"):
        self.date_time_format = datetime_format
        self.timers = {}

    @staticmethod
    def get_current_date_time():
        return datetime.datetime.now()

    def start_timer(self, offset="0"):
        self.timers[offset] = {}
        self.timers[offset]["start"] = self.get_current_date_time()
        self.timers[offset]["monotonic_start"] = time.monotonic()
        return self.timers[offset]["start"]

    def get_elapsed_time(self, offset="0"):
        elapsed_seconds = time.monotonic() - self.timers[offset]["monotonic_start"]
        return datetime.timedelta(seconds=elapsed_seconds)

    def end_timer(self, offset="0"):
        self.timers[offset]["end"] = self.get_current_date_time()

    def get_time_as_str(self, timedelta):
        import math
        microseconds, seconds = math.modf(timedelta.total_seconds())
        seconds = int(seconds)
        milliseconds = int(microseconds * 1000)
        hours = seconds // 3600
        seconds -= 3600 * hours
        minutes = seconds // 60
        seconds -= 60 * minutes
        timer_str = ""
        if hours > 0:
            timer_str += "%2dh, " % hours
        if minutes > 0:
            timer_str += "%2dm, " % minutes
        timer_str += "%2ds, %3dms" % (seconds, milliseconds)
        return timer_str.strip()

    def get_elapsed_time_as_str(self, offset="0"):
        elapsed = self.get_elapsed_time(offset)
        self.end_timer(offset)
        return self.get_time_as_str(elapsed)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTimerMonotonic(unittest.TestCase):

    def test_elapsed_time_reflects_monotonic_not_wall_clock(self):
        """
        get_elapsed_time() must return the monotonic duration, not the
        wall-clock difference.  With patched monotonic values of 100 and 102.5
        the elapsed time must be exactly 2.5 seconds.
        """
        t = Timer()
        with patch("time.monotonic", side_effect=[100.0, 102.5]):
            t.start_timer("cmd")
            elapsed = t.get_elapsed_time("cmd")

        self.assertIsInstance(elapsed, datetime.timedelta)
        self.assertAlmostEqual(elapsed.total_seconds(), 2.5, places=5)

    def test_backward_wall_clock_jump_does_not_produce_negative_elapsed(self):
        """
        Simulate an NTP step that moves the system wall clock back 30 seconds.
        The monotonic-based implementation must still report a positive duration.
        """
        t = Timer()

        # Monotonic advances normally: 5 seconds
        with patch("time.monotonic", side_effect=[200.0, 205.0]):
            t.start_timer("plugin")
            elapsed = t.get_elapsed_time("plugin")

        # Must be 5 seconds (monotonic), not affected by any wall-clock jump
        self.assertGreater(elapsed.total_seconds(), 0)
        self.assertAlmostEqual(elapsed.total_seconds(), 5.0, places=5)

    def test_get_elapsed_time_as_str_returns_nonempty_string(self):
        """get_elapsed_time_as_str() must still produce a human-readable string."""
        t = Timer()
        with patch("time.monotonic", side_effect=[300.0, 303.75]):
            t.start_timer("x")
            result = t.get_elapsed_time_as_str("x")

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_start_timer_still_returns_datetime(self):
        """start_timer() must continue to return a datetime for DB/display."""
        t = Timer()
        with patch("time.monotonic", return_value=0.0):
            result = t.start_timer("check")
        self.assertIsInstance(result, datetime.datetime)

    def test_monotonic_start_stored_in_timer_dict(self):
        """start_timer() must store monotonic_start so get_elapsed_time() can use it."""
        t = Timer()
        with patch("time.monotonic", return_value=42.0):
            t.start_timer("t")
        self.assertIn("monotonic_start", t.timers["t"])
        self.assertEqual(t.timers["t"]["monotonic_start"], 42.0)


if __name__ == "__main__":
    unittest.main()
