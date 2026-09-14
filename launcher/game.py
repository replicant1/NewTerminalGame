"""The end-to-end join: what the launcher actually runs in the window it owns.

WI-1 built a launcher that can open a window for *any* command and take it back
again. WI-2 built a game process that draws a frame and exits on ``q``. This
module is the seam between them, and it is deliberately nothing more than that:
the shell command that starts the real game, as text.

Run it with::

    python3 -m launcher.game

**This module must not import the game.** Implementation plan §3: "The Launcher
process shares no code with the game's Domain, Presentation or Application."
The game is named here as the string :data:`GAME_MODULE` and started as a
subprocess in a window — never imported, never called. That is why the constant
below is a string rather than an import, and there is a test that says so.

Three things the command has to get right, none of them obvious:

* **The window is not yet the right size when the game starts looking.**
  ``do script`` starts the command at the moment the window is created, and the
  launcher's ``configure`` — the call that makes the window 40 x 30 — only runs
  *after* that call returns. A new Terminal window opens at the player's profile
  default, which on an untouched profile is 80 x 24, and 24 is less than the 30
  rows the game requires. The game checks its size once, at curses start-up, and
  fails loudly below 40 x 30, which is correct behaviour that this join must not
  provoke by accident. Measured on this machine: ``configure`` completed 0.496 s
  before the launched process could first look at the terminal, so the race is
  currently won — but it is won by login-shell start-up latency, which is an
  accident of this machine's profile and not something to build on. The gate
  below waits for the size the launcher asked for, and is bounded, and always
  falls through: on a screen that really is too small the game still gets to
  fail loudly. See ``docs/findings/WI-3-configure-startup-race.md``.

* **The game is not on the module path.** The window runs a fresh login shell
  whose working directory is the player's home, so ``python3 -m
  terminalgame.game_main`` would not find the game. The command changes to the
  repository root first.

* **``exec`` has to survive all of it.** ``script.open_window_running`` prefixes
  ``exec`` so that the login shell is *replaced* by the command rather than
  sitting alive underneath it — that is what lets the tab report itself idle the
  moment the game exits, which is the whole basis on which the launcher decides
  it is safe to close the window (caution C2). A gate written as a plain prefix
  would break that chain, so the gate and the game go into one ``/bin/sh -c``
  which ``exec``s the game in turn. The shell is replaced at every step and
  nothing is left alive behind the game.
"""

import argparse
import os
import shlex
import sys

from launcher import script
from launcher.desktop import Desktop
from launcher.lifecycle import LaunchFailed, WindowLauncher
from launcher.runner import OsascriptRunner

#: The game process, named as text. See the module docstring: the launcher may
#: not import the game, so this is a string and stays a string.
GAME_MODULE = "terminalgame.game_main"

#: The repository root — the directory holding both ``launcher`` and the game's
#: package, and therefore the directory the game has to be started from.
REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Seconds the M0 skeleton holds its frame before exiting on its own if nobody
#: presses anything.
#:
#: The game's own default is 3 seconds and the launcher could simply inherit it,
#: but the lifetime of a window on the player's desktop is a decision this join
#: ought to be making out loud rather than picking up by accident, so it is
#: named here and always passed explicitly. Five seconds because a person who is
#: watching needs long enough to actually read the frame and press ``q`` — which
#: is the path WIN-5 and END-6 are about — while an unattended run still ends
#: promptly. It is scaffolding either way: WI-11 replaces the skeleton with the
#: real loop, which ends when the player ends it and not on a timer.
DEFAULT_HOLD_SECONDS = 5.0

#: How long the gate will wait for the window to reach the size the launcher
#: asked for: attempts x interval, so 6 seconds. Bounded, and it falls through
#: rather than giving up, so the game always gets to run and always gets to
#: report a genuinely too-small screen itself.
GATE_ATTEMPTS = 60
GATE_INTERVAL = 0.1



