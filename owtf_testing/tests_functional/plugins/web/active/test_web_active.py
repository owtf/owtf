import mock
from hamcrest import *

from owtf_testing.utils.owtftest import OWTFCliWebPluginTestCase


class OWTFCliWebActivePluginTest(OWTFCliWebPluginTestCase):

    categories = ['plugins', 'web', 'active']

    def test_web_active_wvs_001(self):
        """Test OWTF web active WVS 001 plugin."""
        self.run_owtf('-o', 'OWTF-WVS-001', '-t', 'active', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        self.assert_is_in_logs(
            '1 - Target: %s://%s:%s -> Plugin: Arachni Unauthenticated (web/active)' % (self.PROTOCOL, self.IP, self.PORT),
            name='Worker',
            msg='Arachni web active plugin should have been run!')
        self.assert_is_in_logs(
            'Execution Start Date/Time:',
            name='Worker',
            msg='Arachni web active plugin should have been started!')
        # Test arachni didn't raise an error
        self.assert_is_not_in_logs(
            'unrecognized option',
            name='Worker',
            msg='An error occured when running Arachni web active plugin!')
        # Test no other plugin has been run.
        self.assert_is_not_in_logs(
            '2 - Target:',
            name='Worker',
            msg='No other plugins should have been run!')
        # Test OWTF exited cleanly.
        self.assert_is_in_logs(
            'All jobs have been done. Exiting.',
            name='MainProcess',
            msg='OWTF did not finish properly!')

    def test_web_active_wvs_006(self):
        """Test OWTF web active WVS 006 plugin."""
        self.run_owtf('-o', 'OWTF-WVS-006', '-t', 'active', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        # Test Skipfish went OK.
        self.assert_is_in_logs(
            '1 - Target: %s://%s:%s -> Plugin: Skipfish Unauthenticated (web/active)' % (self.PROTOCOL, self.IP, self.PORT),
            name='Worker',
            msg='Skipfish web active plugin should have been run!')
        self.assert_is_in_logs(
            'Execution Start Date/Time:',
            name='Worker',
            msg='Skipfish web active plugin should have been started!')
        self.assert_is_in_logs(
            'This was a great day for science!',
            name='Worker',
            msg='Skipfish did not finish properly!')
        # Test no other plugin has been run.
        self.assert_is_not_in_logs(
            '2 - Target:',
            name='Worker',
            msg='No other plugins should have been run!')
        # Test OWTF exited cleanly.
        self.assert_is_in_logs(
            'All jobs have been done. Exiting.',
            name='MainProcess',
            msg='OWTF did not finish properly!')
