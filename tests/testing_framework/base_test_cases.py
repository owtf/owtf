from io import BytesIO as StringIO
from os import path
from tests.testing_framework.server import HandlerBuilder, WebServerProcess
from tests.testing_framework.utils import ExpensiveResourceProxy
from hamcrest.library.text.stringcontains import contains_string
from hamcrest.core.assert_that import assert_that
from hamcrest.core.core.isequal import equal_to
from hamcrest.library.text.stringmatches import matches_regexp
from hamcrest.library.number.ordering_comparison import greater_than_or_equal_to
from owtf import ProcessOptions
from framework.core import Core
import unittest
import sys
import re
import shutil
import string
import random
import shlex
import os


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
        """Replaces the system stdout with a string buffer."""
        self.stdout_backup = sys.stdout
        self.replace_stdout_with_string_buffer()

    def get_recorded_stdout(self, flush_buffer=False):
        """Gets the content of the stream buffer, and, optionally, flush it."""
        output = self.stdout_content.getvalue()
        if (flush_buffer):
            self.stdout_content.close()
            self.replace_stdout_with_string_buffer()
        return output

    def replace_stdout_with_string_buffer(self):
        self.stdout_content = StringIO()
        sys.stdout = self.stdout_content

    def stop_stdout_recording(self):
        """Close the string buffer, and restore the system stdout."""
        self.stdout_content.close()
        sys.stdout = self.stdout_backup

    def get_recorded_stdout_and_close(self):
        output = self.get_recorded_stdout()
        self.stop_stdout_recording()
        return output

    def get_resource_path(self, relative_path):
        """Shortcut to retrieve the absolute path of a test resource."""
        return self.get_abs_path(self.RESOURCES_DIR + relative_path)

    def get_abs_path(self, relative_path):
        """Shortcut to retrieve the absolute path of a file"""
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
        self.core_instance.PluginHandler.CanPluginRun = lambda arg1, arg2: True  # In tests, we always want to run the plugins
        return self.core_instance

    def process_options(self, options):
        args = shlex.split(options)
        return ProcessOptions(self.core_instance, args)


class PluginTestCase(BaseTestCase):

    TARGET = "localhost"
    PLUGIN_START_TEXT = "------> Execution Start Date/Time:"
    CORE_PROXY_NAME = "core_instance_proxy"
    OWTF_REVIEW_FOLDER = "owtf_review"
    LOG_FILE = "logfile"
    NOT_INTERACTIVE = " -i no "
    BUG_FOUND_BANNER = "OWTF BUG: Please report the sanitised information below to help make this better. Thank you."
    BUG_FOUND_MESSAGE = "The test failed because a bug was found during the execution."

    core_instance_proxy = None

    @classmethod
    def setUpClass(cls):
        """Prepares the OWTF instance, and clean the possible existing temp files"""
        cls.clean_temp_files()  # Cleans logfile and owtf_review/ before starting
        cls.core_instance_proxy = ExpensiveResourceProxy(CoreInitialiser("http://" + cls.TARGET))
        super(PluginTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """Finish the OWTF instance correctly, and clean temp files."""
        try:
            if cls.core_instance_can_be_destroyed():
                core = cls.core_instance_proxy.get_instance()
                core.Finish(Report=False)  # Avoid finish reporting, it's faster
        except SystemExit:
            pass  # Exit is invoked from the core.Finish method
        finally:
            cls.clean_temp_files()  # Cleans logfile and owtf_review/ before finishing
            super(PluginTestCase, cls).tearDownClass()

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
        """Restart the instance variables for each test"""
        super(BaseTestCase, self).setUp()
        self.core_instance = self.core_instance_proxy.get_instance()
        self.owtf_output = ""

    def owtf(self, args_string=""):
        """Runs OWTF against the test server and stores the result."""
        processed_options = self.process_options(args_string + self.NOT_INTERACTIVE + self.TARGET)
        plugin_dir, plugin = self.get_dir_and_plugin_from_options(processed_options)
        result = self.run_plugin(plugin_dir, plugin)
        self.owtf_output = "\n".join(result[:])
        self.check_for_bugs()

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
            result.append(stdout_output)
        return result

    def check_for_bugs(self):
        if self.owtf_output.count(self.BUG_FOUND_BANNER) > 0:
            print self.owtf_output
            self.fail(self.BUG_FOUND_MESSAGE)

    def assert_external_tool_started(self, times):
        """Assert that the plugin started a given number of tools."""
        self.assert_that_output_contains(self.PLUGIN_START_TEXT, times)

    def assert_that_output_contains_lines(self, lines):
        """Assert that the output of the plugin contains a set of strings."""
        for line in lines:
            self.assert_that_output_contains(line)

    def assert_that_output_contains(self, substring, times=None):
        """Assert that the output of the plugin contains the given content."""
        assert_that(self.owtf_output, contains_string(substring))
        if times is not None:
            assert_that(self.owtf_output.count(substring), equal_to(times))

    def assert_that_output_matches_more_than(self, regex, times):
        """Assert that the output matches a given regular expression a specified number of times."""
        assert_that(self.owtf_output, matches_regexp(regex))
        if times is not None:
            times_replaced = self._get_number_of_occurences_for(regex)
            assert_that(times_replaced, greater_than_or_equal_to(times))

    def _get_number_of_occurences_for(self, regex):
        token = self.generate_random_token()
        output_copy = self.owtf_output
        sub_result, times_replaced = re.subn(regex, token, output_copy)
        return times_replaced

    def generate_random_token(self, length=15):
        """Useful to identify the specified content in the plugin output."""
        charset = string.ascii_uppercase + string.ascii_lowercase + string.digits
        choices = []
        for i in range(length):
            choices.append(random.choice(charset))
        return ''.join(choices)

    def get_resources(self, resource_name):
        """Shortcut to the Config.GetResources method."""
        return self.core_instance.Config.GetResources(resource_name)


class WebPluginTestCase(PluginTestCase):

    HOST = "localhost"
    IP = "127.0.0.1"
    PORT = "8888"
    TARGET = "%s:%s" % (HOST, PORT)
    ANCHOR_PATTERN = "href=\"%s\""
    PASSIVE_LINK_PATTERN = (ANCHOR_PATTERN % (".*" + HOST + "|" + IP + "|\?.+=" + HOST + ".*"))
    DYNAMIC_METHOD_REGEX = "^set_(head|get|post|put|delete|options|connect)_response"
    FROM_FILE_SUFFIX = "_from_file"

    @classmethod
    def setUpClass(cls):
        super(WebPluginTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(WebPluginTestCase, cls).tearDownClass()

    def setUp(self):
        """Initialise the WebPluginTestCase instance variables."""
        super(WebPluginTestCase, self).setUp()
        self.responses = {}
        self.server = None
        self.custom_handlers = []

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

    def check_link_generation_for_resources(self, resources_name):
        """Check that the given resources are correctly linked in the output of the plugin."""
        if not isinstance(resources_name, list):
            resources_name = [resources_name]
        for resource in resources_name:
            times = len(self.get_resources(resource))
            # The pattern should match at least as many times as resources for that name
            self.assert_that_output_matches_more_than(self.PASSIVE_LINK_PATTERN, times)

    def get_url(self, web_path, https=False):
        """Get an absolute URL from a relative URL."""
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
        """
            Generates a dictionary using the header_names as keys and random strings as
            values.
        """
        headers = {}
        for name in header_names:
            headers[name] = self.generate_random_token()
        return headers
