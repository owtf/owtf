from owtf_testing.utils.owtftest import OWTFCliTestCase


class OWTFCliExceptTest(OWTFCliTestCase):

    categories = ['cli']

    def test_except(self):
        """Run OWTF web plugins except one."""
        self.run_owtf('-s', '-g', 'web', '-e', 'OWTF-WVS-006', "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT))
        self.assert_is_in_logs(
            'All jobs have been done. Exiting.',
            name='MainProcess',
            msg='OWTF did not finish properly!')
        self.assert_is_not_in_logs(
            'Target: %s://%s:%s -> Plugin: Skipfish Unauthenticated' % (self.PROTOCOL, self.IP, self.PORT),
            name='Worker',
            msg='Skipfish plugin should not have been run!')
