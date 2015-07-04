from hamcrest import *
from tests.testing_framework.base_test_cases import WebPluginTestCase
from tests.testing_framework.server import PORT
import httplib
from os import path
from flexmock import flexmock
import subprocess
import re
import shlex
import tornado.web


class CustomHandler(tornado.web.RequestHandler):

    def initialize(self, message):
        self.message = message

    def get(self):
        self.write(self.message)


class WebPluginTestCaseTests(WebPluginTestCase):

    HOST = "localhost"  

    def test_that_defined_responses_are_set_correctly(self):
        path_response = {"/first": "first",
                         "/second": "second"}
        for path, content in path_response.items():
            self.set_response(path, content)
        self.start_server()

        first_response = self.perform_request("/first")
        second_response = self.perform_request("/second")

        assert_that(first_response.read(), equal_to(path_response["/first"]))
        assert_that(second_response.read(), equal_to(path_response["/second"]))

    def test_set_response_from_file(self):
        file_path = path.abspath("test_cases/resources/response_example.html")
        self.set_response_from_file("/", file_path)
        self.start_server()

        response = self.perform_request("/").read()

        response_file = open(file_path, "r")
        assert_that(response, equal_to(response_file.read()))
        response_file.close()

    def test_that_it_is_possible_to_define_headers_to_be_returned_by_the_server(self):
        headers = {"Custom-Header": "value"}
        self.set_response("/", "content", headers)
        self.start_server()

        response = self.perform_request("/")

        assert_has_header(response, "Custom-Header", "value")

    def test_that_dynamic_methods_facilitate_to_set_response_for_other_methods(self):
        content = "content"
        self.set_post_response("/", content)  # auto-generated method
        self.start_server()

        response = self.perform_request("/", method="POST")

        assert_that(response.read(), equal_to(content))

    def test_dynamic_methods_with_file_input(self):
        file_path = path.abspath("test_cases/resources/response_example.html")
        self.set_post_response_from_file("/", file_path)
        self.start_server()

        response = self.perform_request("/", "POST").read()

        response_file = open(file_path, "r")
        assert_that(response, equal_to(response_file.read()))
        response_file.close()

    def test_setting_different_methods_to_the_same_path(self):
        self.set_get_response("/", "one")
        self.set_post_response("/", "two")
        self.start_server()

        get_response = self.perform_request("/").read()
        post_response = self.perform_request("/", "POST").read()

        assert_that(get_response, equal_to("one"))
        assert_that(post_response, equal_to("two"))

    def test_that_running_owtf_the_output_of_the_plugin_is_stored(self):
        flexmock(self)
        self.should_receive("run_plugin").and_return(["some_output"]).once()
 
        self.owtf("-g web -t semi_passive -o Spiders_Robots_and_Crawlers")
 
        assert_that(self.owtf_output, contains_string("some_output"))

    def test_that_it_is_possible_to_define_a_custom_handler(self):
        self.set_custom_handler("/", CustomHandler, {"message": "hello"})
        self.start_server()

        response = self.perform_request("/").read()

        assert_that(response, equal_to("hello"))

    def test_that_it_is_possible_to_specify_the_response_code(self):
        self.set_get_response("/", "", status_code=404)
        self.start_server()

        response = self.perform_request("/")

        assert_that(response.status, equal_to(404))

    def perform_request(self, path, method="GET"):
        connection = httplib.HTTPConnection(self.HOST, PORT)
        connection.request(method, path)
        return connection.getresponse()


def assert_has_header(response, header_name, header_value=None):
    header = response.getheader(header_name, default=None)
    assert_that(header is not None)
    if header_value is not None:
        assert_that(header, equal_to(header_value))
