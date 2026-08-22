"""
tests.unit.managers.test_worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for worker management and batch work fetching.
"""
from owtf.managers.worklist import get_work_batch
from owtf.settings import WORKER_BATCH_SIZE, WORKER_HIGH_WATER, WORKER_LOW_WATER, WORKER_MAX_PROCESSES


def test_high_water_greater_than_low_water():
    """HIGH_WATER must be greater than LOW_WATER for proper scaling."""
    assert WORKER_HIGH_WATER > WORKER_LOW_WATER


def test_worker_batch_size_configured():
    """WORKER_BATCH_SIZE must be configured and positive."""
    assert WORKER_BATCH_SIZE > 0


def test_worker_max_processes_configured():
    """WORKER_MAX_PROCESSES must be configured and positive."""
    assert WORKER_MAX_PROCESSES > 0


def test_get_work_batch_respects_batch_size():
    """get_work_batch() must return at most batch_size items."""
    from owtf.db.session import get_scoped_session

    session = get_scoped_session()
    try:
        batch_size = 3
        result = get_work_batch(session, [], batch_size=batch_size)

        # Result can be empty (no work) or list
        if result:
            assert len(result) <= batch_size, f"Expected at most {batch_size} items, got {len(result)}"
    finally:
        session.close()


def test_get_work_batch_default_batch_size():
    """get_work_batch() should use WORKER_BATCH_SIZE when not specified."""
    from owtf.db.session import get_scoped_session

    session = get_scoped_session()
    try:
        result = get_work_batch(session, [])  # No batch_size specified

        # Should return list or None, respecting default batch size
        assert result is None or isinstance(result, list)
        if result:
            assert len(result) <= WORKER_BATCH_SIZE
    finally:
        session.close()


def test_work_batch_with_idle_workers_no_loss():
    """Batch work should not be lost when workers are idle."""
    from owtf.db.session import get_scoped_session
    from owtf.managers.worklist import get_work_batch
    from owtf.models.work import Work

    session = get_scoped_session()
    try:
        # Insert 10 work items
        for i in range(10):
            work = Work(target_id=1, plugin_key=f"plugin_{i}", active=True)
            session.add(work)
        session.commit()

        # Fetch batch of 5
        batch = get_work_batch(session, [], batch_size=5)
        assert len(batch) == 5

        # Check remaining 5 still exist
        remaining = session.query(Work).filter(Work.active.is_(True)).count()
        assert remaining == 5

        # Fetch second batch
        batch2 = get_work_batch(session, [], batch_size=5)
        assert len(batch2) == 5

        # All work should be assigned
        remaining = session.query(Work).filter(Work.active.is_(True)).count()
        assert remaining == 0

    finally:
        session.close()
