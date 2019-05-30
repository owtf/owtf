"""
tests.functional.cli.test_empty_run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from tests.owtftest import OWTFCliTestCase


class OWTFCliEmptyRunTest(OWTFCliTestCase):

    categories = ["cli", "fast"]

    def test_cli_empty_run(self):
        """Run OWTF without parameters."""
        self.run_owtf()
        self.assert_is_in_logs(
            "MainProcess: caught signal SIGINT, exiting",
            name="MainProcess",
            msg="OWTF did not finish properly!",
        )
