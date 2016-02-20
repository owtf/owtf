from tests.testing_framework.base_test_cases import PluginTestCase
from hamcrest import *
from nose_parameterized.parameterized import parameterized


class NetPluginsTests(PluginTestCase):

    TYPE_ACTIVE = "active"
    TYPE_BRUTEFORCE = "bruteforce"
    METASPLOIT_BANNER_REGEX = "metasploit\sv\d+\.\d+\.\d-\d+\s\[core:\d\.\d\sapi:\d\.\d\]"

    @classmethod
    def setUpClass(cls):
        super(NetPluginsTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(NetPluginsTests, cls).tearDownClass()

    # Almost all network plugins are based on metasploit tools, so
    # instead of testing if the tools work, we test that they
    # are invoked from OWTF, and ensure that there isn't any
    # OWTF bug.
    # Some of the tests are affected by the bug #48, so they
    # are failing.
    @parameterized.expand([
        ("ftp", "FtpProbeMethods"),
        ("http-rpc-epmap", "HttpRpcProbeMethods"),
        ("msrpc", "MsRpcProbeMethods"),
        ("ms-sql", "MsSqlProbeMethods"),
        ("ppp", "EmcProbeMethods"),
      #  ("smb", "SmbProbeMethods"),  this is different
        ("smtp", "SmtpProbeMethods"),
        ("snmp", "SnmpProbeMethods"),
        ("vnc", "VncProbeMethods"),
        ("X11", "X11ProbeMethods")
    ])
    def test_net_active(self, plugin_name, resource_name):
        self._run_owtf_and_asserts_for_plugin(self.TYPE_ACTIVE,
                                              plugin_name,
                                              resource_name)

    def test_smb_active(self):
        self.owtf("-g network -t active -o smb")

        num_resources = self.get_number_of_resources("SmbProbeMethods")
        self.assert_external_tool_started(times=num_resources)
        self.assert_that_output_matches_more_than(self.METASPLOIT_BANNER_REGEX, times=3)
        self.assert_that_output_contains("samrdump.py")

    @parameterized.expand([
        ("ftp", "BruteFtpProbeMethods"),
        ("ms-sql", "BruteMsSqlProbeMethods"),
        ("smb", "BruteSmbProbeMethods"),
        ("snmp", "BruteSnmpProbeMethods"),
        ("vnc", "BruteVncProbeMethods")
    ])
    def test_net_bruteforce(self, plugin_name, resource_name):
        self._run_owtf_and_asserts_for_plugin(self.TYPE_BRUTEFORCE,
                                              plugin_name,
                                              resource_name)

    def _run_owtf_and_asserts_for_plugin(self, plugin_type, name, resource_name):
        # Runs the plugin and assert that Metasploit has been
        # called as many times as expected.
        self.owtf("-g network -t " + plugin_type + " -o " + name)

        num_resources = self.get_number_of_resources(resource_name)
        self.assert_external_tool_started(times=num_resources)
        self.assert_that_output_matches_more_than(self.METASPLOIT_BANNER_REGEX, num_resources)

    def get_number_of_resources(self, name):
        return len(self.get_resources(name))
