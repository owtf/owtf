import unittest
import sys
import re
from io import BytesIO as StringIO
from os import path
from tests.testing_framework.server import HandlerBuilder, WebServerProcess
import shlex
from owtf import ProcessOptions
from framework.core import Core
import os
from tests.testing_framework.utils import ExpensiveResourceProxy
from tests.testing_framework.doubles.mock import StreamMock
import shutil
from hamcrest.library.text.stringcontains import contains_string
from hamcrest.core.assert_that import assert_that
import string
import random
from hamcrest.core.core.isequal import equal_to
import cgi


class BaseTestCase(unittest.TestCase):

    RESOURCES_DIR = "test_cases/resources/"

    def setUp(self):
        try:
            self.before()
        except AttributeError:
            pass  # The subclass does not implement the set up method

    def tearDown(self):
        try:
            self.after()
        except AttributeError:
            pass  # The subclass does not implement the tear down method

    def init_stdout_recording(self):
        self.stdout_backup = sys.stdout
        self.replace_stdout_with_string_buffer()

    def get_recorded_stdout(self, flush_buffer=False):
        output = self.stdout_content.getvalue()
        if (flush_buffer):
            self.stdout_content.close()
            self.replace_stdout_with_string_buffer()
        return output

    def replace_stdout_with_string_buffer(self):
        self.stdout_content = StringIO()
        sys.stdout = self.stdout_content

    def stop_stdout_recording(self):
        self.stdout_content.close()
        sys.stdout = self.stdout_backup

    def get_recorded_stdout_and_close(self):
        output = self.get_recorded_stdout()
        self.stop_stdout_recording()
        return output

    def get_resource_path(self, relative_path):
        return self.get_abs_path(self.RESOURCES_DIR + relative_path)

    def get_abs_path(self, relative_path):
        return path.abspath(relative_path)

class CoreInitialiser():
    """Callable class that instantiates the core object."""

    WEB = " -g web "
    NOT_INTERACTIVE = " -i no "

    def __init__(self, target):
        self.target = target

    def __call__(self):
        root_dir = path.abspath("..")  # Relative to tests/ directory
        options = self.WEB + self.NOT_INTERACTIVE + self.target  # Example options to initialise the framework
        self.core_instance = Core(root_dir)
        processed_options = self.process_options(options)
        self.core_instance.initialise_framework(processed_options)
        self.core_instance.PluginHandler.CanPluginRun = lambda arg1, arg2: True
        return self.core_instance

    def process_options(self, options):
        args = shlex.split(options)
        return ProcessOptions(self.core_instance, args)


