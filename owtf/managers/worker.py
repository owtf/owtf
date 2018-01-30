"""
owtf.db.worker_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging
import multiprocessing
import os
import signal
import sys
import traceback
try:
    import queue
except ImportError:
    import Queue as queue
from time import strftime

import psutil

from owtf.managers.worklist import get_work_for_target
from owtf.settings import PROCESS_PER_CORE, MIN_RAM_NEEDED, CLI
from owtf.lib.owtf_process import OWTFProcess
from owtf.lib.exceptions import InvalidWorkerReference
from owtf.utils.process import check_pid
from owtf.utils.error import abort_framework
from owtf.managers.error import add_error
from owtf.plugin.plugin_handler import plugin_handler
from owtf.db.database import get_scoped_session


# For psutil
TIMEOUT = 3


class Worker(OWTFProcess):
    def pseudo_run(self):
        """ When run for the first time, put something into output queue ;)

        :return: None
        :rtype: None
        """
        self.output_q.put('Started')
        while self.poison_q.empty():
            try:
                work = self.input_q.get(True, 2)
                # If work is empty this means no work is there
                if work == ():
                    print("No work")
                    sys.exit(0)
                target, plugin = work
                plugin_dir = plugin_handler.get_plugin_group_dir(plugin['group'])
                plugin_handler.switch_to_target(target["id"])
                plugin_handler.process_plugin(session=self.session, plugin_dir=plugin_dir, plugin=plugin)
                self.output_q.put('done')
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                logging.debug("Worker (%d): Finished", self.pid)
                sys.exit(0)
            except Exception as e:
                e, ex, tb = sys.exc_info()
                add_error(self.session, "Exception occurred while running plugin: {}, {}".format(str(e), str(ex)),
                          str(traceback.format_tb(tb, 4096)))
        logging.debug("Worker (%d): Exiting...", self.pid)
        sys.exit(0)


class WorkerManager(object):

    def __init__(self, keep_working=True):
        self.keep_working = keep_working
        self.worklist = []  # List of unprocessed (plugin*target)
        self.workers = []  # list of worker and work (worker, work)
        self.session = get_scoped_session()
        self.spawn_workers()

    def get_allowed_process_count(self):
        """Get the number of max processes

        :return: max number of allowed processes
        :rtype: `int`
        """
        cpu_count = multiprocessing.cpu_count()
        return PROCESS_PER_CORE * cpu_count

    def get_task(self):
        """Fetch task dict for worker

        :return: Work dict
        :rtype: `dict`
        """
        work = None
        avail = psutil.virtual_memory().available
        if int(avail/1024/1024) > MIN_RAM_NEEDED:
            work = get_work_for_target(self.session, self.targets_in_use())
        else:
            logging.warn("Not enough memory to execute a plugin")
        return work

    def spawn_workers(self):
        """This function spawns the worker process and give them initial work

        :return: None
        :rtype: None
        """
        # Check if maximum limit of processes has reached
        while (len(self.workers) < self.get_allowed_process_count()):
            self.spawn_worker()
        if not len(self.workers):
            abort_framework("Zero worker processes created because of lack of memory")

    def spawn_worker(self, index=None):
        """Spawn a new worker

        :param index: Worker index
        :type index: `int`
        :return: None
        :rtype: None
        """
        w = Worker(input_q=multiprocessing.Queue(), output_q=multiprocessing.Queue(), index=index)
        worker_dict = {"worker": w, "work": (), "busy": False, "paused": False}

        if index is not None:
            logging.debug("Replacing worker at index %d", index)
            self.workers[index] = worker_dict
        else:
            logging.debug("Adding a new worker")
            self.workers.append(worker_dict)
        w.start()

    def targets_in_use(self):
        target_ids = []
        for item in self.workers:
            try:
                target_ids.append(item["work"][0]["id"])
            except IndexError:
                continue
        return target_ids

    def manage_workers(self):
        """This function manages workers, it polls on each queue of worker
        checks if it has done his work and then gives it new work
        if there is one

        :return: None
        :rtype: None
        """
        # Loop while there is some work in worklist
        for k in range(0, len(self.workers)):
            if (not self.workers[k]["worker"].output_q.empty()) or (not check_pid(self.workers[k]["worker"].pid)):
                if check_pid(self.workers[k]["worker"].pid):
                    # Assign target, plugin from tuple work and empty the tuple
                    self.workers[k]["work"] = ()
                    self.workers[k]["busy"] = False  # Worker is IDLE
                    self.workers[k]["start_time"] = "NA"
                else:
                    logging.info("Worker with name %s and pid %s seems dead" % (self.workers[k]["worker"].name,
                                                                                self.workers[k]["worker"].pid))
                    self.spawn_worker(index=k)
                work_to_assign = self.get_task()
                if work_to_assign:
                    logging.info("Work assigned to %s with pid %d" % (self.workers[k]["worker"].name,
                                                                      self.workers[k]["worker"].pid))
                    trash_can = self.workers[k]["worker"].output_q.get()
                    # Assign work ,set target to used,and process to busy
                    self.workers[k]["worker"].input_q.put(work_to_assign)
                    self.workers[k]["work"] = work_to_assign
                    self.workers[k]["busy"] = True
                    self.workers[k]["start_time"] = strftime("%Y/%m/%d %H:%M:%S")
                if not self.keep_working:
                    if not self.is_any_worker_busy():
                        logging.info("All jobs have been done. Exiting.")
                        sys.exit(0)

    def is_any_worker_busy(self):
        """If a worker is still busy, return True. Return False otherwise.

        :return: True if any worker is busy
        :return: `bool`
        """
        return True in [worker['busy'] for worker in self.workers]

    def poison_pill_to_workers(self):
        """This function waits for each worker to complete his work and
        send it poison pill (empty work)

        :return: None
        :rtype: None
        """
        for item in self.workers:
            # Check if process is doing some work
            if item["busy"]:
                if item["paused"]:
                    self._signal_process(item["worker"].pid, signal.SIGCONT)
                trash = item["worker"].output_q.get()
                item["busy"] = False
                item["work"] = ()
            item["worker"].poison_q.put("DIE")

    def join_workers(self):
        """Joins all the workers

        :return: None
        :rtype: None
        """
        for item in self.workers:
            item["worker"].join()

    def clean_up(self):
        """Cleanup workers

        :return: None
        :rtype: None
        """
        self.poison_pill_to_workers()
        self.join_workers()

    def exit(self):
        """This function empties the pending work list and aborts all processes

        :return: None
        :rtype: None
        """
        # As worklist is emptied, aborting of plugins will result in
        # killing of workers
        self.worklist = []  # It is a list
        for item in self.workers:
            work = item["worker"].poison_q.put("DIE")
            self._signal_process(item["worker"].pid, signal.SIGINT)

    def _signal_process(self, pid, psignal):
        """This function kills all children of a process and abort that process

        .note::
            Child processes are handled at shell level

        :param pid: Pid of the process
        :type pid: `int`
        :param psignal: Signal to send
        :type pid: `int`
        :return: None
        :rtype: None
        """
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        children.append(parent)
        for pid in children:
            pid.send_signal(psignal)
        gone, alive = psutil.wait_procs(children, timeout=TIMEOUT)
        if not alive:
            # send SIGKILL
            for pid in alive:
                logging.debug("Process {} survived SIGTERM; trying SIGKILL" % pid)
                pid.kill()

    def _signal_children(self, parent_pid, psignal):
        """Signal OWTF child processes

        :param parent_pid: Parent process PID
        :type parent_pid: `int`
        :param psignal: Signal to send
        :type parent_pid: `int`
        :return: None
        :rtype: None
        """

        def on_terminate(proc):
            logging.debug("Process {} terminated with exit code {}".format(proc, proc.returncode))

        parent = psutil.Process(parent_pid)
        children = parent.children(recursive=True)
        for child in children:
            child.send_signal(psignal)

        gone, alive = psutil.wait_procs(children, timeout=TIMEOUT, callback=on_terminate)
        if not alive:
            # send SIGKILL
            for pid in alive:
                logging.debug("Process {} survived SIGTERM; trying SIGKILL".format(pid))
                pid.kill()
        gone, alive = psutil.wait_procs(alive, timeout=TIMEOUT, callback=on_terminate)
        if not alive:
            # give up
            for pid in alive:
                logging.debug("Process {} survived SIGKILL; giving up".format(pid))

    # NOTE: PSEUDO_INDEX = INDEX + 1
    # This is because the list index starts from 0 and in the UI, indices start from 1
    def get_worker_details(self, pseudo_index=None):
        """Get worker details

        :param pseudo_index: worker index
        :type pseudo_index: `int`
        :return: Worker details
        :rtype: `dict`
        """
        if pseudo_index:
            try:
                temp_dict = dict(self.workers[pseudo_index - 1])
                temp_dict["name"] = temp_dict["worker"].name
                temp_dict["worker"] = temp_dict["worker"].pid
                temp_dict["id"] = pseudo_index
                return temp_dict
            except IndexError:
                raise InvalidWorkerReference("No worker process with id: %s" % str(pseudo_index))
        else:
            worker_temp_list = []
            for i, obj in enumerate(self.workers):
                temp_dict = dict(self.workers[i])
                temp_dict["name"] = temp_dict["worker"].name
                temp_dict["worker"] = temp_dict["worker"].pid
                temp_dict["id"] = i + 1  # Zero-Index is not human friendly
                worker_temp_list.append(temp_dict)
            return worker_temp_list

    def get_busy_workers(self):
        """Returns number of busy workers

        :return: Number of busy workers
        :rtype: `int`
        """
        count = 0
        workers = self.get_worker_details()
        for worker in workers:
            if worker["busy"] is True:
                count += 1

        return count

    def get_worker_dict(self, pseudo_index):
        """Fetch the worker dict from the list

        :param pseudo_index: worker index
        :type pseudo_index: `int`
        :return: Worker info
        :rtype: `dict`
        """
        try:
            return self.workers[pseudo_index - 1]
        except IndexError:
            raise InvalidWorkerReference("No worker process with id: %s" % str(pseudo_index))

    def create_worker(self):
        """Create new worker

        :return: None
        :rtype: None
        """
        self.spawn_worker()

    def delete_worker(self, pseudo_index):
        """
        This actually deletes the worker :
        + Send SIGINT to the worker
        + Remove it from self.workers so that is is not restarted by
          manager cron
        """
        worker_dict = self.get_worker_dict(pseudo_index)
        if not worker_dict["busy"]:
            self._signal_process(worker_dict["worker"].pid, signal.SIGINT)
            del self.workers[pseudo_index - 1]
        else:
            raise InvalidWorkerReference("Worker with id %s is busy" % str(pseudo_index))

    def pause_worker(self, pseudo_index):
        """Pause worker by sending SIGSTOP after verifying the process is running

        :param pseudo_index: worker index
        :type pseudo_index: `int`
        :return: None
        :rtype: None
        """
        worker_dict = self.get_worker_dict(pseudo_index)
        if not worker_dict["paused"]:
            self._signal_children(worker_dict["worker"].pid, signal.SIGSTOP)
            self._signal_process(worker_dict["worker"].pid, signal.SIGSTOP)
            worker_dict["paused"] = True

    def pause_all_workers(self):
        """Pause all workers by sending SIGSTOP after verifying they are running

        :return: None
        :rtype: None
        """
        for worker_dict in self.workers:
            if not worker_dict["paused"]:
                self._signal_children(worker_dict["worker"].pid, signal.SIGSTOP)
                self._signal_process(worker_dict["worker"].pid, signal.SIGSTOP)
                worker_dict["paused"] = True

    def resume_worker(self, pseudo_index):
        """Resume worker by sending SIGCONT after verifying that process is paused

        :param pseudo_index: Worker index
        :type pseudo_index: `int`
        :return: None
        :rtype: None
        """
        worker_dict = self.get_worker_dict(pseudo_index)
        if worker_dict["paused"]:
            self._signal_children(worker_dict["worker"].pid, signal.SIGCONT)
            self._signal_process(worker_dict["worker"].pid, signal.SIGCONT)
            worker_dict["paused"] = False

    def resume_all_workers(self):
        """Resume all workers by sending SIGCONT to each one of them after verification
        that it is really paused

        :return: None
        :rtype: None
        """
        for worker_dict in self.workers:
            if worker_dict["paused"]:
                self._signal_children(worker_dict["worker"].pid, signal.SIGCONT)
                self._signal_process(worker_dict["worker"].pid, signal.SIGCONT)
                worker_dict["paused"] = False

    def abort_worker(self, pseudo_index):
        """Abort worker i.e kill current command, but the worker process is not
        removed, so manager_cron will restart it

        :param pseudo_index: pseudo index for the worker
        :type pseudo_index: `int`
        :return: None
        :rtype: None
        """
        worker_dict = self.get_worker_dict(pseudo_index)
        # You only send SIGINT to worker since it will handle it more
        # gracefully and kick the command process's ***
        self._signal_process(worker_dict["worker"].pid, signal.SIGINT)


worker_manager = WorkerManager(keep_working=not os.environ.get('CLI', CLI))
