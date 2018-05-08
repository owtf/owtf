"""
owtf.worker.local
~~~~~~~~~~~~~~~~~
"""
import logging
import sys
import traceback

try:
    import queue
except ImportError:
    import Queue as queue

from owtf.workers import BaseWorker
from owtf.lib.owtf_process import OWTFProcess
from owtf.models.error import Error
from owtf.managers.target import target_manager


class LocalWorker(OWTFProcess, BaseWorker):

    def initialize(self, **kwargs):
        super(LocalWorker, self).__init__(**kwargs)
        self.output_q = None
        self.input_q = None

    def pseudo_run(self):
        """ When run for the first time, put something into output queue ;)

        :return: None
        :rtype: None
        """
        self.output_q.put("Started")
        while self.poison_q.empty():
            try:
                work = self.input_q.get(True, 2)
                # If work is empty this means no work is there
                if work == ():
                    logging.info("No work")
                    sys.exit(0)
                target, plugin = work
                plugin_dir = self.plugin_handler.get_plugin_group_dir(plugin["group"])
                # Set the target specific thing here
                target_manager.set_target(target["id"])
                self.plugin_handler.process_plugin(session=self.session, plugin_dir=plugin_dir, plugin=plugin)
                self.output_q.put("done")
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                logging.debug("Worker (%d): Finished", self.pid)
                sys.exit(0)
            except Exception as e:
                e, ex, tb = sys.exc_info()
                trace = traceback.format_tb(tb)
                Error.add_error(
                    session=self.session,
                    message="Exception occurred while running plugin: {}, {}".format(str(e), str(ex)),
                    trace=trace,
                )
        logging.debug("Worker (%d): Exiting...", self.pid)
        sys.exit(0)