class WebPluginTestCase(BaseTestCase):

    TARGET = "localhost:8888"
    DYNAMIC_METHOD_REGEX = "^set_(head|get|post|put|delete|options|connect)_response"
    ANCHOR_PATTERN = "href=\"%s\""
    OWTF_REVIEW_FOLDER = "owtf_review"
    LOG_FILE = "logfile"
    NOT_INTERACTIVE = " -i no "
    FROM_FILE_SUFFIX = "_from_file"
    CORE_PROXY_NAME = "core_instance_proxy"
    PLUGIN_START_TEXT = "------> Execution Start Date/Time:"

    core_instance_proxy = None

    @classmethod
    def setUpClass(cls):
        cls.clean_temp_files()  # Cleans logfile and owtf_review/ before starting
        cls.core_instance_proxy = ExpensiveResourceProxy(CoreInitialiser("http://" + cls.TARGET))
        super(WebPluginTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.core_instance_can_be_destroyed():
                core = cls.core_instance_proxy.get_instance()
                core.Finish(Report=False)  # Avoid finish reporting, it's faster
        except SystemExit:
            pass  # Exit is invoked from the core.Finish method
        finally:
            cls.clean_temp_files()  # Cleans logfile and owtf_review/ before finishing
            super(WebPluginTestCase, cls).tearDownClass()

    @classmethod
    def clean_temp_files(cls):
        if os.path.isdir(cls.OWTF_REVIEW_FOLDER):
            shutil.rmtree(cls.OWTF_REVIEW_FOLDER)
        if os.path.isfile(cls.LOG_FILE):
            os.remove(cls.LOG_FILE)

    @classmethod
    def core_instance_can_be_destroyed(cls):
        core_instance_proxy_is_defined = hasattr(cls, cls.CORE_PROXY_NAME)
        is_not_none = (getattr(cls, cls.CORE_PROXY_NAME) is not None)
        return core_instance_proxy_is_defined and is_not_none

    def setUp(self):
        """Initialise the WebPluginTestCase instance variables."""
        self.responses = {}
        self.server = None
        self.custom_handlers = []
        self.core_instance = self.core_instance_proxy.get_instance()
        self.owtf_output = ""
        super(WebPluginTestCase, self).setUp()

    def tearDown(self):
        if self.server is not None:
            self.stop_server()
        super(WebPluginTestCase, self).tearDown()

    def __getattr__(self, name):
        """
            If the method name matches with set_post_response, set_put_response,
            set_post_response_from_file, etc. generates a dynamic method.
        """
        dynamic_method_matcher = re.match(self.DYNAMIC_METHOD_REGEX, name)
        if dynamic_method_matcher is not None:
            method_name = dynamic_method_matcher.group(1)
            from_file = name.endswith(self.FROM_FILE_SUFFIX)
            return self.generate_callable_for_set_response(method_name, from_file)
        else:
            raise AttributeError("'WebPluginTestCase' object has no attribute '" + name + "'")

    def generate_callable_for_set_response(self, method_name, from_file):
        """Returns a function that will be called to set a response."""
        def dynamic_method(path, content="", headers={}, status_code=200):
                if from_file:
                    self.set_response_from_file(path, content, headers, method_name, status_code)
                else:
                    self.set_response(path, content, headers, method_name, status_code)
        return dynamic_method

    def set_response(self, path, content="", headers={}, method="get", status_code=200):
        """
            Sets the response for the server in the given path. Optionally, it
            is possible to specify the headers to be changed, the HTTP method
            to answer to, and the response HTTP status code.
        """
        if not (path in self.responses):
            self.responses[path] = {}
        self.responses[path][method] = {"content": content,
                                        "headers": headers,
                                        "code": status_code}

    def set_response_from_file(self, path, file_path, headers={}, method="get", status_code=200):
        """
            Sets the response for the server in the given path using the
            content of a file. Optionally, it is possible to specify the
            headers to be changed, the HTTP method to answer to, and the
            response HTTP status code.
        """
        response_file = open(file_path, "r")
        self.set_response(path, response_file.read(), headers, method, status_code)
        response_file.close()

    def set_custom_handler(self, path, handler_class, init_params={}):
        """Allows the use of an already implemented tornado RequestHandler"""
        self.custom_handlers.append((path, handler_class, init_params),)

    def start_server(self):
        """Creates a server process with the provided handlers and starts it."""
        autogenerated_handlers = self.build_handlers()
        handlers = autogenerated_handlers + self.custom_handlers
        self.server = WebServerProcess(handlers)
        self.server.start()

    def build_handlers(self):
        """
            For each recorded response, generates a (path, handler) tuple which
            will be passed to the Tornado web server.
        """
        handlers = []
        handler_builder = HandlerBuilder()
        for path, params in self.responses.items():
            handlers.append((path, handler_builder.get_handler(params)))
        return handlers

    def stop_server(self):
        self.server.stop()

    def owtf(self, args_string=""):
        """Runs OWTF against the test server and stores the result."""
        processed_options = self.process_options(args_string + self.NOT_INTERACTIVE + self.TARGET)
        plugin_dir, plugin = self.get_dir_and_plugin_from_options(processed_options)
        result = self.run_plugin(plugin_dir, plugin)
        self.owtf_output = "\n".join(result[:])

    def process_options(self, options):
        """Parses the command line options passed to the owtf method."""
        args = shlex.split(options)
        return ProcessOptions(self.core_instance, args)

    def get_dir_and_plugin_from_options(self, options):
        """
            Performs a plugins search through the plugin handler with the given
            criteria.
        """
        criteria = self.get_criteria_from_options(options)
        directory = os.path.abspath("../plugins/" + criteria["Group"])
        return directory, self.core_instance.Config.Plugin.GetPlugins(criteria)[0]

    def get_criteria_from_options(self, options):
        return {"Group": options["PluginGroup"],
                "Type": options["PluginType"],
                "Name": options["OnlyPlugins"][0]}

    def run_plugin(self, plugin_dir, plugin):
        """
            Runs a plugin with the current core instance and returns a list 
            with the output of the plugin and the stdout content.
        """
        result = []
        self.init_stdout_recording()
        try:
            plugin_output = self.core_instance.PluginHandler.ProcessPlugin(plugin_dir, plugin, {})
            result.append(str(plugin_output))
        except:
            result.append(str(sys.exc_info()[0]))
        finally:
            stdout_output = self.get_recorded_stdout_and_close()
            result.append(str(stdout_output))
        return result

    def assert_external_tool_started(self, times=1):
        self.assert_that_output_contains(self.PLUGIN_START_TEXT, times)

    def assert_that_output_contains_lines(self, lines):
        for line in lines:
            self.assert_that_output_contains(line)

    def assert_that_output_contains(self, substring, times=None):
        assert_that(self.owtf_output, contains_string(substring))
        if times is not None:
            assert_that(self.owtf_output.count(substring), equal_to(times))

    def generate_random_token(self, length=15):
        """Useful to identify the specified content in the plugin output."""
        charset = string.ascii_uppercase + string.ascii_lowercase + string.digits
        choices = []
        for i in range(length):
            choices.append(random.choice(charset))
        return ''.join(choices)

    def get_url(self, web_path, https=False):
        protocol = "https" if https else "http"
        return protocol + "://" + self.TARGET + web_path

    def visit_url(self, url, method=''):
        """
            Grep plugins don't make requests, so the transactions have to be
            stored previously. By using the core.Requester object, all the
            transactions will get logged.
        """
        self.core_instance.Requester.GetTransaction(True, url, Method=method)

    def generate_headers_with_tokens(self, header_names):
        headers = {}
        for name in header_names:
            headers[name] = self.generate_random_token()
        return headers
