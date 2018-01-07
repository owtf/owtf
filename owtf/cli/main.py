try: #PY3
    import asyncio
except ImportError: #PY2
    import trollius as asyncio
    from trollius import From

from owtf.managers.worker import worker_manager


class CliServer(object):
    """
    The CliServer is created only when the user specifies that s-he doesn't
    want to use the WebUI.

    This can be specify with the '--nowebui' argument in the CLI.
    """
    def __init__(self):
        self.worker_manager = worker_manager
        self.task = asyncio.Task(self.worker_manager.manage_workers())
        self.manager_cron = asyncio.get_event_loop()
        self.manager_cron.call_later(2, self.clean_up)

    def start(self):
        try:
            self.manager_cron.run_until_complete(self.task)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            self.clean_up()

    def clean_up(self):
        """Properly stop any tornado callbacks."""
        self.manager_cron.cancel()


def start_cli():
    """This method starts the CLI server."""
    cli_server = CliServer()
    cli_server.start()
