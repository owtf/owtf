from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from tests.testing_framework.doubles.files import FileMock

DEFAULT_CONTENT = ["first line\n", "second line\n", "third line\n"]


class FileMockTests(BaseTestCase):

    def before(self):
        self.mock = FileMock(DEFAULT_CONTENT)

    def test_file_mock_is_iterable(self):
        counter = 0
        for line in self.mock:
            assert_that(line, equal_to(DEFAULT_CONTENT[counter]))
            counter += 1

    def test_file_mock_is_readable_as_a_file(self):
        expected_output = "".join(DEFAULT_CONTENT)

        assert_that(self.mock.read(), equal_to(expected_output))
        self.mock.close()
