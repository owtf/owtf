import tornado
import tornado.ioloop

from owtf.managers.worker import worker_manager


class CliServer(object):
    """
    The CliServer is created only when the user specifies that s-he doesn't
    want to use the WebUI.

    This can be specify with the '--nowebui' argument in the CLI.
    """
    def __init__(self):
        self.worker_manager = worker_manager
        self.manager_cron = tornado.ioloop.PeriodicCallback(self.worker_manager.manage_workers, 2000)

    def start(self):
        try:
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass

    def clean_up(self):
        """Properly stop any tornado callbacks."""
        self.manager_cron.stop()


def start_cli():
    """This method starts the CLI server."""
    cli_server = CliServer()
    cli_server.start()
