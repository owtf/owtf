import inspect
import time
import unittest

import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.testing

from owtf.proxy.proxy import ProxyHandler


class TestLiveInterceptionSourceNoLongerBlocks(unittest.TestCase):
    """Regression guard directly on the fixed source: the live-interception
    poll loop inside ProxyHandler.get() must not call time.sleep() again.
    """

    def test_get_no_longer_calls_time_sleep_in_poll_loop(self):
        source = inspect.getsource(ProxyHandler.get)
        self.assertNotIn("time.sleep(LIVE_INTERCEPTION_DELAY)", source)
        self.assertIn("tornado.gen.sleep(LIVE_INTERCEPTION_DELAY)", source)


class TestPollLoopConcurrency(tornado.testing.AsyncTestCase):
    """proxy.py's live-interception poll loop sleeps between decision checks.
    time.sleep() blocks the whole Tornado IOLoop thread for the duration of
    the sleep, so every other connection through the proxy freezes;
    tornado.gen.sleep() yields control back to the IOLoop so other coroutines
    make progress concurrently.

    These tests reproduce that loop shape (bounded iterations, sleep between
    checks) running two instances side by side and assert on the *interleaving
    order* of their ticks, not on wall-clock elapsed time. Order is decided by
    whether the sleep yields, so the assertions are deterministic regardless
    of machine load (a timing-threshold assertion would be flaky on a busy CI
    runner).
    """

    ITERATIONS = 4
    DELAY = 0.02

    @tornado.testing.gen_test
    def test_gen_sleep_interleaves_two_pollers(self):
        # With a yielding sleep, poller "b" starts ticking before poller "a"
        # has finished all its ticks -> the two tick streams interleave.
        order = []

        @tornado.gen.coroutine
        def poller(key):
            for _ in range(self.ITERATIONS):
                order.append(key)
                yield tornado.gen.sleep(self.DELAY)

        yield [poller("a"), poller("b")]

        self.assertEqual(order.count("a"), self.ITERATIONS)
        self.assertEqual(order.count("b"), self.ITERATIONS)
        first_b = order.index("b")
        last_a = len(order) - 1 - order[::-1].index("a")
        self.assertLess(first_b, last_a, f"pollers did not interleave: {order}")

    @tornado.testing.gen_test
    def test_blocking_sleep_would_serialize_the_pollers(self):
        # Demonstrates the bug this fix removes: with a blocking sleep the two
        # pollers cannot overlap -> ticks come out fully serialized ("aaaabbbb"),
        # so the first "b" only appears after the last "a".
        order = []

        def blocking_sleep(delay):
            time.sleep(delay)
            future = tornado.concurrent.Future()
            future.set_result(None)
            return future

        @tornado.gen.coroutine
        def poller(key):
            for _ in range(self.ITERATIONS):
                order.append(key)
                yield blocking_sleep(self.DELAY)

        yield [poller("a"), poller("b")]

        self.assertEqual(order.count("a"), self.ITERATIONS)
        self.assertEqual(order.count("b"), self.ITERATIONS)
        first_b = order.index("b")
        last_a = len(order) - 1 - order[::-1].index("a")
        self.assertGreater(first_b, last_a, f"expected serialized order, got: {order}")


if __name__ == "__main__":
    unittest.main()
