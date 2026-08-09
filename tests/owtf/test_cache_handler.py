"""Unit tests for owtf.proxy.cache_handler.CacheHandler.

CacheHandler sits at the centre of OWTF's transaction-recording pipeline: it
computes the per-request cache key, writes the JSON transaction file, and drops
the `<hash>.rd` sentinel that TransactionLogger polls to persist a transaction
to the database. Despite that, it had no test coverage.

This suite is pure unittest with no PostgreSQL, no running proxy, and no network
dependency (CacheHandler imports only stdlib, tornado.httputil and a stdlib-only
FileLock), so it runs anywhere the CLI unit tests do -- unlike the existing
tests/functional/proxy/ tests, which require a live proxy on :8008 and httpbin.

Two tests near the end are deliberately CHARACTERIZATION tests: they assert the
current (buggy) behaviour so the contract is pinned and the assertions flip the
moment the corresponding fix lands. They are labelled as such and must not be
read as endorsing the bug.
"""

import base64
import json
import os
import re
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

import tornado.httputil

from owtf.lib.filelock import FileLock
from owtf.proxy.cache_handler import CacheHandler, response_from_cache


def make_request(cookie=None, user_agent=None, body=b"", response_buffer="body"):
    """Build a minimal stand-in for the Tornado request object CacheHandler reads."""
    req = type("FakeRequest", (), {})()
    req.method = "GET"
    req.url = "http://target.example/path"
    req.version = "HTTP/1.1"
    req.body = body
    headers = tornado.httputil.HTTPHeaders()
    if cookie is not None:
        headers["Cookie"] = cookie
    if user_agent is not None:
        headers["User-Agent"] = user_agent
    req.headers = headers
    req.local_timestamp = datetime(2026, 7, 10, 12, 0, 0)
    req.response_buffer = response_buffer
    return req


def make_response(code=200, set_cookie=None):
    resp = type("FakeResponse", (), {})()
    resp.code = code
    resp.request_time = 0.123
    headers = tornado.httputil.HTTPHeaders()
    headers["Content-Type"] = "text/html"
    if set_cookie:
        headers.add("Set-Cookie", set_cookie)
    resp.headers = headers
    return resp


class CacheHandlerTestBase(unittest.TestCase):
    def setUp(self):
        self.cache_dir = tempfile.mkdtemp(prefix="owtf-cache-test-")
        # A blacklist regex for a "session" cookie, mirroring main.py's construction.
        self.cookie_regex = re.compile("session=([^;]+;?)")

    def tearDown(self):
        shutil.rmtree(self.cache_dir, ignore_errors=True)

    def _handler(self, request, blacklist=True):
        return CacheHandler(self.cache_dir, request, self.cookie_regex, blacklist)


class TestCalculateHash(CacheHandlerTestBase):
    def test_hash_is_deterministic(self):
        h1 = self._handler(make_request(user_agent="ua"))
        h2 = self._handler(make_request(user_agent="ua"))
        h1.calculate_hash()
        h2.calculate_hash()
        self.assertEqual(h1.request_hash, h2.request_hash)

    def test_file_path_is_under_cache_dir(self):
        h = self._handler(make_request())
        h.calculate_hash()
        self.assertEqual(os.path.dirname(h.file_path), self.cache_dir)
        self.assertTrue(os.path.basename(h.file_path))

    def test_blacklisted_cookie_value_does_not_affect_hash(self):
        # Two requests differing only in the blacklisted "session" cookie value
        # must hash identically -- that is the point of the blacklist filter.
        h_a = self._handler(make_request(cookie="session=AAAA"))
        h_b = self._handler(make_request(cookie="session=BBBB"))
        h_a.calculate_hash()
        h_b.calculate_hash()
        self.assertEqual(h_a.request_hash, h_b.request_hash)

    def test_non_blacklisted_difference_changes_hash(self):
        h_a = self._handler(make_request(user_agent="agent-one"))
        h_b = self._handler(make_request(user_agent="agent-two"))
        h_a.calculate_hash()
        h_b.calculate_hash()
        self.assertNotEqual(h_a.request_hash, h_b.request_hash)


