from framework.dependency_management.dependency_resolver import BaseComponent
import tornado.ioloop


class CliServer(BaseComponent):

    """
    The CliServer is created only when the user specifies that s-he doesn't
    want to use the WebUI.

    This can be specify with the '--nowebui' argument in the CLI.
    """

    COMPONENT_NAME = "cli_server"

    def __init__(self):
        self.register_in_service_locator()
        self.worker_manager = self.get_component("worker_manager")
        self.manager_cron = tornado.ioloop.PeriodicCallback(
            self.worker_manager.manage_workers,
            2000)

    def start(self):
        try:
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass

    def clean_up(self):
        """Properly stop any tornado callbacks."""
        self.manager_cron.stop()
