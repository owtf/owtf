import mock
from hamcrest import *

from owtf_testing.utils.owtftest import OWTFCliWebPluginTestCase


class OWTFCliWebPluginTest(OWTFCliWebPluginTestCase):

    categories = ['plugins', 'web']

    def test_web_active(self):
        """Test OWTF WEB active plugins."""
        self.run_owtf('-g', 'web', '-t', 'active', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        # Test OWTF exited cleanly.
        self.assert_is_in_logs('All jobs have been done. Exiting.', name='MainProcess')

    def test_web_passive(self):
        """Test OWTF WEB passive plugins."""
        self.run_owtf('-g', 'web', '-t', 'passive', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        # Test OWTF exited cleanly.
        self.assert_is_in_logs('All jobs have been done. Exiting.', name='MainProcess')

    def test_web_semi_passive(self):
        """Test OWTF WEB semi-passive plugins."""
        self.run_owtf('-g', 'web', '-t', 'semi_passive', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        # Test OWTF exited cleanly.
        self.assert_is_in_logs('All jobs have been done. Exiting.', name='MainProcess')

    def test_web_external(self):
        """Test OWTF WEB external plugins."""
        self.run_owtf('-g', 'web', '-t', 'external', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        # Test OWTF exited cleanly.
        self.assert_is_in_logs('All jobs have been done. Exiting.', name='MainProcess')

    def test_web_grep(self):
        """Test OWTF WEB grep plugins."""
        self.run_owtf('-g', 'web', '-t', 'grep', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        # Test OWTF exited cleanly.
        self.assert_is_in_logs('All jobs have been done. Exiting.', name='MainProcess')
