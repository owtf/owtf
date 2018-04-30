"""
owtf.shell.utils
~~~~~~~~~~~~~~~~
# Inspired from:
# http://code.activestate.com/recipes/440554-module-to-allow-asynchronous-subprocess-use-on-win/
"""

import errno
import os
import platform
import subprocess
import sys
import time

if platform.system() == "Windows":
    from win32file import ReadFile, WriteFile
    from win32pipe import PeekNamedPipe
    import msvcrt
else:
    import select
    import fcntl

PIPE = subprocess.PIPE
DISCONNECT_MESSAGE = "Other end disconnected!"


class DisconnectException(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class AsyncPopen(subprocess.Popen):

    def recv(self, maxsize=None):
        return self._recv("stdout", maxsize)

    def recv_err(self, maxsize=None):
        return self._recv("stderr", maxsize)

    def send_recv(self, input="", maxsize=None):
        return self.send(input), self.recv(maxsize), self.recv_err(maxsize)

    def get_conn_maxsize(self, which, maxsize):
        if maxsize is None:
            maxsize = 1024
        elif maxsize < 1:
            maxsize = 1
        return getattr(self, which), maxsize

    def _close(self, which):
        getattr(self, which).close()
        setattr(self, which, None)

    if hasattr(subprocess, "mswindows"):

        def send(self, input):
            if not self.stdin:
                return None
            try:
                x = msvcrt.get_osfhandle(self.stdin.fileno())
                (errCode, written) = WriteFile(x, input)
            except ValueError:
                return self._close("stdin")
            except (subprocess.pywintypes.error, Exception) as why:
                if why[0] in (109, errno.ESHUTDOWN):
                    return self._close("stdin")
                raise
            return written

        def _recv(self, which, maxsize):
            conn, maxsize = self.get_conn_maxsize(which, maxsize)
            if conn is None:
                return None
            try:
                x = msvcrt.get_osfhandle(conn.fileno())
                (read, navail, nMessage) = PeekNamedPipe(x, 0)
                if maxsize < navail:
                    nAvail = maxsize
                if navail > 0:
                    (errCode, read) = ReadFile(x, navail, None)
            except ValueError:
                return self._close(which)
            except (subprocess.pywintypes.error, Exception) as why:
                if why[0] in (109, errno.ESHUTDOWN):
                    return self._close(which)
                raise
            if self.universal_newlines:
                read = self._translate_newlines(read)
            return read

    else:

        def send(self, input):
            if not self.stdin:
                return None
            if not select.select([], [self.stdin], [], 0)[1]:
                return 0
            try:
                written = os.write(self.stdin.fileno(), input)
            except OSError as why:
                if why[0] == errno.EPIPE:  # broken pipe
                    return self._close("stdin")
                raise
            return written

        def _recv(self, which, maxsize):
            conn, maxsize = self.get_conn_maxsize(which, maxsize)
            if conn is None:
                return None
            flags = fcntl.fcntl(conn, fcntl.F_GETFL)
            if not conn.closed:
                fcntl.fcntl(conn, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            try:
                if not select.select([conn], [], [], 0)[0]:
                    return ""
                r = conn.read(maxsize)
                if not r:
                    return self._close(which)
                if self.universal_newlines:
                    r = self._translate_newlines(r)
                return r
            finally:
                if not conn.closed:
                    fcntl.fcntl(conn, fcntl.F_SETFL, flags)


def recv_some(p, t=.1, e=1, tr=5, stderr=0):
    if tr < 1:
        tr = 1
    x = time.time() + t
    y = []
    r = ""
    pr = p.recv
    if stderr:
        pr = p.recv_err
    while time.time() < x or r:
        r = pr()
        if r is None:
            if e:
                raise DisconnectException(DISCONNECT_MESSAGE)
            else:
                break
        elif r:
            y.append(r)
        else:
            time.sleep(max((x - time.time()) / tr, 0))
    return "".join(y)


def send_all(p, data):
    while len(data):
        sent = p.send(data)
        if sent is None:
            raise DisconnectException(DISCONNECT_MESSAGE)
        import sys

        if sys.version_info > (3,):
            buffer = memoryview
        data = buffer(data)


if __name__ == "__main__":
    if sys.platform == "win32":
        shell, commands, tail = ("cmd", ("dir /w", "echo HELLO WORLD"), "\r\n")
    else:
        shell, commands, tail = ("sh", ("ls", "echo HELLO WORLD"), "\n")

    a = AsyncPopen(shell, stdin=PIPE, stdout=PIPE)
    print(recv_some(a))
    for cmd in commands:
        send_all(a, cmd + tail)
        print(recv_some(a))
    send_all(a, "exit" + tail)
    print(recv_some(a, e=0))
    a.wait()
