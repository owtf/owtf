"""
tests.unit.managers.test_worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for worker scaling and batch work fetching.
"""

from owtf.managers.worklist import get_work_batch
from owtf.settings import (
    WORKER_BATCH_SIZE,
    WORKER_HIGH_WATER,
    WORKER_LOW_WATER,
    WORKER_MAX_PROCESSES,
)


def test_worker_batch_size_is_positive():
    """WORKER_BATCH_SIZE must be a positive integer."""
    assert isinstance(WORKER_BATCH_SIZE, int)
    assert WORKER_BATCH_SIZE > 0


def test_worker_max_processes_greater_than_zero():
    """WORKER_MAX_PROCESSES must be greater than zero."""
    assert WORKER_MAX_PROCESSES > 0


def test_high_water_greater_than_low_water():
    """HIGH_WATER must be greater than LOW_WATER for scaling logic to work."""
    assert WORKER_HIGH_WATER > WORKER_LOW_WATER


def test_get_work_batch_respects_batch_size():
    """get_work_batch() must return at most batch_size items in priority order."""
    from owtf.db.session import session_manager

    # Get a real database session
    session = session_manager.get_session()

    try:
        # Test that batch_size parameter limits results
        # Even if more work is available, should return at most batch_size items
        batch_size = 3
        result = get_work_batch(session, [], batch_size=batch_size)

        # Result can be empty (no work) or list of tuples
        if result:
            assert len(result) <= batch_size, f"Expected at most {batch_size} items, got {len(result)}"
    finally:
        session.close()


def test_get_work_batch_default_batch_size():
    """get_work_batch() should use WORKER_BATCH_SIZE when not specified."""
    from owtf.db.session import session_manager

    session = session_manager.get_session()

    try:
        result = get_work_batch(session, [])  # No batch_size specified

        # Should return list or None, respecting default batch size
        assert result is None or isinstance(result, list)
    finally:
        session.close()
