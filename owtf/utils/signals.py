"""
owtf.utils.signals
~~~~~~~~~~~~~~~~~~

Most of it taken from the Flask code.
"""

signals_available = False
try:
    from blinker import Namespace

    signals_available = True
except ImportError:

    class Namespace(object):

        def signal(self, name, doc=None):
            return _FakeSignal(name, doc)

    class _FakeSignal(object):
        """If blinker is unavailable, create a fake class with the same
        interface that allows sending of signals but will fail with an
        error on anything else.  Instead of doing anything on send, it
        will just ignore the arguments and do nothing instead.
        """

        def __init__(self, name, doc=None):
            self.name = name
            self.__doc__ = doc

        def _fail(self, *args, **kwargs):
            raise RuntimeError("Signalling support is unavailable because the blinker library is not installed.")

        send = lambda *a, **kw: None
        connect = disconnect = has_receivers_for = receivers_for = temporarily_connected_to = connected_to = _fail
        del _fail


__all__ = ["_signals", "owtf_exit", "owtf_start", "workers_finish"]

# The namespace for code signals.
_signals = Namespace()

# Core signals
owtf_start = _signals.signal("owtf-start")
owtf_exit = _signals.signal("owtf-exit")
workers_finish = _signals.signal("workers-finish")
