import os
import logging
import errno
import signal

import psutil


def check_pid(pid):
    """Check whether pid exists in the current process table.
    UNIX only.

    :param pid: Pid to check
    :type pid: `int`
    :return: True if pid exists, else false
    :rtype: `bool`
    """
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


def kill_children(parent_pid, sig=signal.SIGINT):
    """Kill all OWTF child process when the SIGINT is received

    :param parent_pid: The pid of the parent OWTF process
    :type parent_pid: `int`
    :param sig: Signal received
    :type sig: `int`
    :return:
    :rtype: None
    """
    def on_terminate(proc):
        """Log debug info on child process termination

        :param proc: Process pid
        :rtype: None
        """
        logging.debug("Process {} terminated with exit code {}".format(
            proc, proc.returncode))

    parent = psutil.Process(parent_pid)
    children = parent.children(recursive=True)
    for child in children:
        child.send_signal(sig)

    _, alive = psutil.wait_procs(children, callback=on_terminate)
    if not alive:
        # send SIGKILL
        for pid in alive:
            logging.debug(
                "Process {} survived SIGTERM; trying SIGKILL" % pid)
            pid.kill()
    _, alive = psutil.wait_procs(alive, callback=on_terminate)
    if not alive:
        # give up
        for pid in alive:
            logging.debug("Process {} survived SIGKILL; giving up" % pid)
