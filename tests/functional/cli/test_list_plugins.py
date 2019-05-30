"""
tests.functional.cli.test_list_plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from tests.owtftest import OWTFCliTestCase


class OWTFCliListPluginsTest(OWTFCliTestCase):

    categories = ["cli"]

    def test_cli_list_plugins_aux(self):
        """Run OWTF to list the aux plugins."""
        expected = [
            "Available AUXILIARY plugins",
            "exploit",
            "smb",
            "bruteforce",
            "dos",
            "se",
            "rce",
            "selenium",
        ]

        self.run_owtf("-l", "auxiliary")
        self.assert_are_in_logs(expected, name="MainProcess")

    def test_cli_list_plugins_net(self):
        """Run OWTF to list the net plugins."""
        expected = ["Available NETWORK plugins", "active", "bruteforce"]

        self.run_owtf("-l", "network")
        self.assert_are_in_logs(expected, name="MainProcess")

    def test_cli_list_plugins_web(self):
        """Run OWTF to list the web plugins."""
        expected = [
            "Available WEB plugins",
            "external",
            "active",
            "passive",
            "grep",
            "semi_passive",
        ]

        self.run_owtf("-l", "web")
        self.assert_are_in_logs(expected, name="MainProcess")
