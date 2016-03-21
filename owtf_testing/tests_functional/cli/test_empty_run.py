import mock
from hamcrest import *

from owtf_testing.utils.owtftest import OWTFCliTestCase


class OWTFCliEmptyRunTest(OWTFCliTestCase):

    categories = ['cli', 'fast']

    def test_cli_empty_run(self):
        """Run OWTF without parameters."""
        self.run_owtf()
        self.assert_is_in_logs(
            'All jobs have been done. Exiting.',
            name='MainProcess',
            msg='OWTF did not finish properly!')
