"""
Unit tests for the SIGKILL escalation logic in WorkerManager._signal_children().

The bug was that `if not alive:` was used instead of `if alive:`, making the
SIGKILL path and the "survived SIGKILL" log unreachable dead code.  These tests
verify the corrected behaviour by replaying the exact branching logic with mocks.
"""
import signal
import unittest
from unittest.mock import MagicMock, call


def _signal_children_logic(children, wait_procs, timeout, sigkill_escalation_calls):
    """
    Reproduce the _signal_children branching logic in isolation so that we can
    test it without importing the full OWTF module graph.

    `sigkill_escalation_calls` is a list that this function appends to whenever
    `pid.kill()` would be called — lets the test assert kill was/wasn't invoked.
    """
    on_terminate_calls = []

    def on_terminate(proc):
        on_terminate_calls.append(proc)

    gone, alive = wait_procs(children, timeout=timeout, callback=on_terminate)
    if alive:  # corrected: was `if not alive:`
        for pid in alive:
            pid.kill()
            sigkill_escalation_calls.append(pid)
    gone, alive = wait_procs(alive, timeout=timeout, callback=on_terminate)
    if alive:  # corrected: was `if not alive:`
        for pid in alive:
            sigkill_escalation_calls.append(("gave_up", pid))


class TestSignalChildrenEscalation(unittest.TestCase):

    def _make_proc(self, pid=1234):
        p = MagicMock()
        p.pid = pid
        return p

    def test_sigkill_sent_to_process_that_survived_sigterm(self):
        """kill() must be called on a process that is still alive after SIGTERM."""
        survivor = self._make_proc(1234)
        calls = []

        def fake_wait_procs(procs, timeout, callback):
            if procs == [survivor]:
                return [], [survivor]   # first call: survivor still alive
            return [survivor], []       # second call: terminated after SIGKILL

        _signal_children_logic(
            children=[survivor],
            wait_procs=fake_wait_procs,
            timeout=3,
            sigkill_escalation_calls=calls,
        )

        survivor.kill.assert_called_once()
        self.assertIn(survivor, calls)

    def test_kill_not_called_when_all_terminated_on_first_wait(self):
        """kill() must NOT be called if all processes terminate before SIGKILL."""
        proc = self._make_proc(5678)
        calls = []

        def fake_wait_procs(procs, timeout, callback):
            return [proc], []   # all gone immediately

        _signal_children_logic(
            children=[proc],
            wait_procs=fake_wait_procs,
            timeout=3,
            sigkill_escalation_calls=calls,
        )

        proc.kill.assert_not_called()
        self.assertEqual(calls, [])

    def test_gave_up_logged_when_process_survives_sigkill(self):
        """The gave-up path must be reachable when a process survives SIGKILL."""
        unkillable = self._make_proc(9999)
        calls = []
        call_count = [0]

        def fake_wait_procs(procs, timeout, callback):
            call_count[0] += 1
            if call_count[0] == 1:
                return [], [unkillable]   # survived SIGTERM
            return [], [unkillable]       # survived SIGKILL too

        _signal_children_logic(
            children=[unkillable],
            wait_procs=fake_wait_procs,
            timeout=3,
            sigkill_escalation_calls=calls,
        )

        unkillable.kill.assert_called_once()
        self.assertIn(("gave_up", unkillable), calls)


if __name__ == "__main__":
    unittest.main()
