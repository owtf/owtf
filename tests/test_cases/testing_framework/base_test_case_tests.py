from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
import sys


class BaseTestCaseTests(BaseTestCase):

    def test_stdout_recording(self):
        expected = "Some output"

        self.init_stdout_recording()
        print expected
        received = self.get_recorded_stdout()
        self.stop_stdout_recording()

        assert_that(received, equal_to(expected + "\n"))

    def test_stdout_recording_multiple_lines(self):
        first_line = "Some output"
        second_line = "More output"
        expected = first_line + "\n" + second_line + "\n"

        self.init_stdout_recording()
        print first_line
        print second_line
        received = self.get_recorded_stdout()
        self.stop_stdout_recording()

        assert_that(received, equal_to(expected))

    def test_stdout_buffer_flushing(self):
        expected = "Some output"

        self.init_stdout_recording()
        print expected
        first_received = self.get_recorded_stdout(True)
        print expected
        second_received = self.get_recorded_stdout()
        self.stop_stdout_recording()

        assert_that(first_received, equal_to(expected + "\n"))
        assert_that(second_received, equal_to(expected + "\n"))

    def test_stdout_recording_and_close(self):
        original_stdout = sys.stdout

        self.init_stdout_recording()
        print "Some output"
        received = self.get_recorded_stdout_and_close()

        assert_that(received is not None)
        assert_that(sys.stdout, same_instance(original_stdout))
