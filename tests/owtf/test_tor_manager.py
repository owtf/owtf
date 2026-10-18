import inspect
import socket
import threading
import unittest
from unittest import mock

from owtf.proxy.tor_manager import TOR_manager


class FakeTorControlPort(object):
    """A throwaway stand-in for the TOR control port.

    It accepts one connection and answers each command it receives with the
    next canned reply, recording the raw bytes it was sent along the way.
    """

    def __init__(self, replies):
        self.replies = list(replies)
        self.received = []
        self._server = socket.socket()
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", 0))
        self._server.listen(1)
        self.port = self._server.getsockname()[1]
        self._thread = threading.Thread(target=self._serve)
        self._thread.daemon = True
        self._thread.start()

    def _serve(self):
        try:
            conn, _ = self._server.accept()
        except OSError:
            return
        with conn:
            for reply in self.replies:
                command = conn.recv(1024)
                if not command:
                    break
                self.received.append(command)
                conn.sendall(reply)

    def stop(self):
        self._server.close()
        self._thread.join(timeout=2)


class TestTorManager(unittest.TestCase):
    """TOR_manager was left behind on Python 2.

    is_tor_running() called the removed 'commands' module, the control socket
    was handed str instead of bytes and then compared against a str reply,
    msg_start_tor() declared a self that a staticmethod never receives, and
    run() passed a second self to an already bound method. Every entry point
    of the class raised before it could do any work.
    """

    def make_manager(self, replies, password="owtf", renew_minutes="5"):
        server = FakeTorControlPort(replies)
        self.addCleanup(server.stop)
        manager = TOR_manager(["127.0.0.1", "9050", str(server.port), password, renew_minutes])
        return manager, server

    def test_authenticate_talks_bytes_to_the_control_port(self):
        _, server = self.make_manager([b"250 OK\r\n"])

        self.assertEqual(server.received[0], b'AUTHENTICATE "owtf"\r\n')

    def test_authenticate_aborts_when_the_password_is_rejected(self):
        # abort_framework() ends the run via sys.exit().
        with self.assertRaises(SystemExit):
            self.make_manager([b"515 Authentication failed\r\n"])

    def test_renew_ip_requests_a_new_circuit_and_reports_success(self):
        manager, server = self.make_manager([b"250 OK\r\n", b"250 OK\r\n"])

        self.assertTrue(manager.renew_ip())
        self.assertEqual(server.received[1], b"SIGNAL NEWNYM\r\n")

    def test_renew_ip_reports_failure_without_raising(self):
        manager, _ = self.make_manager([b"250 OK\r\n", b"551 Internal error\r\n"])

        self.assertFalse(manager.renew_ip())

    def test_is_tor_running_answers_without_the_commands_module(self):
        self.assertIsInstance(TOR_manager.is_tor_running(), bool)

    def test_msg_start_tor_takes_no_arguments(self):
        self.assertEqual(list(inspect.signature(TOR_manager.msg_start_tor).parameters), [])
        TOR_manager.msg_start_tor()

    def test_run_does_not_hand_the_bound_method_a_second_self(self):
        manager, _ = self.make_manager([b"250 OK\r\n"])

        with mock.patch("owtf.proxy.tor_manager.Process") as process:
            manager.run()

        _, kwargs = process.call_args
        self.assertEqual(kwargs.get("args", ()), ())
        # The recorded target must be callable as-is, with nothing extra.
        self.assertEqual(list(inspect.signature(kwargs["target"]).parameters), [])
        process.return_value.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
