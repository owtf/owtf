from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from tests.testing_framework.server import WebServerProcess, PORT
import tornado.web
import httplib


MESSAGE = "hello, world!"


class TestHandler(tornado.web.RequestHandler):  # Test implementation used to initialise the server
    def get(self):
        self.write(MESSAGE)


class WebServerProcessTests(BaseTestCase):

    def before(self):
        self.server = WebServerProcess([(r"/", TestHandler)])
        self.server.start()

    def after(self):
        self.server.stop()

    def test_that_the_process_starts_succesfully(self):
        assert_that(self.server.is_alive())

    def test_that_the_process_stops_succesfully(self):
        self.server.stop()
        assert_that(self.server.is_alive(), is_(False))

    def test_that_the_server_works(self):
        connection = httplib.HTTPConnection(host="localhost", port=PORT)
        connection.request("GET", "/")
        response = connection.getresponse().read()

        assert_that(response, equal_to(MESSAGE))
