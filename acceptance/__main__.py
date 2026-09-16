# -*- coding: utf-8 -*-
"""``python3 -m acceptance`` — run the pack, or list what a person must do.

    python3 -m acceptance --list      # the human checks; opens nothing
    python3 -m acceptance --run       # the exercises, on the real desktop

``--list`` is the default, because the half of this pack that needs no desktop
should be the one you get by accident.
"""

from __future__ import annotations

import argparse
import sys

from acceptance import checks, pack
from launcher.game import game_command

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_LEFT_A_WINDOW = 2


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python3 -m acceptance",
        description="The acceptance pack: what a machine can check, and what "
                    "it cannot.")
    # One or the other, never both: they were two `store_true` flags and
    # `--list` was accepted and then never read, so `--run --list` ran. Saying
    # which you meant is better than being given one of them silently.
    what = parser.add_mutually_exclusive_group()
    what.add_argument("--list", action="store_true",
                      help="print the human checks and open nothing (default)")
    what.add_argument("--run", action="store_true",
                      help="run the exercises against the real desktop")
    parser.add_argument("--show-picture", action="store_true",
                        help="print what the tab was showing, with --run")
    arguments = parser.parse_args(argv)

    if arguments.list or not arguments.run:
        print(checks.render())
        return EXIT_OK

    print("THE EXERCISES")
    print("=" * 70)
    print("Opening one window. It will end itself with `q` — this pack never")
    print("uses a hold and never starts a game it cannot stop.")
    print("")
    observations, shown, window = pack.run(game_command())
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
        print("while it is up every automation call hangs behind it — so the")
        print("pack left it rather than making things worse. Close it when you")
        print("are ready.")
    print("")
    print("Now run `python3 -m acceptance --list`: %d of the requirements this "
          "project makes" % len(checks.CODES_NEEDING_A_PERSON))
    print("cannot be settled by any of the above, and none of them is recorded")
    print("as verified anywhere.")

    if window.abandoned is not None:
        return EXIT_LEFT_A_WINDOW
    return EXIT_FAILED if failed else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
