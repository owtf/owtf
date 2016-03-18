from owtf_testing.utils.owtftest import OWTFCliTestCase


class OWTFCliOnlyPluginsTest(OWTFCliTestCase):

    categories = ['cli', 'fast']

    def test_only_one_plugin(self):
        """Run OWTF with only one plugin."""
        self.run_owtf('-s', '-o', 'OWTF-WVS-001', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        # Test WVS-001 active AND external were run.
        self.assert_is_in_logs(
            'Target: %s://%s:%s -> Plugin: Arachni Unauthenticated (web/active)' % (self.PROTOCOL, self.IP, self.PORT),
            name='Worker',
            msg='Arachni web active plugin should have been run!')
        self.assert_is_in_logs(
            'Target: %s://%s:%s -> Plugin: Arachni Unauthenticated (web/external)' % (self.PROTOCOL, self.IP, self.PORT),
            name='Worker',
            msg='Arachni web external plugin should have been run!')
        # Test that no other plugin has been run.
        self.assert_is_not_in_logs(
            '3 - Target:',
            name='Worker',
            msg='No other plugins should have been run!')
        # Test OWTF exited cleanly
        self.assert_is_in_logs(
            'All jobs have been done. Exiting.',
            name='MainProcess',
            msg='OWTF did not finish properly!')

    def test_only_one_plugin_one_type(self):
        """Run OWTF with only one external plugin (regression #376)."""
        self.run_owtf('-s', '-o', 'OWTF-WVS-001', '-t', 'external', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        # Test WVS-001 external were run.
        self.assert_is_in_logs(
            'Target: %s://%s:%s -> Plugin: Arachni Unauthenticated (web/external)' % (self.PROTOCOL, self.IP, self.PORT),
            name='Worker',
            msg='Arachni web external plugin should have been run!')
        # Test that no other plugin has been run.
        self.assert_is_not_in_logs(
            '2 - Target:',
            name='Worker',
            msg='No other plugin should have been run!')
        # Test OWTF exited cleanly
        self.assert_is_in_logs(
            'All jobs have been done. Exiting.',
            name='MainProcess',
            msg='OWTF did not finish properly!')
