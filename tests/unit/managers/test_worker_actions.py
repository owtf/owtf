"""Worker broadcasts run once per worker and never target pseudo-index zero."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest


def worker_modules():
    # The manager starts workers and opens a DB session at import time.
    with (
        patch("owtf.db.session.get_scoped_session", return_value=Mock()),
        patch("owtf.workers.local.LocalWorker.start"),
    ):
        from owtf.api.handlers.work import WorkerHandler
        from owtf.managers import worker

    return WorkerHandler, worker


@pytest.mark.parametrize("action", ["pause", "resume", "abort"])
def test_broadcast_action_does_not_target_worker_zero(action):
    WorkerHandler, worker = worker_modules()
    manager = Mock()
    handler = SimpleNamespace()

    with patch("owtf.api.handlers.work.worker_manager", manager):
        WorkerHandler.get(handler, "0", action)

    getattr(manager, f"{action}_all_workers").assert_called_once_with()
    getattr(manager, f"{action}_worker").assert_not_called()


@pytest.mark.parametrize("action", ["pause", "resume", "abort"])
def test_single_worker_action_uses_one_based_id(action):
    WorkerHandler, _ = worker_modules()
    manager = Mock()

    with patch("owtf.api.handlers.work.worker_manager", manager):
        WorkerHandler.get(SimpleNamespace(), "2", action)

    getattr(manager, f"{action}_worker").assert_called_once_with(2)
    getattr(manager, f"{action}_all_workers").assert_not_called()


def test_abort_all_workers_signals_each_worker_once():
    _, worker = worker_modules()
    manager = worker.WorkerManager.__new__(worker.WorkerManager)
    manager.workers = [
        {"worker": SimpleNamespace(pid=101)},
        {"worker": SimpleNamespace(pid=202)},
    ]
    original_workers = list(manager.workers)

    with patch.object(worker, "_signal_process") as signal_process:
        manager.abort_all_workers()

    assert signal_process.call_count == 2
    assert [call.args[0] for call in signal_process.call_args_list] == [101, 202]
    assert manager.workers == original_workers
