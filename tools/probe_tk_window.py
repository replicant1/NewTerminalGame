"""Open one real window for about a second, measure it, and reap it.

**This is not part of the test suite.** Its name does not match ``test_*.py``,
so ``unittest discover`` never collects it. It is run deliberately, by a
person or by a developer who has decided to, with:

    /usr/bin/python3 tools/probe_tk_window.py

Why it exists: under candidate 2 the window is the application's own, and
everything WI-3 claims about it — that the title is exact, that the geometry
is honoured, that the window cannot be resized, that the tick fires at the
ghost's cadence — is a claim about what Tk 8.5 actually does on this machine.
The suite cannot check any of it, because the suite must never open a window.
So this does, once, briefly, and writes down what it saw.

It obeys section 4 of the implementation plan in full:

* It ends **by itself**. The quit is scheduled on Tk's own scheduler before
  the event loop is entered, so it does not depend on anybody pressing
  anything.
* It reaps in a ``finally``, so a failure anywhere still takes the window
  away.
* It only ever acts on the window it created, through the handle it was
  given at the moment of creation.
* There is no ``mainloop`` here without a way out.

One further safety, and it is a real advantage of candidate 2 over the
supervisor design: the window belongs to *this* process. If this process is
killed outright, the window goes with it. There is no second application left
holding a window, and so no modal sheet for anybody to dismiss.
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from terminal_game.shell.cadence import TICK_INTERVAL_MS  # noqa: E402
from terminal_game.shell.tk_toolkit import TkToolkit  # noqa: E402
from terminal_game.shell.toolkit import PixelSize, ScreenPosition  # noqa: E402
from terminal_game.shell.window_owner import WindowOwner  # noqa: E402

#: How long the window is on screen. Short on purpose: somebody is looking at
#: this screen.
LIFETIME_MS = 1200

#: When to take the measurements — late enough that the window manager has
#: certainly mapped and placed the window, early enough to be well clear of
#: the quit.
MEASURE_AT_MS = 700

#: A plausible stand-in for what WI-2's metrics will hand over. Nothing about
#: WI-3 depends on the number; the point is that the window owner is told it.
PROBE_SIZE = PixelSize(width=512, height=600)
PROBE_POSITION = ScreenPosition(x=140, y=140)


class CountingCollaborator:
    """Counts what arrives, so the probe can report that it arrived."""

    def __init__(self):
        self.ticks = 0
        self.keys = []
        self.first_tick_at = None
        self.last_tick_at = None

    def on_tick(self):
        now = time.monotonic()
        if self.first_tick_at is None:
            self.first_tick_at = now
        self.last_tick_at = now
        self.ticks += 1

    def on_key(self, key):
        self.keys.append(key.keysym)


def main() -> int:
    toolkit = TkToolkit()
    collaborator = CountingCollaborator()
    owner = WindowOwner(
        toolkit,
        PROBE_SIZE,
        collaborator,
        position=PROBE_POSITION,
    )
    findings = {
        "asked_for": {
            "title": owner.spec.title,
            "width_px": owner.spec.size.width,
            "height_px": owner.spec.size.height,
            "x": owner.spec.position.x,
            "y": owner.spec.position.y,
            "background": owner.spec.background,
            "resizable": owner.spec.resizable,
            "tick_interval_ms": owner.tick_interval_ms,
        },
        "measured": {},
        "error": None,
    }

    started = time.monotonic()
    try:
        canvas = owner.open()
        # The toplevel reached through the drawing target: a public Tk route,
        # and the same window, not "the front window".
        root = canvas.winfo_toplevel()

        def measure():
            resizable_width, resizable_height = root.resizable()
            findings["measured"] = {
                "title_read_back": root.title(),
                "window_width_px": root.winfo_width(),
                "window_height_px": root.winfo_height(),
                "canvas_width_px": canvas.winfo_width(),
                "canvas_height_px": canvas.winfo_height(),
                "x": root.winfo_x(),
                "y": root.winfo_y(),
                "background": root.cget("background"),
                "resizable_width": bool(resizable_width),
                "resizable_height": bool(resizable_height),
                "tk_version": root.tk.call("info", "patchlevel"),
            }

        # Both of these go on Tk's own scheduler, before the loop is entered,
        # so neither depends on anything happening.
        toolkit.schedule_once(MEASURE_AT_MS, measure)
        toolkit.schedule_once(LIFETIME_MS, owner.end_session)

        owner.run()
    except BaseException as exc:  # reported, not swallowed: see the finally
        findings["error"] = "{0}: {1}".format(type(exc).__name__, exc)
    finally:
        owner.end_session()

    elapsed = time.monotonic() - started
    findings["measured"]["ticks_delivered"] = collaborator.ticks
    findings["measured"]["keys_delivered"] = collaborator.keys
    findings["measured"]["window_lifetime_s"] = round(elapsed, 3)
    if collaborator.ticks > 1 and collaborator.first_tick_at is not None:
        span = collaborator.last_tick_at - collaborator.first_tick_at
        findings["measured"]["observed_tick_interval_ms"] = round(
            1000.0 * span / (collaborator.ticks - 1), 1
        )
    findings["measured"]["nominal_tick_interval_ms"] = TICK_INTERVAL_MS

    print(json.dumps(findings, indent=2, sort_keys=True))
    return 1 if findings["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
