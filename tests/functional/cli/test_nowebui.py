"""
tests.functional.cli.test_nowebui
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from tests.owtftest import OWTFCliTestCase


class OWTFCliNoWebUITest(OWTFCliTestCase):

    categories = ["cli", "fast"]

    def test_cli_no_webui(self):
        """Run OWTF without its Web UI."""
        self.run_owtf()
        self.assert_has_not_been_logged(
            "Starting web server at http://127.0.0.1:8009",
            name="MainProcess",
            msg="The web UI should not have been run!",
        )
        self.assert_is_in_logs(
            "MainProcess: caught signal SIGINT, exiting",
            name="MainProcess",
            msg="OWTF did not finish properly!",
        )
