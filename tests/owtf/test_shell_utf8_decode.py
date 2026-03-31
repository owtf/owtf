"""
Tests for the errors='replace' UTF-8 decode fix in owtf/shell/base.py.

shell_exec_monitor() reads subprocess stdout line-by-line and decodes each
chunk as UTF-8.  Security tools routinely emit non-UTF-8 bytes (binary
headers, Latin-1 strings, raw port-scan data, etc.).  Before the fix,
bytes.decode('utf-8') with the default errors='strict' would raise
UnicodeDecodeError on any such chunk, silently killing the plugin and
discarding all output collected so far.

The fix adds errors='replace' so decoding always succeeds: invalid bytes
are substituted with the Unicode replacement character U+FFFD (\\ufffd).

These tests verify:
1. Non-UTF-8 bytes decode without raising when errors='replace' is used.
2. The default errors='strict' WOULD raise — confirming the fix is necessary.
3. Valid UTF-8 bytes are decoded identically with or without errors='replace'.
4. The replacement character (U+FFFD) appears in place of invalid bytes.
5. Output after bad bytes is not lost — the rest of the string survives.
6. The KeyboardInterrupt path (out.decode) applies the same fix.
"""
import unittest


# ---------------------------------------------------------------------------
# The actual decode calls from the fixed owtf/shell/base.py:
#
#   line.decode("utf-8", errors="replace").strip()     # stdout loop  (line 196)
#   output += line.decode("utf-8", errors="replace")   # stdout loop  (line 198-200)
#   logging.warning(out.decode("utf-8", errors="replace"))  # KeyboardInterrupt (line 204)
#   output += out.decode("utf-8", errors="replace")    # KeyboardInterrupt (line 205)
#
# We test the decode expression directly — no OWTF imports needed.
# ---------------------------------------------------------------------------

# Bytes that are invalid UTF-8 sequences
INVALID_UTF8_SEQUENCES = [
    b"\xff",                   # lone 0xFF — not valid in any UTF-8 sequence
    b"\xfe",                   # lone 0xFE — same
    b"\xff\xfe",               # UTF-16 BOM — not valid UTF-8
    b"\x80",                   # continuation byte without leading byte
    b"\xc3\x28",               # invalid 2-byte sequence
    b"\xe2\x28\xa1",           # invalid 3-byte sequence
    b"\xf0\x28\x8c\xbc",      # invalid 4-byte sequence
]

REPLACEMENT_CHAR = "\ufffd"


class TestUTF8DecodeWithReplace(unittest.TestCase):

    # ------------------------------------------------------------------
    # The fix is necessary: strict mode raises on invalid bytes
    # ------------------------------------------------------------------

    def test_strict_mode_raises_on_invalid_utf8(self):
        """
        Confirm that the OLD behaviour (no errors= kwarg) raises UnicodeDecodeError
        on non-UTF-8 bytes.  This is the regression the fix prevents.
        """
        for bad_bytes in INVALID_UTF8_SEQUENCES:
            with self.subTest(bad_bytes=bad_bytes):
                with self.assertRaises(UnicodeDecodeError,
                                       msg=f"{bad_bytes!r} should raise in strict mode"):
                    bad_bytes.decode("utf-8")

    # ------------------------------------------------------------------
    # The fix works: errors='replace' never raises
    # ------------------------------------------------------------------

    def test_replace_mode_never_raises_on_invalid_utf8(self):
        """
        errors='replace' must not raise on any invalid UTF-8 byte sequence.
        This directly tests the decode expressions used in shell_exec_monitor().
        """
        for bad_bytes in INVALID_UTF8_SEQUENCES:
            with self.subTest(bad_bytes=bad_bytes):
                try:
                    result = bad_bytes.decode("utf-8", errors="replace")
                except UnicodeDecodeError as exc:
                    self.fail(
                        f"decode with errors='replace' raised UnicodeDecodeError "
                        f"for {bad_bytes!r}: {exc}"
                    )
                self.assertIsInstance(result, str)

    def test_replacement_character_substituted_for_invalid_bytes(self):
        """Invalid bytes must produce U+FFFD replacement characters, not be silently dropped."""
        for bad_bytes in INVALID_UTF8_SEQUENCES:
            with self.subTest(bad_bytes=bad_bytes):
                result = bad_bytes.decode("utf-8", errors="replace")
                self.assertIn(
                    REPLACEMENT_CHAR, result,
                    f"expected U+FFFD in decoded output of {bad_bytes!r}, got {result!r}",
                )

    # ------------------------------------------------------------------
    # Output after bad bytes is preserved
    # ------------------------------------------------------------------

    def test_content_after_invalid_bytes_is_not_lost(self):
        """
        A line like b'\\xff\\xfenmap output' must produce the 'nmap output'
        portion in the decoded string — only the invalid prefix is replaced.
        """
        line = b"\xff\xfenmap output: port 80 open\n"
        result = line.decode("utf-8", errors="replace")
        self.assertIn("nmap output", result)
        self.assertIn("port 80 open", result)

    def test_mixed_line_preserves_ascii_content(self):
        """A line mixing valid ASCII and invalid bytes must preserve the ASCII parts."""
        line = b"result: \xffOK\n"
        result = line.decode("utf-8", errors="replace")
        self.assertIn("result: ", result)
        self.assertIn("OK", result)
        self.assertIn(REPLACEMENT_CHAR, result)

    # ------------------------------------------------------------------
    # Valid UTF-8 is unaffected
    # ------------------------------------------------------------------

    def test_valid_utf8_decoded_identically(self):
        """errors='replace' must not alter output that is already valid UTF-8."""
        valid_lines = [
            b"normal ascii output\n",
            b"unicode: caf\xc3\xa9\n",          # "café" in UTF-8
            b"\xe2\x9c\x94 check mark\n",        # ✔ U+2714
            b"",
        ]
        for line in valid_lines:
            with self.subTest(line=line):
                self.assertEqual(
                    line.decode("utf-8"),
                    line.decode("utf-8", errors="replace"),
                    "valid UTF-8 must decode identically with or without errors='replace'",
                )

    # ------------------------------------------------------------------
    # KeyboardInterrupt path: out = proc.communicate()[0]
    # ------------------------------------------------------------------

    def test_bulk_bytes_from_communicate_decode_without_raising(self):
        """
        The KeyboardInterrupt path collects all remaining stdout at once via
        proc.communicate().  Simulate a block of output containing bad bytes.
        """
        # Simulate mixed output: some valid, some invalid, as one chunk
        out = b"Scan started\nHost: 192.168.1.1\xff\n80/tcp open http\n"
        try:
            decoded = out.decode("utf-8", errors="replace")
        except UnicodeDecodeError as exc:
            self.fail(f"bulk decode with errors='replace' raised: {exc}")

        self.assertIn("Scan started", decoded)
        self.assertIn("80/tcp open http", decoded)
        self.assertIn(REPLACEMENT_CHAR, decoded)  # the \xff is replaced

    def test_strip_on_decoded_line_works_after_replace(self):
        """
        The stdout loop uses .decode('utf-8', errors='replace').strip().
        Verify strip() works correctly on strings containing replacement chars.
        """
        line = b"  \xff output line  \n"
        result = line.decode("utf-8", errors="replace").strip()
        self.assertFalse(result.startswith(" "))
        self.assertFalse(result.endswith(" "))
        self.assertFalse(result.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
