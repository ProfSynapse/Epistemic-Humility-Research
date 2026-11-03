"""Linux exec boundary that kills the engine if its owning harness dies."""

import ctypes
import os
import signal
import sys


def main():
    if not sys.platform.startswith("linux"):
        raise RuntimeError("parent-death guarding requires the qualified Linux host")
    parent = int(sys.argv[1])
    command = sys.argv[3:]
    if sys.argv[2] != "--" or not command or parent <= 0:
        raise ValueError("expected parent PID followed by -- and an exec command")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:  # PR_SET_PDEATHSIG
        raise OSError(ctypes.get_errno(), "cannot install parent-death guard")
    # Close the race in which the parent exited before prctl was installed.
    if os.getppid() != parent:
        raise RuntimeError("owning harness exited before engine startup")
    os.execv(command[0], command)


if __name__ == "__main__":
    main()