def size_gate(columns=script.COLUMNS, rows=script.ROWS,
              attempts=GATE_ATTEMPTS, interval=GATE_INTERVAL):
    """A bounded ``sh`` loop that waits for the terminal to reach ``columns`` x
    ``rows``, as one line.

    One line because the command is embedded in an AppleScript string literal
    and :func:`launcher.script.applescript_string` refuses control characters —
    a newline in there would be a second command typed into the player's shell.

    ``stty size`` reports ``rows columns`` in that order, and reads them from
    the terminal itself rather than from terminfo, so it needs no ``TERM``. If
    it fails, ``set --`` leaves the positional parameters empty and ``${1:-0}``
    makes that a zero, which simply fails the comparison and costs one more
    turn round a loop that is bounded anyway.
    """
    return (
        "i=0; "
        "while [ $i -lt %(attempts)d ]; do "
        "set -- $(stty size 2>/dev/null); "
        "if [ ${1:-0} -ge %(rows)d ] && [ ${2:-0} -ge %(columns)d ]; "
        "then break; fi; "
        "i=$((i+1)); "
        "sleep %(interval)s; "
        "done"
        % {
            "attempts": int(attempts),
            "rows": int(rows),
            "columns": int(columns),
            "interval": _seconds(interval),
        }
    )


def game_command(repository_root=None, python_executable=None,
                 hold_seconds=DEFAULT_HOLD_SECONDS,
                 columns=script.COLUMNS, rows=script.ROWS,
                 attempts=GATE_ATTEMPTS, interval=GATE_INTERVAL):
    """The one-line shell command that runs the real game in its own window.

    Everything the window will do is in this string, and it is a return value
    rather than a side effect, so a test can read the whole of it. That is the
    same reasoning WI-1 used for the AppleScript itself (plan §11.6): the
    dangerous facts here are *which module is started*, *whether it is bounded*
    and *whether ``exec`` survives*, and all three are facts about the text.
    """
    root = REPOSITORY_ROOT if repository_root is None else repository_root
    python = sys.executable if python_executable is None else python_executable
    inner = "; ".join([
        size_gate(columns, rows, attempts, interval),
        "cd %s || exit 1" % (shlex.quote(root),),
        "exec %s -m %s --hold %s" % (
            shlex.quote(python), GAME_MODULE, _seconds(hold_seconds),
        ),
    ])
    return "/bin/sh -c %s" % (shlex.quote(inner),)


def play(launcher, command):
    """One whole session: open the window, let the game be played, take it back.

    This is :meth:`WindowLauncher.run` with one difference, and the difference
    is the whole of WI-3's risk. ``run`` decides the game has finished by asking
    the tab whether it is ``busy``, and **that flag is false for the entire life
    of a game in a window that has been given its 40 x 30 grid** — measured, the
    game alive from +0.9 s to +8.4 s with ``busy`` false from +0.9 s onwards. So
    ``run`` closes the window while the player is still playing.

    Asking instead what processes the tab is running gives the true answer, and
    an empty list is an unambiguous "nothing is running in there" that needs no
    matching of names. It also covers the start-up gap for free: a window whose
    login shell is still starting lists that shell, so it is never mistaken for
    a window whose game has ended.
    """
    window = launcher.open(command)
    return launcher.reap(
        window.window_id,
        launcher.session_timeout,
        still_running=launcher.has_live_processes,
    )


def main(argv=None, launcher=None, out=None, err=None):
    """``python3 -m launcher.game`` — open a window, play, take the window back.

    The exit codes are WI-1's: zero when the window was closed, one when it was
    left open or the launch failed, and in the latter case the window id named
    so a human can deal with what the launcher would not.
    """
    arguments = _parse_arguments(argv)
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    if launcher is None:
        launcher = WindowLauncher(Desktop(OsascriptRunner()))

    command = game_command(hold_seconds=arguments.hold)
    try:
        result = play(launcher, command)
    except LaunchFailed as failure:
        err.write("%s\n" % (failure,))
        return 1

    out.write("%s\n" % (result.reason,))
    return 0 if result.closed else 1


def _parse_arguments(argv):
    parser = argparse.ArgumentParser(
        prog="launcher.game",
        description="Open a terminal window and run the game in it.")
    parser.add_argument(
        "--hold", type=float, default=DEFAULT_HOLD_SECONDS,
        help="seconds the frame stays up if nobody presses q "
             "(default: %(default)s). Never unbounded.")
    arguments = parser.parse_args(argv)
    if arguments.hold < 0:
        parser.error("--hold cannot be negative")
    return arguments


def _seconds(value):
    """Format a number of seconds for a shell command line.

    Plainly, so the command a person reads in a log says ``5`` and ``0.1``
    rather than ``5.0`` and ``0.1000000000000000055``.
    """
    number = float(value)
    if number == int(number):
        return str(int(number))
    return repr(round(number, 3))


if __name__ == "__main__":
    sys.exit(main())
