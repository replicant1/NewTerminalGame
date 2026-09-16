# -*- coding: utf-8 -*-
"""WI-18 — the assembled game, exercised on a real screen.

    /usr/bin/python3 tools/play_the_game.py --exercise first-frame
    /usr/bin/python3 tools/play_the_game.py --exercise played
    /usr/bin/python3 tools/play_the_game.py --exercise crash
    /usr/bin/python3 tools/play_the_game.py --exercise close

**One window per run, and the run ends by itself.** Everything is scheduled
on Tk's own scheduler before the event loop is entered, there is a backstop
whatever else happens, and the window is reaped in a ``finally``. Nothing
waits on a person and nothing blocks.

**It is not part of the suite**: ``unittest discover -p "test_*.py"`` does
not collect it.

Why it exists, when the game already has an entry point
-------------------------------------------------------
``/usr/bin/python3 -m terminal_game`` is the game and is meant to be played
by a person, unbounded, until they press ``q``. An agent must never launch
that. These four exercises drive the **same assembled**
:class:`~terminal_game.shell.game.Game` under a hard deadline, with keys
driven into the window this process created, and print what they saw.

Two of them exist because *proved by a double is not proved*, and both are
things WI-17 measured one level down and WI-18 changed:

* ``crash`` — a game whose composer falls over must exit **non-zero**. WI-17
  measured that the window is reaped, ``run()`` returns normally, stderr is
  empty and nothing says the game crashed. ``exit_code`` is the only thing
  that does, and a double cannot show it working on real Tk.
* ``close`` — the close button must now reach the **session**. WI-17
  measured the phase still ``playing`` afterwards, because the window owner
  binds that request to its own shutdown. WI-18 rebinds it, and this is the
  exercise that says whether the rebinding survives contact with a real
  window manager message.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import random
import sys
import time

if __name__ == "__main__" and __package__ is None:  # pragma: no cover
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from terminal_game.shell.game import build_game, compose_picture
from tools.window_manners import press_the_close_button, window_still_there

#: The backstop. Short: a person is looking at this screen, and every
#: exercise ends long before it on its own.
DEFAULT_LIFETIME_MS = 5000

#: Fixed so that the same run twice gives the same maze and the same answer.
EXERCISE_SEED = 20260916

__all__ = ["run_exercise", "main"]


class FallingComposer:
    """The real composer, until the picture it was told to fall over on.

    An error path exercised with an input that legitimately produces an
    error. **No production code is altered**; this is a collaborator handed
    to the session by this script, and the prohibition on mutating working
    code to watch something go red stands.
    """

    class DeliberateComposeFailure(Exception):
        pass

    def __init__(self, fail_after: int = 3) -> None:
        self._fail_after = fail_after
        self.composed = 0

    def __call__(self, state):
        self.composed += 1
        if self.composed > self._fail_after:
            raise self.DeliberateComposeFailure(
                "the composer fell over on picture {0}".format(self.composed)
            )
        return compose_picture(state)


def run_exercise(name, lifetime_ms=DEFAULT_LIFETIME_MS):
    # pragma: no cover - the point of it is that it needs a real window
    """Open the assembled game once, do one thing to it, and report."""
    from terminal_game.shell import tk_grid
    from terminal_game.shell.anchor import WindowAnchor
    from terminal_game.shell.grid_surface import pixel_size_for
    from terminal_game.shell.tk_anchor import pointer_anchor
    from terminal_game.shell.tk_toolkit import TkToolkit

    metrics = tk_grid.measure_metrics()
    pixel_size = pixel_size_for(metrics)
    anchor = WindowAnchor(pointer_anchor)
    position = anchor.position_for(pixel_size)
    toolkit = TkToolkit()

    composer = FallingComposer(fail_after=3) if name == "crash" else compose_picture
    game = build_game(
        toolkit,
        pixel_size,
        lambda target: tk_grid.surface_on(target, metrics),
        position=position,
        random_source=random.Random(EXERCISE_SEED),
        compose=composer,
    )

    report = {
        "exercise": name,
        "pid": os.getpid(),
        "lifetime_ms": lifetime_ms,
        "error": None,
        "asked_for": {
            "title": game.owner.spec.title,
            "width_px": pixel_size.width,
            "height_px": pixel_size.height,
            "x": position.x,
            "y": position.y,
            "cell_width_px": metrics.width,
            "cell_height_px": metrics.height,
            "tick_interval_ms": game.owner.tick_interval_ms,
            "anchor_query_saw_something": anchor.anchor() is not None,
            "anchor_query_failure": None
            if anchor.failure is None
            else repr(anchor.failure),
        },
        "measured": {},
    }

    # The six keys the "played" exercise drives: the four arrows, one key the
    # game must ignore, and q. Pressed into the window this process created,
    # through the handle captured at creation.
    keys = ["Up", "Left", "Down", "Right", "z", "q"]
    started = time.monotonic()
    target = None
    opening_square = None
    try:
        surface = game.start()
        target = surface.canvas
        root = target.winfo_toplevel()
        opening_square = _square(game)

        if name == "played":
            for index, keysym in enumerate(keys):
                toolkit.schedule_once(
                    500 + 180 * index,
                    lambda k=keysym: root.event_generate(
                        "<KeyPress>", keysym=k, when="now"
                    ),
                )
        elif name == "close":
            toolkit.schedule_once(900, lambda: press_the_close_button(root))
        elif name == "first-frame":
            toolkit.schedule_once(700, lambda: _measure_window(report, root, target))
            toolkit.schedule_once(1100, game.session.quit)
        # "crash" needs nothing scheduled: the composer falls over on the
        # fourth picture, which the ghost's own ticking reaches by itself.

        # The backstop, before the loop is entered. This run cannot outlive
        # it even if nothing else happens at all.
        toolkit.schedule_once(lifetime_ms, game.owner.end_session)
        game.run()
    except BaseException as exc:  # reported, not swallowed: see the finally
        report["error"] = "{0}: {1}".format(type(exc).__name__, exc)
    finally:
        game.owner.end_session()
        report["measured"]["window_reaped"] = not window_still_there(target)
        report["measured"]["lifetime_s"] = round(time.monotonic() - started, 3)

    report["measured"].update({
        "exit_code": game.exit_code,
        "session_failure": None
        if game.failure is None
        else "{0}: {1}".format(type(game.failure).__name__, game.failure),
        "phase_at_the_end": game.session.phase.value,
        "frames_shown": game.frames_shown,
        "score": game.session.state.score.points,
        "outcome": game.session.state.outcome.name,
        "opening_square": opening_square,
        "player_square": _square(game),
        "player_moved": opening_square != _square(game),
        "ended_before_the_backstop": report["measured"]["lifetime_s"]
        < lifetime_ms / 1000.0,
    })
    if name == "played":
        report["measured"]["keys_pressed"] = keys
    if name == "crash":
        report["measured"]["pictures_composed"] = composer.composed
        report["measured"]["the_exception_came_back_out_of_run"] = (
            report["error"] is not None
        )
    return report


def _square(game):  # pragma: no cover - needs an assembled game
    player = game.session.state.player
    return [player.column, player.row]


def _measure_window(report, root, canvas):  # pragma: no cover - needs a window
    """Read the window back, once, from the handle we were given."""
    raw_resizable = root.wm_resizable()
    width_flag, height_flag = root.tk.splitlist(raw_resizable)
    report["measured"].update({
        "title_read_back": root.title(),
        "window_width_px": root.winfo_width(),
        "window_height_px": root.winfo_height(),
        "x": root.winfo_x(),
        "y": root.winfo_y(),
        "background": root.cget("background"),
        "resizable_width": bool(int(width_flag)),
        "resizable_height": bool(int(height_flag)),
        "canvas_items": len(canvas.find_all()),
        "canvas_item_kinds": sorted({canvas.type(item) for item in canvas.find_all()}),
    })


def expected_to_fail(name) -> bool:
    """Is a non-zero exit the *right* answer for this exercise?"""
    return name == "crash"


def main(argv) -> int:  # pragma: no cover - measured by running it
    name = "first-frame"
    if "--exercise" in argv:
        name = argv[argv.index("--exercise") + 1]
    lifetime_ms = DEFAULT_LIFETIME_MS
    if "--lifetime-ms" in argv:
        lifetime_ms = int(argv[argv.index("--lifetime-ms") + 1])

    if name not in ("first-frame", "played", "crash", "close"):
        print("unknown exercise: {0!r}".format(name), file=sys.stderr)
        return 2

    # CTRL-5 at the shell level: nothing typed is echoed anywhere. The whole
    # run is captured and reported as a measurement rather than printed over
    # the report.
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        report = run_exercise(name, lifetime_ms)
    report["measured"]["stdout_during_the_run"] = out.getvalue()
    report["measured"]["stderr_during_the_run"] = err.getvalue()

    clean = report["error"] is None and report["measured"]["exit_code"] == 0
    report["clean_exit"] = clean
    report["expected_to_fail"] = expected_to_fail(name)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["expected_to_fail"]:
        # A clean exit here would mean the crash went unnoticed, which is
        # the defect this exercise exists to look for.
        return 0 if not clean else 1
    return 0 if clean else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
