import unittest
import sys
from io import BytesIO as StringIO


class BaseTestCase(unittest.TestCase):

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
