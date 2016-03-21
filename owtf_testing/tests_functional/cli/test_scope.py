import mock
import unittest
from hamcrest import *

from owtf_testing.utils.owtftest import OWTFCliTestCase


class OWTFCliScopeTest(OWTFCliTestCase):

    categories = ['cli']

    def test_cli_target_is_valid_ip(self):
        """Run OWTF with a valid IP target (regression #375)."""
        self.run_owtf('-s', '%s:%s' % (self.IP, self.PORT))
        self.assert_is_in_logs(
            '(net/',
            name='Worker',
            msg='Net plugins should have been run!')
        self.assert_is_not_in_logs(
            '(web/',
            name='Worker',
            msg='Web plugins should not have been run!')
        self.assert_is_not_in_logs(
            '(aux/',
            name='Worker',
            msg='Web plugins should not have been run!')
        self.assert_is_in_logs(
            "All jobs have been done. Exiting.",
            name='MainProcess',
            msg='OWTF did not finish properly!')

    def test_cli_target_is_invalid(self):
        """Run OWTF with an invalid target."""
        invalid_target = 'a' * 63 + '.invalid'
        self.run_owtf('%s://%s' % (self.PROTOCOL, invalid_target))
        self.assert_is_in_logs(
            "Unable to resolve: '%s'" % invalid_target,
            name='MainProcess',
            msg='OWTF should not have resolved the address')

    def test_cli_target_is_valid_http(self):
        """Run OWTF with a valid http target."""
        self.run_owtf('-s', '%s://%s:%s' % (self.PROTOCOL, self.DOMAIN, self.PORT))
        self.assert_is_in_logs('(web/', name='Worker')
        self.assert_is_not_in_logs('(net/', name='Worker')
        self.assert_is_not_in_logs('(aux/', name='Worker')
        self.assert_is_in_logs(
            "All jobs have been done. Exiting.",
            name='MainProcess',
            msg='OWTF did not finish properly!')

    def test_cli_target_are_mixed(self):
        """Run OWTF with a valid http target and a valid IP one (regression #375)."""
        self.run_owtf(
            '-s',
            '%s://%s:%s' % (self.PROTOCOL, self.DOMAIN, self.PORT),
            '%s://%s:%s' % (self.PROTOCOL, self.IP, self.PORT))
        self.assert_is_in_logs('(web/', name='Worker')
        self.assert_is_in_logs('(net/', name='Worker')
        self.assert_is_not_in_logs('(aux/', name='Worker')
        self.assert_is_in_logs(
            "All jobs have been done. Exiting.",
            name='MainProcess',
            msg='OWTF did not finish properly!')

    def test_cli_target_are_mixed_but_web_specified(self):
        """Run OWTF with a valid http target, a valid IP one and web group (regression #375)."""
        self.run_owtf(
            '-s',
            '-g', 'web',
            '%s://%s:%s' % (self.PROTOCOL, self.DOMAIN, self.PORT),
            '%s://%s:%s' % (self.PROTOCOL, self.IP, self.PORT))
        self.assert_is_in_logs('(web/', name='Worker')
        self.assert_is_not_in_logs('(net/', name='Worker')
        self.assert_is_not_in_logs('(aux/', name='Worker')
        self.assert_is_in_logs(
            "All jobs have been done. Exiting.",
            name='MainProcess',
            msg='OWTF did not finish properly!')

    def test_cli_target_are_mixed_but_net_specified(self):
        """Run OWTF with a valid http target, a valid IP one and net group (regression #375)."""
        self.run_owtf(
            '-s',
            '-g', 'net',
            '%s://%s:%s' % (self.PROTOCOL, self.DOMAIN, self.PORT),
            '%s://%s:%s' % (self.PROTOCOL, self.IP, self.PORT))
        self.assert_is_in_logs('(net/', name='Worker')
        self.assert_is_not_in_logs('(web/', name='Worker')
        self.assert_is_not_in_logs('(aux/', name='Worker')
        self.assert_is_in_logs(
            "All jobs have been done. Exiting.",
            name='MainProcess',
            msg='OWTF did not finish properly!')
