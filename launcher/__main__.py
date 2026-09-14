"""Run a command in a window of its own: ``python3 -m launcher <command>``.

This is the launcher process end to end — the thing WI-3 will point at the real
game. It takes a shell command, opens a window for it, waits for it to finish
and takes the window away again, and it prints what it did rather than leaving
anyone to guess.

The one thing it cannot check for you is caution C4: a command that never exits
leaves a window that cannot be closed without a modal sheet in front of a person
who did not ask for one. The launcher waits, gives up after its bound, and says
so — but it will not close a window with something still running in it.
"""

import sys

from launcher.desktop import Desktop
from launcher.lifecycle import LaunchFailed, WindowLauncher
from launcher.runner import OsascriptRunner


def main(argv=None, launcher=None, out=None, err=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    if not argv:
        err.write("usage: python3 -m launcher <command> [args ...]\n")
        return 2

    command = " ".join(argv)
    if launcher is None:
        launcher = WindowLauncher(Desktop(OsascriptRunner()))

    try:
        result = launcher.run(command)
    except LaunchFailed as failure:
        err.write("%s\n" % (failure,))
        return 1

    out.write("%s\n" % (result.reason,))
    return 0 if result.closed else 1


if __name__ == "__main__":
    sys.exit(main())
