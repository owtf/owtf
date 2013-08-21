import tornado.ioloop
import tornado.web
from multiprocessing import Process
import httplib
import time
import random
import string
import os
import signal
import sys

PORT = 8888


class WebServerProcess():
    """Handles a child process that executes the tornado application."""

    def __init__(self, handlers=[(), ]):
        self.handlers = handlers
        self.process = None

    def start(self):
        application = self.create_application()
        self.process = Process(target=start_application, args=(application,))
        self.process.start()
        self.wait_until_server_is_ready()

    def wait_until_server_is_ready(self):
        while not self.server_is_ready():
            # If it's not ready, wait for it
            time.sleep(0.1)

    def test_connection(self):
        conn = httplib.HTTPConnection("localhost:" + str(PORT))
        conn.request("GET", "/")

    def stop(self):
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
        if (self.process is None):
            return False
        else:
            return self.process.is_alive()

    def create_application(self):
        return tornado.web.Application(handlers=self.handlers)


def start_application(application):
    application.listen(PORT)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:  # Exit cleanly
        sys.exit(0)


class HandlerBuilder():
    """Creates implementation classes for the tornado request handlers."""

    def get_handler(self, params):
        """Creates a handler class with bound methods and returns it."""
        #handler_class = self.create_handler_class()
        methods = {}
        for method_name, options in params.items():
            method_impl = self.create_method_implementation(options["headers"], options["content"], options["code"])
            methods[method_name] = method_impl
        return self.create_handler_class(methods)

    def create_method_implementation(self, headers, content, code):
        """Creates the implementation of the dynamic method"""
        def implementation(self):
            for name, value in headers.items():
                self.set_header(name, value)
            if isinstance(content, list):
                for line in content:
                    self.write(line)
                    self.write('\r\n')
            else:
                self.write(content)
            self.set_status(code)
        return implementation

    def create_handler_class(self, methods):
        """Creates a subclass of a tornado RequestHandler"""
        handler_class = type("handler_class" + self.get_random_string(),
                             (tornado.web.RequestHandler, ),
                             methods)
        return handler_class

    def get_random_string(self):
        """Used to generate a class name randomly, to avoid collisions with other classes."""
        charset = string.ascii_uppercase + string.ascii_lowercase + string.digits
        choices = []
        for i in range(10):
            choices.append(random.choice(charset))
        return ''.join(choices)
