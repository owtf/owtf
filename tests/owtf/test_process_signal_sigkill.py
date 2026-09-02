"""Regression test for owtf.utils.process._signal_process().

The SIGTERM -> SIGKILL escalation guarded its SIGKILL loop with `if not alive:`,
so the loop only ran when the survivor list was empty -- i.e. it never ran, and
processes that ignored the first signal were never force-killed (leaked as
orphans). This is the same inverted-condition bug fixed in WorkerManager._signal_children
(that one is a separate function / separate PR); this covers the twin in
utils.process, which WorkerManager.exit() relies on to reap worker process trees.
"""

import signal
import unittest
from unittest.mock import MagicMock, patch

from owtf.utils import process


class TestSignalProcessSigkillEscalation(unittest.TestCase):
    def _run_with_survivors(self, survivors):
        """Invoke _signal_process with a mocked psutil where wait_procs reports
        `survivors` as still alive after the first signal. Returns the parent +
        child mocks so the caller can assert on kill()."""
        parent = MagicMock(name="parent")
        child = MagicMock(name="child")
        parent.children.return_value = [child]

        with patch.object(process, "psutil") as psutil_mock:
            psutil_mock.Process.return_value = parent
            psutil_mock.wait_procs.return_value = ([], survivors)
            process._signal_process(1234, signal.SIGTERM)
        return parent, child

    def test_survivor_receives_sigkill(self):
        survivor = MagicMock(name="survivor")
        self._run_with_survivors([survivor])
        survivor.kill.assert_called_once()

    def test_no_survivors_means_no_kill(self):
        parent, child = self._run_with_survivors([])
        child.kill.assert_not_called()
        parent.kill.assert_not_called()

    def test_first_signal_is_sent_to_parent_and_children(self):
        parent = MagicMock(name="parent")
        child = MagicMock(name="child")
        parent.children.return_value = [child]
        with patch.object(process, "psutil") as psutil_mock:
            psutil_mock.Process.return_value = parent
            psutil_mock.wait_procs.return_value = ([], [])
            process._signal_process(1234, signal.SIGTERM)
        child.send_signal.assert_called_once_with(signal.SIGTERM)
        parent.send_signal.assert_called_once_with(signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
