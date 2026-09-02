"""
owtf.managers.worker
~~~~~~~~~~~~~~~~~~~~
Manage workers and assign work to them.
"""

import logging
import multiprocessing
import queue
import signal
from time import strftime

import psutil

from owtf.db.session import get_scoped_session
from owtf.lib.exceptions import InvalidWorkerReference
from owtf.managers.worklist import delete_work, get_pending_count, get_work_batch, get_work_for_target, requeue_work
from owtf.settings import (
    MIN_RAM_NEEDED,
    PROCESS_PER_CORE,
    WORKER_BATCH_SIZE,
    WORKER_HIGH_WATER,
    WORKER_LOW_WATER,
    WORKER_MAX_PROCESSES,
)
from owtf.utils.error import abort_framework
from owtf.utils.process import _signal_process, check_pid
from owtf.utils.signals import owtf_start, workers_finish
from owtf.workers.local import LocalWorker

__all__ = ["worker_manager"]

# For psutil
TIMEOUT = 3


class WorkerManager(object):
    def __init__(self):
        # Complicated stuff to keep everything Pythonic and from blowing up
        def handle_signal(sender, **kwargs):
            self.on_start(sender, **kwargs)

        self.handle_signal = handle_signal
        owtf_start.connect(handle_signal)
        self.worklist = []  # List of unprocessed (plugin*target)
        self.workers = []  # list of worker and work (worker, work)
        self.session = get_scoped_session()
        self.spawn_workers()

    def on_start(self, sender, **kwargs):
        self.keep_working = not kwargs["args"]["nowebui"]

    def get_allowed_process_count(self):
        """Get the number of max processes

        :return: max number of allowed processes
        :rtype: `int`
        """
        cpu_count = multiprocessing.cpu_count()
        return min(PROCESS_PER_CORE * cpu_count, WORKER_MAX_PROCESSES)

    def get_task(self):
        """Fetch task dict for worker

        :return: Work dict
        :rtype: `dict`
        """
        work = None
        avail = psutil.virtual_memory().available
        if int(avail / 1024 / 1024) > MIN_RAM_NEEDED:
            work = get_work_for_target(self.session, self.targets_in_use())
        else:
            logging.warning("Not enough memory to execute a plugin")
        return work

    def spawn_workers(self):
        """This function spawns the worker process and give them initial work

        :return: None
        :rtype: None
        """
        # Check if maximum limit of processes has reached
        max_workers = min(self.get_allowed_process_count(), WORKER_MAX_PROCESSES)
        while len(self.workers) < max_workers:
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
        w = LocalWorker(
            input_q=multiprocessing.Queue(),
            output_q=multiprocessing.Queue(),
            index=index,
        )
        worker_dict = {"worker": w, "work": (), "work_id": None, "busy": False, "paused": False}

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

    @staticmethod
    def _read_worker_result(worker):
        """Return the latest terminal event currently queued by a worker."""
        terminal_result = None
        while True:
            try:
                result = worker["worker"].output_q.get_nowait()
            except queue.Empty:
                break

            if result in ("done", "failed"):
                terminal_result = result
            elif result == "Started":
                continue
            else:
                logging.warning("Unknown worker result: %r", result)
                terminal_result = "failed"

        return terminal_result

    @staticmethod
    def _clear_worker_assignment(worker):
        worker["work"] = ()
        worker["work_id"] = None
        worker["busy"] = False
        worker["start_time"] = "NA"

    def _resolve_worker_work(self, worker, result=None, interrupted=False):
        """Finish completed attempts or reactivate interrupted work."""
        work_id = worker.get("work_id")
        if work_id is None:
            return

        if result in ("done", "failed"):
            delete_work(self.session, work_id)
        elif interrupted:
            requeue_work(self.session, work_id)
        else:
            return

        self._clear_worker_assignment(worker)

    def manage_workers(self):
        """This function manages workers, it polls on each queue of worker
        checks if it has done his work and then gives it new work
        if there is one

        :return: None
        :rtype: None
        """
        # --- Pass 1: resolve workers from the previous cycle ---
        for k, worker in enumerate(self.workers):
            if worker.get("drain"):
                continue  # handled in Pass 2

            result = self._read_worker_result(worker)

            if not check_pid(worker["worker"].pid):
                logging.info(
                    "Worker with name %s and pid %d seems dead",
                    worker["worker"].name,
                    worker["worker"].pid,
                )
                self._resolve_worker_work(
                    worker,
                    result=result,
                    interrupted=True,
                )
                self.spawn_worker(index=k)
                continue

            if result in ("done", "failed"):
                self._resolve_worker_work(worker, result=result)

        # --- Pass 2: remove workers already flagged to drain ---
        still_active = []
        for worker in self.workers:
            if worker.get("drain"):
                try:
                    _signal_process(worker["worker"].pid, signal.SIGTERM)
                    worker["worker"].poison_q.put("DIE")
                except Exception as e:
                    logging.warning("Failed to signal draining worker: %s", str(e))

                worker["worker"].join(timeout=5)
                if worker["worker"].is_alive():
                    logging.error("Worker %s did not terminate after SIGTERM; forcing kill", worker["worker"].name)
                    worker["worker"].terminate()
                    worker["worker"].join()

                result = self._read_worker_result(worker)
                self._resolve_worker_work(
                    worker,
                    result=result,
                    interrupted=result != "done",
                )
                continue

            still_active.append(worker)
        self.workers = still_active

        # --- Pass 3: scale, then fetch exactly as much work as can be assigned ---
        pending_count = get_pending_count(self.session)
        current_worker_count = len(self.workers)
        max_allowed_workers = self.get_allowed_process_count()

        if pending_count > WORKER_HIGH_WATER and current_worker_count < max_allowed_workers:
            logging.info("Pending work (%d) exceeds HIGH_WATER (%d), spawning worker", pending_count, WORKER_HIGH_WATER)
            self.spawn_worker()
        elif pending_count < WORKER_LOW_WATER and current_worker_count > 1:
            for worker in self.workers:
                if not worker["busy"]:
                    logging.info(
                        "Pending work (%d) below LOW_WATER (%d), draining worker %s",
                        pending_count,
                        WORKER_LOW_WATER,
                        worker["worker"].name,
                    )
                    worker["drain"] = True
                    break

        ready_workers = [w for w in self.workers if not w["busy"] and not w.get("drain")]
        work_batch = get_work_batch(self.session, self.targets_in_use(), len(ready_workers), WORKER_BATCH_SIZE)

        for worker, (work_id, target, plugin) in zip(ready_workers, work_batch):
            work_to_assign = (target, plugin)
            logging.info(
                "Work assigned to %s with pid %d",
                worker["worker"].name,
                worker["worker"].pid,
            )
            # Track ownership before enqueueing so an immediate worker exit
            # can be requeued on the next manager cycle.
            worker["work"] = work_to_assign
            worker["work_id"] = work_id
            worker["busy"] = True
            worker["start_time"] = strftime("%Y/%m/%d %H:%M:%S")
            try:
                worker["worker"].input_q.put(work_to_assign)
            except Exception:
                logging.exception(
                    "Unable to assign work_id %s to worker %s",
                    work_id,
                    worker["worker"].name,
                )
                requeue_work(self.session, work_id)
                self._clear_worker_assignment(worker)

        if not self.keep_working and not self.is_any_worker_busy():
            logging.info("All jobs have been done. Exiting.")
            workers_finish.send(self)

    def is_any_worker_busy(self):
        """If a worker is still busy, return True. Return False otherwise.

        :return: True if any worker is busy
        :return: `bool`
        """
        return True in [worker["busy"] for worker in self.workers]

    def poison_pill_to_workers(self):
        """This function waits for each worker to complete his work and
        send it poison pill (empty work)

        :return: None
        :rtype: None
        """
        for item in self.workers[:]:
            if item.get("drain"):
                try:
                    _signal_process(item["worker"].pid, signal.SIGTERM)
                    item["worker"].poison_q.put("DIE")
                except Exception as e:
                    logging.warning("Failed to terminate draining worker: %s", str(e))
                continue
            # Check if process is doing some work
            if item["busy"]:
                if item["paused"]:
                    _signal_process(item["worker"].pid, signal.SIGCONT)
                result = item["worker"].output_q.get()
                self._resolve_worker_work(item, result=result)

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
            item["worker"].poison_q.put("DIE")
            _signal_process(item["worker"].pid, signal.SIGINT)

    @staticmethod
    def _signal_children(parent_pid, psignal):
        """Signal OWTF child processes

        :param parent_pid: Parent process PID
        :type parent_pid: `int`
        :param psignal: Signal to send
        :type parent_pid: `int`
        :return: None
        :rtype: None
        """

        def on_terminate(proc):
            logging.debug("Process %s terminated with exit code %d", proc, proc.returncode)

        parent = psutil.Process(parent_pid)
        children = parent.children(recursive=True)
        for child in children:
            child.send_signal(psignal)

        gone, alive = psutil.wait_procs(children, timeout=TIMEOUT, callback=on_terminate)
        if not alive:
            # send SIGKILL
            for pid in alive:
                logging.debug("Process %d survived SIGTERM; trying SIGKILL", pid)
                pid.kill()
        gone, alive = psutil.wait_procs(alive, timeout=TIMEOUT, callback=on_terminate)
        if not alive:
            # give up
            for pid in alive:
                logging.debug("Process %d survived SIGKILL; giving up", pid)

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
                raise InvalidWorkerReference("No worker process with id: {!s}".format(pseudo_index))
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
            raise InvalidWorkerReference("No worker process with id: {!s}".format(pseudo_index))

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
            _signal_process(worker_dict["worker"].pid, signal.SIGINT)
            del self.workers[pseudo_index - 1]
        else:
            raise InvalidWorkerReference("Worker with id {!s} is busy".format(pseudo_index))

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
            _signal_process(worker_dict["worker"].pid, signal.SIGSTOP)
            worker_dict["paused"] = True

    def pause_all_workers(self):
        """Pause all workers by sending SIGSTOP after verifying they are running

        :return: None
        :rtype: None
        """
        for worker_dict in self.workers:
            if not worker_dict["paused"]:
                self._signal_children(worker_dict["worker"].pid, signal.SIGSTOP)
                _signal_process(worker_dict["worker"].pid, signal.SIGSTOP)
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
            _signal_process(worker_dict["worker"].pid, signal.SIGCONT)
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
                _signal_process(worker_dict["worker"].pid, signal.SIGCONT)
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
        _signal_process(worker_dict["worker"].pid, signal.SIGINT)


worker_manager = WorkerManager()
