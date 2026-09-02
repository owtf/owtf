import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from owtf.lib.filelock import FileLock
from owtf.proxy.cache_handler import CacheHandler


class TestCacheHandlerFileLockException(unittest.TestCase):
    """CacheHandler.load() must handle a lock-acquisition timeout without
    raising NameError. FileLock.acquire() raises the nested
    FileLock.FileLockException on timeout, not a top-level
    FileLockTimeoutException (which does not exist anywhere in the codebase).
    """

    def setUp(self):
        self.cache_dir = tempfile.mkdtemp()
        fake_request = type("FakeRequest", (), {})()
        self.handler = CacheHandler(self.cache_dir, fake_request, cookie_regex=None, blacklist=False)
        self.handler.file_path = os.path.join(self.cache_dir, "deadbeef")

    def tearDown(self):
        shutil.rmtree(self.cache_dir, ignore_errors=True)

    def test_load_handles_filelock_exception_without_nameerror(self):
        with patch.object(FileLock, "acquire", side_effect=FileLock.FileLockException("timeout")):
            result = self.handler.load()
        self.assertIsNone(result)

    def test_timeout_handler_cannot_write_or_release_another_handlers_lock(self):
        owner = FileLock(self.handler.file_path)
        owner.acquire()
        try:
            def finish_partial_write_then_time_out(_lock):
                open(self.handler.file_path, "w").close()
                raise FileLock.FileLockException("timeout")

            with patch.object(FileLock, "acquire", autospec=True, side_effect=finish_partial_write_then_time_out):
                self.assertIsNone(self.handler.load())

            self.handler.dump(object())

            self.assertEqual(os.path.getsize(self.handler.file_path), 0)
            self.assertTrue(os.path.exists(owner.lockfile))
            self.assertTrue(owner.locked())
        finally:
            owner.release()

    def test_filelock_raises_filelock_exception_not_a_top_level_name(self):
        lock = FileLock(os.path.join(self.cache_dir, "locked_file"), timeout=0.05, delay=0.01)
        # Simulate another process already holding the lock.
        open(lock.lockfile, "w").close()
        with self.assertRaises(FileLock.FileLockException):
            lock.acquire()


if __name__ == "__main__":
    unittest.main()
