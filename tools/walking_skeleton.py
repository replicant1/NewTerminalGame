# -*- coding: utf-8 -*-
"""WI-4 — the walking skeleton: candidate 2, end to end, on a real screen.

    /usr/bin/python3 tools/walking_skeleton.py            # 10 seconds, or q
    /usr/bin/python3 tools/walking_skeleton.py --seconds 3
    /usr/bin/python3 tools/walking_skeleton.py --json     # measurements only

This is the proof the whole of M0 exists to reach. It opens the game's own
window at the size WI-2's font metrics give, paints **the specimen picture
from the requirements** through the real surface, logs the ticks arriving and
the keys pressed, and closes the window and exits when ``q`` is pressed or
after a bounded number of seconds, whichever comes first.

**It is not part of the suite.** Its name does not match ``test_*``, so
``unittest discover`` never collects it. What the suite *does* import is
:class:`WalkingSkeleton`, which takes every collaborator as an argument and
names no toolkit, so the join can be asserted with no window anywhere.

It obeys section 4 of the implementation plan in full:

* The quit is scheduled on the toolkit's own scheduler **before** the event
  loop is entered, so it does not depend on anybody pressing anything. There
  is no ``mainloop`` here without a way out.
* The window is reaped in a ``finally``, so a failure anywhere still takes it
  away — and :class:`WindowOwner` reaps on its own failure paths too.
* It only ever acts on the window it created, through the handle it was
  given at the moment of creation. Never "the front window", never by title.
* The window belongs to this process, so killing the process takes the
  window with it. There is no second application left holding one, and so no
  modal sheet for anybody to dismiss.

What it deliberately does **not** do: play. There is no maze generator here,
no ghost and no rules. It paints one fixed picture. Assembling the real game
is WI-18's, and `q` is checked here by keysym only because WI-9's input
translator has not landed yet.
"""

from __future__ import annotations

import json
import os
import sys
import time

if __name__ == "__main__" and __package__ is None:  # pragma: no cover
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from terminal_game.shell.toolkit import KeyPress, PixelSize, ScreenPosition
from terminal_game.shell.window_owner import WindowOwner

#: How long the window stays up if nobody presses anything. Long enough for a
#: person to read the titlebar and look at the picture, which is the point of
#: this item; short enough that a forgotten run goes away on its own.
DEFAULT_LIFETIME_SECONDS = 10

#: Where the window goes until WI-14 lands a real anchor. Down and to the
#: right of the top-left corner, which is WIN-4's spirit without WIN-4's
#: permission question.
SKELETON_POSITION = ScreenPosition(x=160, y=160)

#: The keys that end the session (CTRL-4). Checked here by keysym because
#: WI-9's input translator, which owns this properly, has not landed.
QUIT_KEYSYMS = frozenset(("q", "Q"))


class Journal:
    """What arrived, and when.

    The skeleton's whole output besides the picture: it exists so that a
    person watching can see that ticks really are arriving at the ghost's
    cadence and that arrow keys really are being delivered.
    """

    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self.ticks = 0
        self.keys = []
        self.first_tick_at = None
        self.last_tick_at = None
        self.started_at = self._clock()

    def tick(self) -> None:
        now = self._clock()
        if self.first_tick_at is None:
            self.first_tick_at = now
        self.last_tick_at = now
        self.ticks += 1

    def key(self, key: KeyPress) -> None:
        self.keys.append(key.keysym)

    @property
    def observed_tick_interval_ms(self):
        """The cadence actually observed, or ``None`` before two ticks."""
        if self.ticks < 2 or self.first_tick_at is None:
            return None
        span = self.last_tick_at - self.first_tick_at
        return round(1000.0 * span / (self.ticks - 1), 1)

    def summary(self) -> dict:
        return {
            "ticks": self.ticks,
            "keys": list(self.keys),
            "observed_tick_interval_ms": self.observed_tick_interval_ms,
            "elapsed_s": round(self._clock() - self.started_at, 3),
        }


class WalkingSkeleton:
    """WI-2's surface on WI-3's window, and the keys and ticks in between.

    Every collaborator is an argument, so the assembly can be driven by
    recording doubles with no window anywhere. The three things this class
    owns, and the only three, are:

    * building the surface **on the drawing target the window handed back**,
      and painting the frame through it;
    * passing ticks and keys on to the journal;
    * ending the session on ``q``, and on a timer, so it can never run on.

    What the window does and what the surface does are owned by WI-3 and
    WI-2, and are not re-asserted here.
    """

    def __init__(
        self,
        toolkit,
        pixel_size: PixelSize,
        make_surface,
        frame,
        journal: Journal,
        *,
        lifetime_ms: int = DEFAULT_LIFETIME_SECONDS * 1000,
        position: ScreenPosition = SKELETON_POSITION,
    ) -> None:
        self._toolkit = toolkit
        self._make_surface = make_surface
        self._frame = frame
        self._journal = journal
        self._lifetime_ms = lifetime_ms
        self._owner = WindowOwner(toolkit, pixel_size, self, position=position)
        self._surface = None

    @property
    def owner(self) -> WindowOwner:
        return self._owner

    @property
    def surface(self):
        """The surface, once the window has been opened."""
        return self._surface

    # -- what the window delivers ----------------------------------------

    def on_tick(self) -> None:
        self._journal.tick()

    def on_key(self, key: KeyPress) -> None:
        self._journal.key(key)
        if key.keysym in QUIT_KEYSYMS:
            self._owner.end_session()

    # -- the run ----------------------------------------------------------

    def open(self):
        """Create the window and put the picture in it.

        Returns the surface. The drawing target comes from the window owner
        and is handed straight to the surface factory: that is the WI-2 /
        WI-3 join, and it is the whole reason this item exists.
        """
        target = self._owner.open()
        self._surface = self._make_surface(target)
        self._surface.paint(self._frame)
        return self._surface

    def run(self) -> None:
        """Open, paint, and hand over until ``q`` or the deadline.

        The deadline is scheduled before the event loop is entered, so the
        run is bounded whatever happens next.
        """
        try:
            self.open()
            self._toolkit.schedule_once(self._lifetime_ms, self._owner.end_session)
            self._owner.run()
        finally:
            self._owner.end_session()


