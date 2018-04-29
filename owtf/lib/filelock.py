"""
owtf.lib.filelock
~~~~~~~~~~~~~~~~~

Implementation of a simple cross-platform file locking mechanism.
This is a modified version of code retrieved on 2013-01-01 from
http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python.
The original code was released under the BSD License, as is this modified version.
Modifications in this version:

 - Tweak docstrings for sphinx.
 - Accept an absolute path for the protected file (instead of a file name relative to cwd).
 - Allow timeout to be None.
 - Fixed a bug that caused the original code to be NON-threadsafe when the same FileLock instance was
   shared by multiple threads in one process.
   (The original was safe for multiple processes, but not multiple threads in a single process.
   This version is safe for both cases.)
 - Added ``purge()`` function.
 - Added ``available()`` function.
 - Expanded API to mimic ``threading.Lock interface``:
   - ``__enter__`` always calls ``acquire()``, and therefore blocks if ``acquire()`` was called previously.
   - ``__exit__`` always calls ``release()``.  It is therefore a bug to call ``release()`` from within a
   context manager.
   - Added ``locked()`` function.
   - Added blocking parameter to ``acquire()`` method

# taken from https://github.com/ilastik/lazyflow/blob/master/lazyflow/utility/fileLock.py
# original version from http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/
"""
import errno
import os
import sys
import time

__all__ = ["FileLock"]


class FileLock(object):
    """ A file locking mechanism that has context-manager support so
        you can use it in a ``with`` statement. This should be relatively cross
        compatible as it doesn't rely on ``msvcrt`` or ``fcntl`` for the locking.
    """

    class FileLockException(Exception):
        pass

    def __init__(self, protected_file_path, timeout=None, delay=1, lock_file_contents=None):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.is_locked = False
        self.lockfile = protected_file_path + ".lock"
        self.timeout = timeout
        self.delay = delay
        self._lock_file_contents = lock_file_contents
        if self._lock_file_contents is None:
            self._lock_file_contents = "Owning process args:\n"
            for arg in sys.argv:
                self._lock_file_contents += arg + "\n"

    def locked(self):
        """Returns True iff the file is owned by THIS FileLock instance.
        (Even if this returns false, the file could be owned by another FileLock instance,
        possibly in a different thread or process).

        :return: True if file owned by Filelock instance
        :rtype: `bool`
        """
        return self.is_locked

    def available(self):
        """Returns True iff the file is currently available to be locked.

        :return: True if lockfile is available
        :rtype: `bool`
        """
        return not os.path.exists(self.lockfile)

    def acquire(self, blocking=True):
        """Acquire the lock, if possible. If the lock is in use, and `blocking` is False, return False.
            Otherwise, check again every `self.delay` seconds until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it raises an exception.

        :param blocking: File blocked or not
        :type blocking: `bool`
        :return: True if lock is acquired, else False
        :rtype: `bool`
        """

        start_time = time.time()
        while True:
            try:
                # Attempt to create the lockfile.
                # These flags cause os.open to raise an OSError if the file already exists.
                fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                with os.fdopen(fd, "a") as f:
                    # Print some info about the current process as debug info for anyone who bothers to look.
                    f.write(self._lock_file_contents)
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if self.timeout is not None and (time.time() - start_time) >= self.timeout:
                    raise FileLock.FileLockException("Timeout occurred for lock '{!s}'.".format(self.lockfile))
                if not blocking:
                    return False
                time.sleep(self.delay)
        self.is_locked = True
        return True

    def release(self):
        """Get rid of the lock by deleting the lockfile.
            When working in a `with` statement, this gets automatically
            called at the end.

        :return: None
        :rtype: None
        """
        self.is_locked = False
        os.unlink(self.lockfile)

    def __enter__(self):
        """ Activated when used in the with statement.
            Should automatically acquire a lock to be used in the with block.
        """
        self.acquire()
        return self

    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        self.release()

    def __del__(self):
        """ Make sure this ``FileLock`` instance doesn't leave a .lock file
            lying around.
        """
        if self.is_locked:
            self.release()

    def purge(self):
        """
        For debug purposes only.  Removes the lock file from the hard disk.
        """
        if os.path.exists(self.lockfile):
            self.release()
            return True
        return False
