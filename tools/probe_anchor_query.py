#!/usr/bin/env /usr/bin/python3
"""WI-14 — run the real anchor query once, and write down what happened.

    /usr/bin/python3 tools/probe_anchor_query.py

**Not part of the automated suite.**  It constructs a Tk interpreter, and
WI-10's rule 5 forbids the suite doing that.  It is run deliberately, by a
person or by the developer, and it is what
``docs/findings/WI-14-anchor-query.md`` is written from.

Why this script exists at all, in the plan's own words: *a stub cannot prove
the absence of a permission dialog.*  Every test of WI-14 supplies its own
query, so the suite can say the arithmetic is right and can say nothing
whatever about whether the real query prompts.  Only running it can.

What it does, and what it cannot do
-----------------------------------
It creates a Tk root, **withdraws it before anything can be mapped**, reads
the pointer position and the screen size, destroys the root, and prints what
it found.  It never enters an event loop.

* **No window appears.**  Tk does not map a toplevel until the event loop
  runs, and the root is withdrawn first and destroyed in a ``finally``.
* **No keyboard focus is taken**, so it cannot disturb anything the person
  at the machine is doing.
* **No permission is requested.**  The pointer position and the screen size
  are things the toolkit knows about the machine it is on.  There is no code
  here that asks about another application's window — that is the thing
  which needs Accessibility or Automation permission, and it is deliberately
  absent rather than guarded.

The elapsed time is printed because it is the evidence that matters: a TCC
permission dialog blocks the calling process until a human answers it, so a
query that returns in milliseconds is a query that raised no dialog.

It cannot hang.  A watchdog kills the process after
``DEADLINE_SECONDS`` whatever Tk is doing, so there is never a live process
behind a window nobody can see.
"""

from __future__ import annotations

import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from terminal_game.shell.anchor import (  # noqa: E402
    ANCHOR_OFFSET,
    FALLBACK_POSITION,
    WindowAnchor,
    no_anchor,
)
from terminal_game.shell.tk_anchor import pointer_anchor  # noqa: E402
from terminal_game.shell.toolkit import PixelSize  # noqa: E402

#: The window WI-2 measured for Menlo 16pt: 40 x 30 cells.
GAME_WINDOW = PixelSize(width=400, height=570)

#: Hard self-quit.  Generous next to a query that should take milliseconds,
#: and short enough that a hang is over before anybody notices it.
DEADLINE_SECONDS = 10


def _die(signum, frame):  # pragma: no cover - only fires on a hang
    sys.stderr.write(
        "probe_anchor_query: deadline of {0}s reached; something blocked, "
        "which is itself the finding\n".format(DEADLINE_SECONDS)
    )
    os._exit(2)


def main() -> int:
    signal.signal(signal.SIGALRM, _die)
    signal.alarm(DEADLINE_SECONDS)

    print("WI-14 anchor query probe")
    print("interpreter: {0}".format(sys.executable))
    print("")

    started = time.monotonic()
    anchor = pointer_anchor()
    elapsed_ms = (time.monotonic() - started) * 1000.0

    print("the real query, run once")
    print("  returned          : {0!r}".format(anchor))
    print("  elapsed           : {0:.1f} ms".format(elapsed_ms))
    print(
        "  a permission dialog blocks its caller until a human answers, so "
        "this is\n  evidence about whether one appeared."
    )
    print("")

    placed = WindowAnchor(lambda: anchor).position_for(GAME_WINDOW)
    print("where a {0}x{1} window would go".format(*GAME_WINDOW))
    print("  offset            : {0}".format(tuple(ANCHOR_OFFSET)))
    print("  placement         : {0}".format(tuple(placed)))
    print("")

    fallback = WindowAnchor(no_anchor).position_for(GAME_WINDOW)
    print("with no anchor at all (A2's fallback)")
    print("  placement         : {0}".format(tuple(fallback)))
    print("  fixed offset      : {0}".format(tuple(FALLBACK_POSITION)))
    print("")

    try:
        import tkinter

        print(
            "tkinter._default_root after the probe: {0!r}  "
            "(None means the root was destroyed)".format(tkinter._default_root)
        )
    except Exception as failure:  # pragma: no cover
        print("tkinter unavailable: {0!r}".format(failure))

    signal.alarm(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
