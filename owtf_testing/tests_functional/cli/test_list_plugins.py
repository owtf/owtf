import mock
from hamcrest import *

from owtf_testing.utils.owtftest import OWTFCliTestCase


class OWTFCliListPluginsTest(OWTFCliTestCase):

    categories = ['cli']

    def test_cli_list_plugins_aux(self):
        """Run OWTF to list the aux plugins."""
        expected = ['Available AUXILIARY plugins', 'exploit', 'smb', 'bruteforce', 'dos', 'wafbypasser', 'se', 'rce', 'selenium']

        self.run_owtf('-l', 'aux')
        self.assert_are_in_logs(expected, name='MainProcess')
        self.run_owtf('--list_plugins', 'aux')
        self.assert_are_in_logs(expected, name='MainProcess')

    def test_cli_list_plugins_net(self):
        """Run OWTF to list the net plugins."""
        expected = ['Available NET plugins', 'active', 'bruteforce']

        self.run_owtf('-l', 'net')
        self.assert_are_in_logs(expected, name='MainProcess')
        self.run_owtf('--list_plugins', 'net')
        self.assert_are_in_logs(expected, name='MainProcess')

    def test_cli_list_plugins_web(self):
        """Run OWTF to list the web plugins."""
        expected = ['Available WEB plugins', 'external', 'active', 'passive', 'grep', 'semi_passive']

        self.run_owtf('-l', 'web')
        self.assert_are_in_logs(expected, name='MainProcess')
        self.run_owtf('--list_plugins', 'web')
        self.assert_are_in_logs(expected, name='MainProcess')
