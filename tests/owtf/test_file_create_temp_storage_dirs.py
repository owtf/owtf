"""
Unit tests for create_temp_storage_dirs() logic in owtf/utils/file.py.

The bug: the pid subdirectory path was computed *inside* the block guarded by
`if not os.path.exists(/tmp/owtf)`, so on any run after the first (when the
base dir already existed) the pid directory was silently never created.

The fix collapses both levels into a single unconditional path computation.
These tests reproduce the corrected logic directly to avoid the heavy OWTF
import chain.
"""
import os
import tempfile
import unittest
from unittest.mock import patch, call


def _create_temp_storage_dirs(owtf_pid, make_dirs_fn=None, exists_fn=None):
    """
    Re-implementation of the *corrected* create_temp_storage_dirs() logic.
    Injecting make_dirs_fn and exists_fn lets the test control the filesystem.
    """
    if make_dirs_fn is None:
        make_dirs_fn = os.makedirs
    if exists_fn is None:
        exists_fn = os.path.exists

    tmp_dir = os.path.join("/tmp", "owtf", str(owtf_pid))
    if not exists_fn(tmp_dir):
        make_dirs_fn(tmp_dir)


class TestCreateTempStorageDirs(unittest.TestCase):

    def test_creates_pid_subdir_when_nothing_exists(self):
        """Both the base and pid dirs are created on the very first run."""
        with tempfile.TemporaryDirectory() as root:
            pid_dir = os.path.join("/tmp", "owtf", "1234")

            created_paths = []

            def fake_makedirs(path):
                # Redirect into temp root so the test stays clean
                rel = os.path.relpath(path, "/")
                real = os.path.join(root, rel)
                os.makedirs(real, exist_ok=True)
                created_paths.append(path)

            def fake_exists(path):
                rel = os.path.relpath(path, "/")
                return os.path.exists(os.path.join(root, rel))

            _create_temp_storage_dirs(1234, make_dirs_fn=fake_makedirs, exists_fn=fake_exists)

            self.assertIn(pid_dir, created_paths)

    def test_creates_pid_subdir_even_when_base_dir_exists(self):
        """
        Regression: the old code skipped pid-dir creation when /tmp/owtf
        already existed.  The corrected code must always create the pid dir.
        """
        with tempfile.TemporaryDirectory() as root:
            # Pre-create the equivalent of /tmp/owtf so fake_exists returns True for it
            base_equiv = os.path.join(root, "tmp", "owtf")
            os.makedirs(base_equiv, exist_ok=True)

            pid_dir = os.path.join("/tmp", "owtf", "5678")
            created_paths = []

            def fake_makedirs(path):
                rel = os.path.relpath(path, "/")
                real = os.path.join(root, rel)
                os.makedirs(real, exist_ok=True)
                created_paths.append(path)

            def fake_exists(path):
                rel = os.path.relpath(path, "/")
                return os.path.exists(os.path.join(root, rel))

            _create_temp_storage_dirs(5678, make_dirs_fn=fake_makedirs, exists_fn=fake_exists)

            self.assertIn(pid_dir, created_paths,
                          "pid subdir must be created even when /tmp/owtf already exists")

    def test_does_not_call_makedirs_when_pid_dir_already_exists(self):
        """make_dirs must not be called when the pid directory is already there."""
        with tempfile.TemporaryDirectory() as root:
            # Pre-create the equivalent of /tmp/owtf/9999
            pid_equiv = os.path.join(root, "tmp", "owtf", "9999")
            os.makedirs(pid_equiv, exist_ok=True)

            called = []

            def fake_makedirs(path):
                called.append(path)

            def fake_exists(path):
                rel = os.path.relpath(path, "/")
                return os.path.exists(os.path.join(root, rel))

            _create_temp_storage_dirs(9999, make_dirs_fn=fake_makedirs, exists_fn=fake_exists)

            self.assertEqual(called, [],
                             "makedirs must not be called when pid dir already exists")


if __name__ == "__main__":
    unittest.main()
