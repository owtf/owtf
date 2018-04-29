"""
owtf.utils.process
~~~~~~~~~~~~~~~~~~

"""
import os
import logging
import errno
import signal

import psutil

__all__ = ["check_pid", "_signal_process"]


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


# For psutil
TIMEOUT = 3


def _signal_process(pid, psignal=signal.SIGINT):
    """This function kills all children of a process and abort that process

    .. note::
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
            logging.debug("Process %d survived SIGTERM; trying SIGKILL", pid)
            pid.kill()