# ---------------------------------------------------------------------------
# Everything below here touches the real toolkit and the real screen.
# ---------------------------------------------------------------------------


def specimen_frame():
    """The specimen picture from the requirements, as a frame value.

    Transcribed once, in ``terminal_game/presentation/specimen.py``, and read from there rather
    than copied: two transcriptions of a 30-row picture are two things to
    drift apart. That module is shared data, not a test case — it is
    deliberately not named ``test_*`` — but it does live under ``tests/``,
    which is worth a second look if this file ever grows into something the
    application depends on. It will not: WI-18 builds the real entry point
    from a real game state.
    """
    from terminal_game.presentation.frame import Colour, Frame
    from terminal_game.presentation.specimen import SPECIMEN_ROWS

    return Frame.from_text("\n".join(SPECIMEN_ROWS), Colour.WALL_BLUE)


def _window_still_there(target) -> bool:
    """Is the window we created still in existence?

    Asked of the handle captured at creation and no other. A destroyed Tk
    widget does not answer politely — it raises — which is itself the answer.
    """
    if target is None:
        return False
    try:
        return bool(target.winfo_exists())
    except Exception:
        return False


def main(argv) -> int:  # pragma: no cover - measured by running it, not tested
    from terminal_game.shell import tk_grid
    from terminal_game.shell.grid_surface import font_specification, pixel_size_for
    from terminal_game.shell.tk_toolkit import TkToolkit

    seconds = DEFAULT_LIFETIME_SECONDS
    if "--seconds" in argv:
        seconds = int(argv[argv.index("--seconds") + 1])
    quiet = "--json" in argv
    # --press Up,Left,q drives synthetic key events into the real window, so
    # that the key path can be measured against real Tk without touching the
    # keyboard of whoever is sitting in front of the screen. It presses only
    # into the window this process created.
    pressed = []
    if "--press" in argv:
        pressed = [k for k in argv[argv.index("--press") + 1].split(",") if k]

    # Measured before any window exists, on a Tk interpreter that is
    # withdrawn before it can be mapped. WIN-2 is derived from this and
    # nothing else.
    metrics = tk_grid.measure_metrics()
    pixel_size = pixel_size_for(metrics)

    journal = Journal()
    toolkit = TkToolkit()
    frame = specimen_frame()
    skeleton = WalkingSkeleton(
        toolkit,
        pixel_size,
        lambda target: tk_grid.surface_on(target, metrics),
        frame,
        journal,
        lifetime_ms=seconds * 1000,
    )

    findings = {
        "asked_for": {
            "title": skeleton.owner.spec.title,
            "width_px": pixel_size.width,
            "height_px": pixel_size.height,
            "cell_width_px": metrics.width,
            "cell_height_px": metrics.height,
            "font": list(font_specification()),
            "tick_interval_ms": skeleton.owner.tick_interval_ms,
            "lifetime_s": seconds,
            "keys_to_press": list(pressed),
        },
        "measured": {},
        "error": None,
    }

    if not quiet:
        print("Opening the game's window for up to {0}s. Press q to close it "
              "sooner; it closes itself either way.".format(seconds))

    target = None
    try:
        surface = skeleton.open()
        target = surface.canvas
        root = target.winfo_toplevel()

        def measure():
            width, height = root.tk.splitlist(root.wm_resizable())
            findings["measured"].update({
                "title_read_back": root.title(),
                "window_width_px": root.winfo_width(),
                "window_height_px": root.winfo_height(),
                "canvas_width_px": target.winfo_width(),
                "canvas_height_px": target.winfo_height(),
                "x": root.winfo_x(),
                "y": root.winfo_y(),
                "background": root.cget("background"),
                "resizable_width": bool(int(width)),
                "resizable_height": bool(int(height)),
                "canvas_items": len(target.find_all()),
                "canvas_item_kinds": sorted(
                    {target.type(item) for item in target.find_all()}
                ),
                "tk_version": root.tk.call("info", "patchlevel"),
            })

        toolkit.schedule_once(400, measure)
        for index, keysym in enumerate(pressed):
            toolkit.schedule_once(
                600 + 150 * index,
                lambda k=keysym: root.event_generate(
                    "<KeyPress>", keysym=k, when="now"
                ),
            )
        toolkit.schedule_once(seconds * 1000, skeleton.owner.end_session)
        skeleton.owner.run()
    except BaseException as exc:
        findings["error"] = "{0}: {1}".format(type(exc).__name__, exc)
    finally:
        skeleton.owner.end_session()
        findings["measured"]["window_reaped"] = not _window_still_there(target)

    findings["measured"].update(journal.summary())
    findings["measured"]["nominal_tick_interval_ms"] = skeleton.owner.tick_interval_ms
    findings["measured"]["painted_rows"] = (
        len(frame.to_text().split("\n")) if frame is not None else 0
    )

    print(json.dumps(findings, indent=2, sort_keys=True))
    return 1 if findings["error"] else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
