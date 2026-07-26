"""
tests/test_community_plugin_bounds.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cover the min and max bounds that the upload handler applies to the
uploader-supplied execution_timeout and memory_limit values.

The bounds live in owtf.settings and the parsing helper lives in
owtf.api.handlers.community_plugin._parse_bounded_int. Testing the
helper directly is enough to prove that:

* an empty field falls back to the default,
* a garbage string returns 400,
* a value below the min returns 400,
* a value above the max returns 400,
* the min and max values themselves are accepted (inclusive bounds),
* a value in the middle of the range comes through unchanged.

Run with:
    python -m pytest tests/test_community_plugin_bounds.py -v
"""

import pytest

from owtf.api.handlers.community_plugin import _parse_bounded_int
from owtf.lib.exceptions import APIError
from owtf.settings import (
    COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    COMMUNITY_PLUGIN_MAX_MEMORY,
    COMMUNITY_PLUGIN_MAX_TIMEOUT,
    COMMUNITY_PLUGIN_MEMORY_LIMIT,
    COMMUNITY_PLUGIN_MIN_MEMORY,
    COMMUNITY_PLUGIN_MIN_TIMEOUT,
)


class TestExecutionTimeoutBounds:
    """execution_timeout must be an int inside the configured seconds range."""

    def _parse(self, raw):
        return _parse_bounded_int(
            "execution_timeout",
            raw,
            COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
            COMMUNITY_PLUGIN_MIN_TIMEOUT,
            COMMUNITY_PLUGIN_MAX_TIMEOUT,
            "seconds",
        )

    def test_empty_uses_default(self):
        assert self._parse("") == COMMUNITY_PLUGIN_DEFAULT_TIMEOUT

    def test_min_value_accepted(self):
        assert self._parse(str(COMMUNITY_PLUGIN_MIN_TIMEOUT)) == COMMUNITY_PLUGIN_MIN_TIMEOUT

    def test_max_value_accepted(self):
        assert self._parse(str(COMMUNITY_PLUGIN_MAX_TIMEOUT)) == COMMUNITY_PLUGIN_MAX_TIMEOUT

    def test_mid_range_value_passes_through(self):
        mid = (COMMUNITY_PLUGIN_MIN_TIMEOUT + COMMUNITY_PLUGIN_MAX_TIMEOUT) // 2
        assert self._parse(str(mid)) == mid

    def test_below_min_rejected(self):
        with pytest.raises(APIError) as exc:
            self._parse(str(COMMUNITY_PLUGIN_MIN_TIMEOUT - 1))
        assert exc.value.status_code == 400
        assert "execution_timeout" in str(exc.value)

    def test_above_max_rejected(self):
        with pytest.raises(APIError) as exc:
            self._parse(str(COMMUNITY_PLUGIN_MAX_TIMEOUT + 1))
        assert exc.value.status_code == 400
        assert "execution_timeout" in str(exc.value)

    def test_non_integer_rejected(self):
        with pytest.raises(APIError) as exc:
            self._parse("not-a-number")
        assert exc.value.status_code == 400
        assert "integer" in str(exc.value)

    def test_negative_rejected(self):
        with pytest.raises(APIError) as exc:
            self._parse("-30")
        assert exc.value.status_code == 400


class TestMemoryLimitBounds:
    """memory_limit must be an int inside the configured bytes range."""

    def _parse(self, raw):
        return _parse_bounded_int(
            "memory_limit",
            raw,
            COMMUNITY_PLUGIN_MEMORY_LIMIT,
            COMMUNITY_PLUGIN_MIN_MEMORY,
            COMMUNITY_PLUGIN_MAX_MEMORY,
            "bytes",
        )

    def test_empty_uses_default(self):
        assert self._parse("") == COMMUNITY_PLUGIN_MEMORY_LIMIT

    def test_min_value_accepted(self):
        assert self._parse(str(COMMUNITY_PLUGIN_MIN_MEMORY)) == COMMUNITY_PLUGIN_MIN_MEMORY

    def test_max_value_accepted(self):
        assert self._parse(str(COMMUNITY_PLUGIN_MAX_MEMORY)) == COMMUNITY_PLUGIN_MAX_MEMORY

    def test_mid_range_value_passes_through(self):
        mid = (COMMUNITY_PLUGIN_MIN_MEMORY + COMMUNITY_PLUGIN_MAX_MEMORY) // 2
        assert self._parse(str(mid)) == mid

    def test_below_min_rejected(self):
        with pytest.raises(APIError) as exc:
            self._parse(str(COMMUNITY_PLUGIN_MIN_MEMORY - 1))
        assert exc.value.status_code == 400
        assert "memory_limit" in str(exc.value)

    def test_above_max_rejected(self):
        with pytest.raises(APIError) as exc:
            self._parse(str(COMMUNITY_PLUGIN_MAX_MEMORY + 1))
        assert exc.value.status_code == 400
        assert "memory_limit" in str(exc.value)

    def test_non_integer_rejected(self):
        with pytest.raises(APIError) as exc:
            self._parse("128mb")
        assert exc.value.status_code == 400
        assert "integer" in str(exc.value)


class TestBoundsMessageContent:
    """The 400 message should tell the uploader the exact accepted range."""

    def test_range_appears_in_message(self):
        with pytest.raises(APIError) as exc:
            _parse_bounded_int("execution_timeout", "5", 300, 10, 900, "seconds")
        msg = str(exc.value)
        assert "10" in msg
        assert "900" in msg
        assert "seconds" in msg
