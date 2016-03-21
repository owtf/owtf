import mock

from owtf_testing.utils.owtftest import OWTFCliTestCase

from framework.dependency_management.dependency_resolver import ServiceLocator


class OWTFCliSimulationTest(OWTFCliTestCase):

    categories = ['cli', 'fast']

    def test_cli_simulation(self):
        """Run OWTF in simulation mode."""
        self.run_owtf('-s')
        self.assert_is_in_logs(
            'All jobs have been done. Exiting.',
            name='MainProcess',
            msg='OWTF did not finish properly!')
        plugin_handler = ServiceLocator.get_component("plugin_handler")
        self.assertTrue(
            plugin_handler.Simulation,
            msg='OWTF should have been run in simulation mode!')

    def test_cli_no_simualtion(self):
        """Run OWTF not in simulation mode."""
        self.run_owtf()
        self.assert_is_in_logs(
            'All jobs have been done. Exiting.',
            name='MainProcess',
            msg='OWTF did not finish properly!')
        plugin_handler = ServiceLocator.get_component("plugin_handler")
        self.assertFalse(
            plugin_handler.Simulation,
            msg='OWTF should not have been run in simulation mode!')
