"""``python3 -m auto_smoketest`` — run the exercises against the real desktop.

One window is opened and taken back again. Unlike the register in
``manual_smoketest``, this one really does something to the machine it is run
on, which is why it is a separate command rather than a flag: nobody should
reach the desktop by leaving an argument off.
"""

from __future__ import annotations

import argparse
import sys
import time

from launcher.game import game_command
from manual_smoketest import checks
from auto_smoketest import pack

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_LEFT_A_WINDOW = 2


def main(argv=None, runner=None, clock=time.time, sleeper=time.sleep):
    """Open one window, run the game in it, report, and take the window back.

    `runner`, `clock` and `sleeper` are injectable for the same reason they
    are in `launcher.game.main`: without a seam here, nothing can exercise
    this function except a real desktop, and so nothing did — every line of
    it was unreached by the suite. They are not for callers to vary.
    """
    parser = argparse.ArgumentParser(
        prog="python3 -m auto_smoketest",
        description="Open one window, run the real game in it, and take the "
                    "window back. Reports what it observed.")
    parser.add_argument("--show-picture", action="store_true",
                        help="print what the tab was showing")
    arguments = parser.parse_args(argv)

    print("THE EXERCISES")
    print("=" * 70)
    print("Opening one window. It will end itself with `q` — this never uses")
    print("a hold and never starts a game it cannot stop.")
    print("")
    observations, shown, window = pack.run(
        game_command(), runner=runner, clock=clock, sleeper=sleeper)
    for observation in observations:
        print(observation)
    print("")
    print("what the window did, by the clock:")
    for when, what in window.events:
        print("   %6.2fs  %s" % (when, what))

    if arguments.show_picture and shown:
        print("")
        print("what the tab was showing:")
        for row in shown.splitlines():
            print("   |%s|" % row)

    print("")
    print("-" * 70)
    failed = [o for o in observations if o.ok is False]
    noted = [o for o in observations if o.ok is None]
    print("%d exercises: %d ok, %d failed, %d observed for a person to judge"
          % (len(observations), len(observations) - len(failed) - len(noted),
             len(failed), len(noted)))
    if window.abandoned is not None:
        print("")
        print("*** WINDOW %d WAS LEFT OPEN ***" % window.abandoned)
        print("Something was still running in it. Closing a window with a live")
        print("process raises a modal sheet that only you can dismiss, and")
        print("while it is up every automation call hangs behind it — so this")
        print("left it rather than making things worse. Close it when you")
        print("are ready.")
    print("")
    print("Now run `python3 -m manual_smoketest`: %d of the requirements this "
          "project makes" % len(checks.CODES_NEEDING_A_PERSON))
    print("cannot be settled by any of the above, and none of them is recorded")
    print("as verified anywhere.")

    if window.abandoned is not None:
        return EXIT_LEFT_A_WINDOW
    return EXIT_FAILED if failed else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