class TestDumpLoadRoundTrip(CacheHandlerTestBase):
    def _dump(self, handler, response):
        # dump() releases self.file_lock at the end, so acquire one first, the
        # same way load() would have before a cache-miss dump.
        handler.calculate_hash()
        handler.file_lock = FileLock(handler.file_path)
        handler.file_lock.acquire()
        handler.dump(response)

    def test_text_response_round_trips(self):
        req = make_request(response_buffer="<html>hello</html>")
        handler = self._handler(req)
        self._dump(handler, make_response(code=200, set_cookie="sid=xyz; Path=/"))

        restored = response_from_cache(handler.file_path)
        self.assertEqual(restored.code, 200)
        self.assertEqual(restored.body, "<html>hello</html>")
        self.assertIn("sid=xyz; Path=/", restored.cookies)

    def test_rd_sentinel_is_written(self):
        # The TransactionLogger contract: dump() must leave a <hash>.rd file that
        # the logger polls to persist the transaction.
        handler = self._handler(make_request())
        self._dump(handler, make_response())
        self.assertTrue(os.path.isfile("{}.rd".format(handler.file_path)))

    def test_dumped_json_is_wellformed_and_complete(self):
        handler = self._handler(make_request())
        self._dump(handler, make_response(code=404))
        with open(handler.file_path) as fh:
            data = json.load(fh)
        for key in (
            "request_method", "request_url", "response_code",
            "response_headers", "response_body", "binary_response",
        ):
            self.assertIn(key, data)
        self.assertEqual(data["response_code"], 404)


class TestBinaryResponseCharacterization(CacheHandlerTestBase):
    """CHARACTERIZATION (documents a bug, does not endorse it).

    dump() guards binary detection with `try: response_body = self.request
    .response_buffer / except UnicodeDecodeError`. But response_buffer is a plain
    str attribute, so reading it can never raise UnicodeDecodeError -- the except
    branch is dead and `binary_response` is always False. Binary bodies therefore
    get stored as (already-corrupted) text and never base64-encoded.

    When the proposal's bytes-buffer / content-type-based binary fix lands, the
    assertion below should flip to expect binary_response=True + a base64 body.
    """

    def test_binary_detection_is_currently_dead(self):
        req = make_request(response_buffer="��PNG-ish-bytes")
        handler = self._handler(req)
        handler.calculate_hash()
        handler.file_lock = FileLock(handler.file_path)
        handler.file_lock.acquire()
        handler.dump(make_response())

        with open(handler.file_path) as fh:
            data = json.load(fh)
        self.assertIs(data["binary_response"], False)  # bug: should be able to be True
        # Body was stored as text, not base64 -- proving no binary handling ran.
        self.assertEqual(data["response_body"], "��PNG-ish-bytes")
        with self.assertRaises((ValueError, Exception)):
            # It is not valid base64 of the original bytes -- i.e. it was NOT encoded.
            base64.b64decode(data["response_body"], validate=True)


class TestLockTimeoutCharacterization(CacheHandlerTestBase):
    """CHARACTERIZATION (documents a bug, does not endorse it).

    On a cache miss, load() acquires a FileLock and catches
    `FileLockTimeoutException` on timeout -- but that name is undefined anywhere
    in the codebase (FileLock.acquire() actually raises FileLock.FileLockException).
    So a lock timeout raises NameError instead of being handled.

    When the exception-handling fix lands, this should flip to assert load()
    returns None gracefully.
    """

    def test_lock_timeout_currently_raises_nameerror(self):
        handler = self._handler(make_request())
        handler.calculate_hash()  # so file_path is set; file does not exist -> cache miss
        with patch.object(FileLock, "acquire", side_effect=FileLock.FileLockException("timeout")):
            with self.assertRaises(NameError):
                handler.load()


if __name__ == "__main__":
    unittest.main()
