import os
import sys
import time
import signal
import logging
import httplib

from multiprocessing import Process

import tornado.ioloop
import tornado.web


class DummyGetHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")


class DummyWebApplication(tornado.web.Application):

    def log_request(self, handler):
        pass


class WebServerProcess(object):
    """Handles a child process that executes the tornado application."""

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.process = None

    def start(self):
        """
            Creates a web server in another process and wait until it is ready to
            handle requests.
        """
        # Create the web application
        self.application = DummyWebApplication([(r'/', DummyGetHandler)])
        self.process = Process(
            target=start_application,
            args=(self.application, self.ip, self.port))
        self.process.start()
        self.wait_until_server_is_ready()

    def wait_until_server_is_ready(self):
        while not self.server_is_ready():
            # If it's not ready, wait for it
            time.sleep(0.1)

    def test_connection(self):
        conn = httplib.HTTPConnection("%s:%s" % (self.ip, self.port))
        conn.request("GET", "/")

    def stop(self):
        """Stops the web server and wait until it has sucesfully cleaned up."""
        if self.is_alive():
            os.kill(self.process.pid, signal.SIGINT)
            self.wait_for_server_shutdown()
        self.process = None

    def wait_for_server_shutdown(self):
        while self.server_is_ready():  # Wait until server is down
            time.sleep(0.1)

    def server_is_ready(self):
        try:
            self.test_connection()
            return True
        except:
            return False

    def is_alive(self):
        """Test if the server process is alive and running."""
        if (self.process is None):
            return False
        else:
            return self.process.is_alive()


def start_application(application, ip, port):
    """Callable to be executed in the subprocess."""
    application.listen(str(port), address=ip)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:  # Exit cleanly
        sys.exit(0)
