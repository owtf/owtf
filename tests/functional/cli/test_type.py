"""
tests.functional.cli.test_type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from tests.owtftest import OWTFCliWebPluginTestCase


class OWTFCliTypeTest(OWTFCliWebPluginTestCase):
    """See https://github.com/owtf/owtf/issues/390 and https://github.com/owtf/owtf/pull/665"""

    categories = ["cli", "fast"]

    def test_cli_type_no_group_and_type_when_http_host(self):
        """Web group should be selected based on the host if http specified(regression #390)."""
        self.run_owtf(
            "-s", "-t", "active", "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT)
        )
        self.assert_is_in_logs(
            "(web/", name="Worker", msg="Web plugins should have been run!"
        )
        self.assert_is_not_in_logs(
            "(auxiliary/", name="Worker", msg="Aux plugins should not have been run!"
        )
        self.assert_is_not_in_logs(
            "(network/", name="Worker", msg="Net plugins should not have been run!"
        )
        # Test OWTF exited cleanly.
        self.assert_is_in_logs("All jobs have been done. Exiting.", name="MainProcess")

    def test_cli_type_no_group_and_type_when_host(self):
        """Net group should be selected based on the host (regression #390)."""
        self.run_owtf("-s", "-t", "active", "%s:%s" % (self.DOMAIN, self.PORT))
        self.assert_is_in_logs(
            "(network/", name="Worker", msg="Net plugins should have been run!"
        )
        self.assert_is_not_in_logs(
            "(web/", name="Worker", msg="Web plugins should not have been run!"
        )
        self.assert_is_not_in_logs(
            "(auxiliary/", name="Worker", msg="Aux plugins should not have been run!"
        )
        # Test OWTF exited cleanly.
        self.assert_is_in_logs("All jobs have been done. Exiting.", name="MainProcess")

    def test_cli_type_no_group_and_type_when_http_ip(self):
        """Web group should be selected based on the ip if http (regression #390)."""
        self.run_owtf(
            "-s", "-t", "active", "%s://%s:%s" % (self.PROTOCOL, self.IP, self.PORT)
        )
        self.assert_is_in_logs(
            "(web/", name="Worker", msg="Web plugins should have been run!"
        )
        self.assert_is_not_in_logs(
            "(network/", name="Worker", msg="Net plugins should not have been run!"
        )
        self.assert_is_not_in_logs(
            "(auxiliary/", name="Worker", msg="Aux plugins should not have been run!"
        )
        # Test OWTF exited cleanly.
        self.assert_is_in_logs("All jobs have been done. Exiting.", name="MainProcess")

    def test_cli_type_no_group_and_type_when_ip(self):
        """Net group should be selected based on the ip (regression #390)."""
        self.run_owtf("-s", "-t", "active", "%s:%s" % (self.IP, self.PORT))
        self.assert_is_in_logs(
            "(network/", name="Worker", msg="Net plugins should have been run!"
        )
        self.assert_is_not_in_logs(
            "(auxiliary/", name="Worker", msg="Aux plugins should not have been run!"
        )
        self.assert_is_not_in_logs(
            "(web/", name="Worker", msg="Web plugins should not have been run!"
        )
        # Test OWTF exited cleanly.
        self.assert_is_in_logs("All jobs have been done. Exiting.", name="MainProcess")
