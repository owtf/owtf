def test_manage_workers_two_cycles_no_stranded_work_and_drain_removal():
    """Manager-level regression test for the reported lifecycle bug:
    get_work_batch() must claim only work that assignable-this-cycle
    workers can take, completed/dead work must be deleted or requeued
    (never silently stranded), and a drained worker must be removed and
    joined rather than lingering in self.workers as phantom idle capacity.
    """
    import queue as queue_module
    from unittest import mock

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from owtf.db.model_base import Model
    from owtf.models.plugin import Plugin
    from owtf.models.session import Session  # noqa: F401 - registers target_association_table's FK target
    from owtf.models.target import Target
    from owtf.models.test_group import TestGroup
    from owtf.models.work import Work

    with (
        mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()),
        mock.patch("owtf.workers.local.LocalWorker.start"),
    ):
        from owtf.managers.worker import WorkerManager

    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()

    class FakeQueue:
        def __init__(self):
            self._items = []

        def empty(self):
            return len(self._items) == 0

        def get_nowait(self):
            if not self._items:
                raise queue_module.Empty()
            return self._items.pop(0)

        def put(self, item):
            self._items.append(item)

    class FakeWorkerProcess:
        def __init__(self, pid, name):
            self.pid = pid
            self.name = name
            self.output_q = FakeQueue()
            self.input_q = FakeQueue()
            self.poison_q = FakeQueue()
            self._alive = True

        def is_alive(self):
            return self._alive

        def join(self, timeout=None):
            self._alive = False

        def terminate(self):
            self._alive = False

    try:
        # --- Seed: one plugin and three targets (Work has a unique
        # constraint on target_id+plugin_key). ---
        tg = TestGroup(code="OWTF-TEST-001", group="web", descrip="d", url="http://x", priority=1)
        plugin = Plugin(
            key="active@OWTF-TEST-001",
            title="t",
            name="n",
            code="OWTF-TEST-001",
            group="web",
            type="active",
            file="f.py",
        )
        target1 = Target(target_url="http://example1.com")
        target2 = Target(target_url="http://example2.com")
        target3 = Target(target_url="http://example3.com")
        session.add_all([tg, plugin, target1, target2, target3])
        session.commit()

        work1 = Work(target_id=target1.id, plugin_key=plugin.key, active=True)
        work2 = Work(target_id=target2.id, plugin_key=plugin.key, active=True)
        work3 = Work(target_id=target3.id, plugin_key=plugin.key, active=True)
        session.add_all([work1, work2, work3])
        session.commit()
        work1_id, work2_id, work3_id = work1.id, work2.id, work3.id

        # --- 4 idle fake workers, no real OS processes involved ---
        manager = WorkerManager.__new__(WorkerManager)
        manager.session = session
        manager.keep_working = True
        manager.workers = [
            {
                "worker": FakeWorkerProcess(pid=1001 + i, name=f"worker-{i}"),
                "work": (),
                "work_id": None,
                "busy": False,
                "paused": False,
            }
            for i in range(4)
        ]

        with (
            mock.patch("owtf.managers.worker.WORKER_LOW_WATER", 4),
            mock.patch("owtf.managers.worker.check_pid", return_value=True),
            mock.patch("owtf.managers.worker._signal_process"),
        ):
            # ---- Cycle 1 ----
            manager.manage_workers()

            # pending_count(3) < WORKER_LOW_WATER should have flagged
            # exactly one idle worker to drain as part of normal Pass 3
            drained = [w for w in manager.workers if w.get("drain")]
            assert len(drained) == 1, "expected exactly one worker flagged to drain"
            assert drained[0]["work_id"] is None
            assert drained[0]["busy"] is False

            # Only workers confirmed ready this cycle should hold claimed work
            assigned = [w for w in manager.workers if w["work_id"] is not None]
            assert len(assigned) == 3, "should claim exactly as many rows as could be assigned"
            assigned_ids = {w["work_id"] for w in assigned}
            assert assigned_ids == {work1_id, work2_id, work3_id}

            # All rows are soft-claimed (still exist, just inactive) — not lost
            assert session.query(Work).count() == 3
            assert session.query(Work).filter(Work.active.is_(True)).count() == 0

            # Simulate one successful attempt, one permanent plugin failure,
            # and one attempt that is still running.
            completed_worker = next(w for w in assigned if w["work_id"] == work1_id)
            failed_worker = next(w for w in assigned if w["work_id"] == work2_id)
            completed_worker["worker"].output_q.put("done")
            failed_worker["worker"].output_q.put("failed")

            # ---- Cycle 2 ----
            manager.manage_workers()

        # The completed row must be genuinely deleted, not just inactive
        assert session.query(Work).get(work1_id) is None, "completed work must be deleted, not stranded"

        # A plugin failure completes the attempt too. Requeueing it would run a
        # permanently broken plugin forever.
        assert session.query(Work).get(work2_id) is None, "failed work must not be requeued forever"

        # The still-in-progress row must remain tracked, not stranded either
        still_in_progress = session.query(Work).get(work3_id)
        assert still_in_progress is not None
        assert still_in_progress.active is False
        holder = next((w for w in manager.workers if w["work_id"] == work3_id), None)
        assert holder is not None, "in-progress work must still be held by a tracked worker"

        # The drained worker must be gone from self.workers and joined
        assert len(manager.workers) == 3, "drained worker must be removed"
        # sanity: holder is alive/in-progress
        assert not any(not w["worker"].is_alive() and w is holder for w in manager.workers)
        drained_process = drained[0]["worker"]
        assert drained_process.is_alive() is False, "drained worker must be joined/terminated"

        # No row is stranded: every row is either deleted (accounted
        # for above) or active=False and held by a real tracked worker.
        remaining_rows = session.query(Work).all()
        held_work_ids = {w["work_id"] for w in manager.workers if w["work_id"] is not None}
        for row in remaining_rows:
            assert row.active is False
            assert row.id in held_work_ids, f"Work row {row.id} is inactive but not held by any tracked worker"

        # pending_count must reflect reality, not a phantom non-zero count
        from owtf.managers.worklist import get_pending_count

        assert get_pending_count(session) == 0
    finally:
        session.close()
