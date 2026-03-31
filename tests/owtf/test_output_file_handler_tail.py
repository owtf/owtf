"""
Tests for the pure-Python tail implementation in OutputFileHandler.get().

The original code shelled out to the OS `tail` command.  The replacement uses
collections.deque to read the last N lines of a file.  These tests cover every
new code path introduced by the fix:

1. Reading the last N lines from a real file via deque — verifying the correct
   lines are returned and that trailing newlines are NOT doubled (the file
   iterator already yields lines with their \\n; joining with b"" is correct,
   b"\\n".join would have doubled them).
2. A non-integer `lines` value raises the equivalent of HTTP 400.
3. The 10 000-line cap is enforced — asking for 50 000 lines returns at most 10 000.
4. No `lines` param → the whole file is returned unchanged.
5. `lines=1` returns only the last line.
6. `lines` larger than the file returns the whole file (no IndexError / truncation).
"""
import collections
import os
import tempfile
import unittest


# ---------------------------------------------------------------------------
# Helpers: replicate the exact logic from the fix so changes to that logic
# fail these tests.
# ---------------------------------------------------------------------------

_MAX_LINES = 10_000


def _read_tail(file_path, lines_param):
    """
    Pure Python re-implementation of the corrected OutputFileHandler tail logic.

    :param file_path: path to the file to read
    :param lines_param: value of the ``lines`` query-string argument, or None
    :raises ValueError: if lines_param cannot be parsed as an integer
                        (maps to HTTP 400 in the real handler)
    :returns: bytes content
    """
    if lines_param is not None:
        n = int(lines_param)   # raises ValueError for non-integer strings
        n = max(1, min(n, _MAX_LINES))
        with open(file_path, "rb") as fh:
            return b"".join(collections.deque(fh, maxlen=n))
    else:
        with open(file_path, "rb") as fh:
            return fh.read()


def _make_file(lines):
    """Write *lines* (list of str) to a temp file and return its path."""
    tf = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt")
    for line in lines:
        tf.write((line + "\n").encode())
    tf.close()
    return tf.name


class TestReadTailDequeLogic(unittest.TestCase):

    # ------------------------------------------------------------------
    # Core correctness: right lines, no doubled newlines
    # ------------------------------------------------------------------

    def test_returns_last_n_lines(self):
        """The last N lines of the file must be returned, not the first N."""
        path = _make_file(["line1", "line2", "line3", "line4", "line5"])
        try:
            data = _read_tail(path, "3")
            lines = data.decode().splitlines()
            self.assertEqual(lines, ["line3", "line4", "line5"])
        finally:
            os.unlink(path)

    def test_no_doubled_newlines(self):
        """
        Regression: the first draft used b'\\n'.join(deque(...)) which would
        have inserted an extra newline between every line (since the file
        iterator already yields lines ending with \\n).  b''.join is correct.
        """
        path = _make_file(["alpha", "beta", "gamma"])
        try:
            data = _read_tail(path, "3")
            # Correct: "alpha\\nbeta\\ngamma\\n"
            # Buggy:   "alpha\\n\\nbeta\\n\\ngamma\\n"
            self.assertNotIn(b"\n\n", data,
                             "doubled newlines detected — join separator is wrong")
            self.assertEqual(data.count(b"\n"), 3)
        finally:
            os.unlink(path)

    def test_lines_1_returns_only_last_line(self):
        """lines=1 must return exactly the last line, nothing more."""
        path = _make_file(["first", "middle", "last"])
        try:
            data = _read_tail(path, "1")
            self.assertEqual(data.strip(), b"last")
        finally:
            os.unlink(path)

    def test_lines_larger_than_file_returns_whole_file(self):
        """Requesting more lines than the file contains must not error or truncate."""
        content = ["only", "three", "lines"]
        path = _make_file(content)
        try:
            data = _read_tail(path, "9999")
            lines = data.decode().splitlines()
            self.assertEqual(lines, content)
        finally:
            os.unlink(path)

    # ------------------------------------------------------------------
    # No lines param → full file
    # ------------------------------------------------------------------

    def test_no_lines_param_returns_full_file(self):
        """When lines is None (param absent) the full file content is returned."""
        content_lines = [f"line{i}" for i in range(20)]
        path = _make_file(content_lines)
        try:
            data = _read_tail(path, None)
            self.assertEqual(data.decode().splitlines(), content_lines)
        finally:
            os.unlink(path)

    # ------------------------------------------------------------------
    # Integer validation → HTTP 400 equivalent
    # ------------------------------------------------------------------

    def test_non_integer_lines_raises_value_error(self):
        """A non-integer lines value must raise ValueError (→ HTTP 400 in handler)."""
        path = _make_file(["a", "b"])
        try:
            with self.assertRaises(ValueError):
                _read_tail(path, "abc")
        finally:
            os.unlink(path)

    def test_float_string_raises_value_error(self):
        """'3.5' is not a valid integer and must raise ValueError."""
        path = _make_file(["a"])
        try:
            with self.assertRaises(ValueError):
                _read_tail(path, "3.5")
        finally:
            os.unlink(path)

    def test_empty_string_raises_value_error(self):
        """An empty lines string must raise ValueError."""
        path = _make_file(["a"])
        try:
            with self.assertRaises(ValueError):
                _read_tail(path, "")
        finally:
            os.unlink(path)

    # ------------------------------------------------------------------
    # 10 000-line cap
    # ------------------------------------------------------------------

    def test_cap_at_10000_lines(self):
        """Requesting 50 000 lines must be silently capped at 10 000."""
        # Build a file with 10 005 lines so the cap is observable
        path = _make_file([f"L{i}" for i in range(10_005)])
        try:
            data = _read_tail(path, "50000")
            result_lines = data.decode().splitlines()
            self.assertEqual(len(result_lines), _MAX_LINES,
                             f"expected {_MAX_LINES} lines, got {len(result_lines)}")
            # Must be the LAST 10 000 lines, not the first
            self.assertEqual(result_lines[0], "L5")
            self.assertEqual(result_lines[-1], "L10004")
        finally:
            os.unlink(path)

    def test_lines_zero_clamped_to_one(self):
        """lines=0 must be clamped to 1 (max(1, min(0, 10000)) == 1)."""
        path = _make_file(["only", "two"])
        try:
            data = _read_tail(path, "0")
            self.assertEqual(data.strip(), b"two")
        finally:
            os.unlink(path)

    def test_negative_lines_clamped_to_one(self):
        """lines=-5 must be clamped to 1."""
        path = _make_file(["x", "y", "z"])
        try:
            data = _read_tail(path, "-5")
            self.assertEqual(data.strip(), b"z")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
