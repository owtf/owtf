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
