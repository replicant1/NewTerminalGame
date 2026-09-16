# -*- coding: utf-8 -*-
"""WI-17 — the window's manners, exercised against real Tk.

    /usr/bin/python3 tools/window_manners.py --exercise window
    /usr/bin/python3 tools/window_manners.py --exercise keys
    /usr/bin/python3 tools/window_manners.py --exercise fail-collaborator
    /usr/bin/python3 tools/window_manners.py --exercise fail-session
    /usr/bin/python3 tools/window_manners.py --exercise close

**One window per run, and the run ends by itself.**  Each exercise opens
exactly one window, schedules everything it is going to do on Tk's own
scheduler *before* the event loop is entered, keeps a backstop that ends the
session whatever else happens, and reaps in a ``finally``.  There is no
``mainloop`` here without a way out and nothing waits on a person.

**It is not part of the suite.**  Its name does not match ``test_*``, so
``unittest discover`` never collects it.  What the suite does import is
:class:`KeyDispatcher`, :class:`Exercise` and :func:`exit_code_for`, none of
which name a toolkit, so their decisions are asserted with no window
anywhere.

Why this item needs a script at all
-----------------------------------
Amendment 2 of the plan shrank WI-17 to mostly verification, and then
attached a warning to it.  **WI-3 was green and its probe passed because
neither ever pressed a key** — with Tk-internal focus alone no key event is
delivered at all, and ``q`` is the only way out of a finished game.  A double
will cheerfully report success on every promise this item makes.  So the
substance of WI-17 is the three exercises section 4 of the plan says it owes:

* a **real key press reaching a real window and being acted on** — not
  logged, *acted on*: the player's square changes and ``q`` ends the session
  (``--exercise keys``);
* a **real exception inside a real** ``after()`` **callback with the window
  confirmed reaped** — in both of the two shapes the application can produce
  one (``--exercise fail-collaborator`` and ``--exercise fail-session``);
* a **real** ``q`` **and a real close button ending the process with no
  orphan** (``--exercise keys`` and ``--exercise close``).

Plus ``--exercise window``, which reads the manners themselves back off a
real window: the title, the refusal to resize, and the absence of a caret.

The two Tk 8.5 behaviours this item is built around
---------------------------------------------------
**Tk swallows an exception raised inside an** ``after()`` **callback.**  It
goes to ``report_callback_exception``, a traceback is printed and the loop
carries on.  So "an exception still reaps the window" cannot be built by
letting anything propagate.  :class:`~terminal_game.shell.tk_toolkit.TkToolkit`
points ``report_callback_exception`` at itself, keeps the first exception,
stops the loop and re-raises out of ``run_event_loop``; this script measures
that the arrangement really works on real Tk rather than only on the double.

**``root.resizable()`` with no arguments returns the Tcl string ``'0 0'``**,
not a pair, so unpacking it raises.  ``--exercise window`` records the raw
string as well as the parsed booleans, because the raw string is the thing
that cost a probe run in WI-3.

What this script deliberately does not do
-----------------------------------------
It does not build the game.  :class:`KeyDispatcher` below is three lines of
key-to-intent translation that exist here so that a real arrow key can be
seen to move a real player; **the production one is WI-18's**, where the plan
puts it, and this class is not a proposal for it.
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

from terminal_game.application.session import Session, new_session
from terminal_game.domain.game_state import GameState
from terminal_game.domain.maze_generator import generate_maze
from terminal_game.presentation.frame_composer import compose_frame
from terminal_game.presentation.input_translator import translate
from terminal_game.presentation.status_line import status_row
from terminal_game.shell.game import GameCollaborator
from terminal_game.shell.toolkit import KeyPress, PixelSize, ScreenPosition
from terminal_game.shell.window_owner import WindowOwner

#: Where the window goes.  WI-14 owns the real anchor; this is the same fixed
#: offset every other script in the project uses, and nothing here depends on
#: it.
EXERCISE_POSITION = ScreenPosition(x=180, y=180)

#: The backstop.  Short on purpose: a person is looking at this screen, and
#: every exercise ends long before this on its own.
DEFAULT_LIFETIME_MS = 4000

#: The seed the ``keys`` exercise lays its maze out from.  Fixed so that the
#: same run twice gives the same picture and the same answer.
EXERCISE_SEED = 20260916

#: Tk's name for the message a window manager sends when the close button is
#: pressed.  Invoking the command Tk registered against it is the same route
#: the close button takes; see :func:`_press_the_close_button`.
CLOSE_PROTOCOL = "WM_DELETE_WINDOW"


# ---------------------------------------------------------------------------
# The parts with a decision in them.  No toolkit is named below this line
# until the "real screen" section, so the suite asserts all of it.
# ---------------------------------------------------------------------------


class KeyDispatcher:
    """WI-18's collaborator, with a notebook strapped to it.

    The dispatch itself — translate, then ``quit()`` or ``move(direction)``
    — is **WI-18's** :class:`~terminal_game.shell.game.GameCollaborator`
    and is not reimplemented here.  When this exercise was written WI-18 had
    not landed, and these were three throwaway lines; now that it has, the
    exercise drives the real thing, which is the only honest way for it to
    claim it exercised the real key path.

    What is left here is the recording: what arrived, what it became, and
    where the player was afterwards, so that ``--exercise keys`` can show an
    arrow key *doing something* rather than being logged. WI-4's skeleton
    pressed keys and wrote them down, which is not the same claim.
    """

    def __init__(self, session) -> None:
        self._session = session
        self._collaborator = GameCollaborator(session)
        #: Every keysym the window delivered, in order.
        self.keys_delivered = []
        #: What each of those became: ``"move"``, ``"quit"`` or ``None``.
        self.intents = []
        #: The player's square after each key, so a move can be seen to have
        #: happened rather than merely been asked for.
        self.player_after_each_key = []
        self.ticks = 0

    def on_tick(self) -> None:
        self.ticks += 1
        self._collaborator.on_tick()

    def on_key(self, key: KeyPress) -> None:
        self.keys_delivered.append(key.keysym)
        intent = translate(key.keysym, key.char)
        self.intents.append(None if intent is None else intent.kind.value)
        self._collaborator.on_key(key)
        self.player_after_each_key.append(_square_of(self._session))


def _square_of(session):
    """The player's square as a plain pair, or ``None`` if there is no game."""
    state = getattr(session, "state", None)
    player = getattr(state, "player", None)
    if player is None:
        return None
    return [player.column, player.row]


class FallingOverCollaborator:
    """Raises on the tick it is told to, and not before.

    This is an error path exercised with an input that legitimately produces
    an error — the tick count is a parameter.  **No working code is altered
    to make anything fail**; the prohibition in section 4 of the plan stands.
    """

    class DeliberateFailure(Exception):
        pass

    def __init__(self, fail_on_tick: int = 3) -> None:
        self._fail_on_tick = fail_on_tick
        self.ticks = 0
        self.keys_delivered = []

    def on_tick(self) -> None:
        self.ticks += 1
        if self.ticks >= self._fail_on_tick:
            raise self.DeliberateFailure(
                "the collaborator fell over on tick {0}".format(self.ticks)
            )

    def on_key(self, key: KeyPress) -> None:
        self.keys_delivered.append(key.keysym)


class Exercise:
    """One window, one bounded script, one report.

    Every collaborator is an argument and no toolkit is named, so the
    boundedness and the reaping can be asserted against a recording double.

    *script* is a sequence of ``(delay_ms, action)``.  Every one of them, and
    the backstop, is scheduled **before** the event loop is entered, so the
    run is bounded whatever happens next and nothing waits on a person.
    """

    def __init__(
        self,
        toolkit,
        pixel_size: PixelSize,
        collaborator,
        *,
        script=(),
        lifetime_ms: int = DEFAULT_LIFETIME_MS,
        position: ScreenPosition = EXERCISE_POSITION,
        name: str = "exercise",
    ) -> None:
        self._toolkit = toolkit
        self._collaborator = collaborator
        self._script = list(script)
        self._lifetime_ms = lifetime_ms
        self._owner = WindowOwner(toolkit, pixel_size, collaborator, position=position)
        self.report = {
            "exercise": name,
            "pid": os.getpid(),
            "lifetime_ms": lifetime_ms,
            "error": None,
            "measured": {},
        }
        #: Filled in by :meth:`run` with the drawing target, so that a caller
        #: can reach the real window through the handle it was given at the
        #: moment of creation, and through no other route.
        self.drawing_target = None

    @property
    def owner(self) -> WindowOwner:
        return self._owner

    @property
    def lifetime_ms(self) -> int:
        return self._lifetime_ms

    @property
    def script(self):
        """Everything scheduled before the loop is entered, in order."""
        return tuple(self._script)

    def at(self, delay_ms: int, action) -> None:
        """Add *action* to the script, *delay_ms* after the window opens.

        Must be no later than the backstop, or it would be asking for
        something to happen after the window has already gone.
        """
        if delay_ms >= self._lifetime_ms:
            raise ValueError(
                "{0} ms is at or past the {1} ms backstop, so it would never "
                "happen".format(delay_ms, self._lifetime_ms)
            )
        self._script.append((delay_ms, action))

    def run(self, on_open=None, still_there=lambda target: False) -> dict:
        """Open, run the script, and reap.

        *on_open* is called once with the drawing target, before anything is
        scheduled, for the parts of an exercise that need the real widget.
        *still_there* answers whether the window survived, and is the only
        place this class would have to name a toolkit if it asked itself.
        """
        started = time.monotonic()
        try:
            self.drawing_target = self._owner.open()
            if on_open is not None:
                on_open(self.drawing_target)
            for delay_ms, action in self._script:
                self._toolkit.schedule_once(delay_ms, action)
            # The backstop, scheduled before the loop is entered: this run
            # cannot outlive it even if everything else fails to happen.
            self._toolkit.schedule_once(self._lifetime_ms, self._owner.end_session)
            self._owner.run()
        except BaseException as exc:  # reported, not swallowed: see the finally
            self.report["error"] = "{0}: {1}".format(type(exc).__name__, exc)
        finally:
            self._owner.end_session()
            self.report["measured"]["window_reaped"] = not still_there(
                self.drawing_target
            )
            self.report["measured"]["lifetime_s"] = round(
                time.monotonic() - started, 3
            )
        return self.report


def exit_code_for(report: dict) -> int:
    """``0`` only if the run was clean in **both** of the ways it can be.

    This is the whole of WI-18's inherited hazard, written down as four
    lines.  An exception that reached ``run_event_loop`` comes back out and
    lands in ``report["error"]``.  An exception inside the *session* never
    gets that far: the session routes it into the same shutdown path ``q``
    uses and keeps it on ``session.failure``, so the event loop returns
    normally and **a crashed game exits looking clean** unless somebody
    looks.  Looking is this function.
    """
    if report.get("error") is not None:
        return 1
    if report.get("measured", {}).get("session_failure"):
        return 1
    if not report.get("measured", {}).get("window_reaped", False):
        return 1
    return 0


def expected_to_fail(exercise_name: str) -> bool:
    """Is a non-clean exit the *right* answer for this exercise?

    The two failure exercises are asking whether a failure is noticed, so a
    clean exit from either of them is the bad outcome, not the good one.
    """
    return exercise_name in ("fail-collaborator", "fail-session")


# ---------------------------------------------------------------------------
# Everything below here touches the real toolkit and the real screen.
# ---------------------------------------------------------------------------


def _still_there(target) -> bool:  # pragma: no cover - needs a real widget
    """Is the window we created still in existence?

    Asked of the handle captured at creation and of no other.  Never "the
    front window", never by title: the user's own shells and editor are
    windows too.  A destroyed Tk widget does not answer politely — it raises
    — which is itself the answer.
    """
    if target is None:
        return False
    try:
        return bool(target.winfo_exists())
    except Exception:
        return False


def _widget_kinds(widget):  # pragma: no cover - needs a real widget
    """Every widget class in the window, the toplevel included."""
    kinds = [type(widget).__name__]
    for child in widget.winfo_children():
        kinds.extend(_widget_kinds(child))
    return kinds


def _press_the_close_button(root):  # pragma: no cover - needs a real window
    """Take the same route the window's own close button takes.

    A window manager does not call a Python function: it sends the toplevel a
    ``WM_DELETE_WINDOW`` message, and Tk answers it by evaluating the Tcl
    command registered against that protocol.  Evaluating that command is
    therefore the real path, and not a stand-in for it — the one thing it
    cannot reproduce is a human hand on a mouse.
    """
    command = root.tk.call("wm", "protocol", root._w, CLOSE_PROTOCOL)
    root.tk.eval(command)


def real_compose(state: GameState):
    """The real composer over the real status line: a state in, a frame out."""
    return compose_frame(state, status_row(state.score.points, state.outcome))


def _real_game_session(show, compose=real_compose):
    # pragma: no cover - assembled, then measured
    """A real session over a real maze, with the real composer.

    Deliberately not an entry point: WI-18 owns assembling the game, and
    this exists only so that the exercises can press a real arrow key at a
    real player and see the player move.  ``shut_down`` is indirected
    through *holder* because the session and the window owner each need the
    other, and the window owner is built second.
    """
    source = random.Random(EXERCISE_SEED)
    maze = generate_maze(source)
    holder = {}
    session = new_session(
        maze,
        compose=compose,
        show=show,
        random_source=source,
        shut_down=lambda: holder["end"](),
    )
    return session, holder


def main(argv) -> int:  # pragma: no cover - measured by running it, not tested
    from terminal_game.shell import tk_grid
    from terminal_game.shell.grid_surface import pixel_size_for
    from terminal_game.shell.tk_toolkit import TkToolkit

    name = "window"
    if "--exercise" in argv:
        name = argv[argv.index("--exercise") + 1]
    lifetime_ms = DEFAULT_LIFETIME_MS
    if "--lifetime-ms" in argv:
        lifetime_ms = int(argv[argv.index("--lifetime-ms") + 1])

    # Measured before any window exists, on an interpreter that is withdrawn
    # before it can be mapped.  WIN-2 comes from this and nothing else.
    metrics = tk_grid.measure_metrics()
    pixel_size = pixel_size_for(metrics)
    toolkit = TkToolkit()

    runner = {
        "window": _exercise_window,
        "keys": _exercise_keys,
        "fail-collaborator": _exercise_fail_collaborator,
        "fail-session": _exercise_fail_session,
        "close": _exercise_close,
    }.get(name)
    if runner is None:
        print("unknown exercise: {0!r}".format(name), file=sys.stderr)
        return 2

    # CTRL-5 at the shell level: nothing typed is echoed anywhere.  The whole
    # of the run is captured, and whatever reached a stream is reported as a
    # measurement rather than printed over the report.
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        report = runner(toolkit, tk_grid, metrics, pixel_size, lifetime_ms)
    report["measured"]["stdout_during_the_run"] = out.getvalue()
    report["measured"]["stderr_during_the_run"] = err.getvalue()

    clean = exit_code_for(report) == 0
    report["clean_exit"] = clean
    report["expected_to_fail"] = expected_to_fail(report["exercise"])
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["expected_to_fail"]:
        # A clean exit here would mean the failure went unnoticed, which is
        # the defect this exercise exists to look for.
        return 0 if not clean else 1
    return 0 if clean else 1


def _surface_on(tk_grid, metrics, target):  # pragma: no cover
    return tk_grid.surface_on(target, metrics)


def _exercise_window(toolkit, tk_grid, metrics, pixel_size, lifetime_ms):
    # pragma: no cover - needs a real window
    """The manners themselves, read back off a real window."""
    from terminal_game.presentation.frame import Colour, Frame
    from terminal_game.presentation.specimen import SPECIMEN_ROWS

    class Idle:
        def on_tick(self):
            pass

        def on_key(self, key):
            pass

    exercise = Exercise(
        toolkit, pixel_size, Idle(), lifetime_ms=lifetime_ms, name="window"
    )
    frame = Frame.from_text("\n".join(SPECIMEN_ROWS), Colour.WALL_BLUE)
    held = {}

    def on_open(target):
        surface = _surface_on(tk_grid, metrics, target)
        surface.paint(frame)
        held["root"] = target.winfo_toplevel()
        held["canvas"] = target
        held["surface"] = surface

    def measure():
        root, canvas = held["root"], held["canvas"]
        # Measured in WI-3: with no arguments this hands back the Tcl string
        # "0 0", not a pair, so unpacking it raises.  Both forms are recorded.
        raw_resizable = root.wm_resizable()
        width_flag, height_flag = root.tk.splitlist(raw_resizable)
        before = sorted(canvas.coords(item) for item in canvas.find_all())
        exercise.report["measured"].update({
            "title_read_back": root.title(),
            "window_width_px": root.winfo_width(),
            "window_height_px": root.winfo_height(),
            "asked_for_width_px": pixel_size.width,
            "asked_for_height_px": pixel_size.height,
            "resizable_raw": raw_resizable,
            "resizable_raw_type": type(raw_resizable).__name__,
            "resizable_width": bool(int(width_flag)),
            "resizable_height": bool(int(height_flag)),
            "canvas_items": len(canvas.find_all()),
            "canvas_item_kinds": sorted(
                {canvas.type(item) for item in canvas.find_all()}
            ),
            # SCRN-7, the window's half of it.  A Tk canvas shows a caret
            # only when one of its text items has the canvas focus; nothing
            # ever gives it away, and the caret is zero pixels wide besides.
            "widget_kinds_in_the_window": sorted(set(_widget_kinds(root))),
            "canvas_insertwidth": canvas.cget("insertwidth"),
            "canvas_takefocus": str(canvas.cget("takefocus")),
            "canvas_focused_item": str(canvas.focus()),
        })
        held["before"] = before

    def resize_request():
        root, canvas = held["root"], held["canvas"]
        # A resize *request*: the shape of event a window manager delivers
        # when somebody drags a corner.  The window is not resizable, so the
        # grid must be exactly what it was.
        root.event_generate(
            "<Configure>",
            width=pixel_size.width + 220,
            height=pixel_size.height + 220,
            when="now",
        )
        root.update_idletasks()
        after = sorted(canvas.coords(item) for item in canvas.find_all())
        exercise.report["measured"].update({
            "window_width_px_after_resize_request": root.winfo_width(),
            "window_height_px_after_resize_request": root.winfo_height(),
            "canvas_items_after_resize_request": len(canvas.find_all()),
            "cell_positions_unchanged_by_resize_request": held["before"] == after,
            "grid_rows": len(frame.to_text().split("\n")),
            "grid_columns": len(frame.to_text().split("\n")[0]),
        })

    exercise.at(500, measure)
    exercise.at(900, resize_request)
    exercise.at(1300, exercise.owner.end_session)
    return exercise.run(on_open=on_open, still_there=_still_there)


def _exercise_keys(toolkit, tk_grid, metrics, pixel_size, lifetime_ms):
    # pragma: no cover - needs a real window
    """A real key press, reaching a real window, and being acted on."""
    painted = {"count": 0}
    held = {}

    def show(frame):
        painted["count"] += 1
        surface = held.get("surface")
        if surface is not None:
            surface.paint(frame)

    session, holder = _real_game_session(show)
    dispatcher = KeyDispatcher(session)
    exercise = Exercise(
        toolkit, pixel_size, dispatcher, lifetime_ms=lifetime_ms, name="keys"
    )
    holder["end"] = exercise.owner.end_session

    def on_open(target):
        held["surface"] = _surface_on(tk_grid, metrics, target)
        held["root"] = target.winfo_toplevel()
        session.start()

    # Six keys: the four arrows, one key the game must ignore, and q.  Driven
    # into the window this process created, through the handle captured at
    # creation, so nobody's keyboard is touched.
    keys = ["Up", "Left", "Down", "Right", "z", "q"]
    for index, keysym in enumerate(keys):
        exercise.at(
            500 + 180 * index,
            lambda k=keysym: held["root"].event_generate(
                "<KeyPress>", keysym=k, when="now"
            ),
        )

    def finish(report):
        report["measured"].update({
            "keys_pressed": keys,
            "keys_delivered": list(dispatcher.keys_delivered),
            "intents": list(dispatcher.intents),
            "player_after_each_key": list(dispatcher.player_after_each_key),
            "player_moved": len(set(
                tuple(square)
                for square in dispatcher.player_after_each_key
                if square is not None
            )) > 1,
            "ticks_delivered": dispatcher.ticks,
            "frames_painted": painted["count"],
            "phase_at_the_end": session.phase.value,
            "session_failure": None
            if session.failure is None
            else repr(session.failure),
        })
        return report

    return finish(exercise.run(on_open=on_open, still_there=_still_there))


def _exercise_fail_collaborator(toolkit, tk_grid, metrics, pixel_size, lifetime_ms):
    # pragma: no cover - needs a real window
    """A real exception inside a real ``after()`` callback.

    The collaborator raises on its third tick.  ``WindowOwner`` reaps and
    re-raises; Tk catches the re-raise and hands it to
    ``report_callback_exception``; the adapter keeps it, stops the loop, and
    ``run_event_loop`` re-raises it once ``mainloop()`` has returned.  If any
    link in that chain is wrong the exercise exits 0 with a window gone and
    nobody any the wiser, which is exactly the shape of defect it looks for.
    """
    collaborator = FallingOverCollaborator(fail_on_tick=3)
    exercise = Exercise(
        toolkit,
        pixel_size,
        collaborator,
        lifetime_ms=lifetime_ms,
        name="fail-collaborator",
    )

    def on_open(target):
        surface = _surface_on(tk_grid, metrics, target)
        del surface

    report = exercise.run(on_open=on_open, still_there=_still_there)
    report["measured"].update({
        "ticks_before_the_failure": collaborator.ticks,
        "the_exception_came_back_out_of_run": report["error"] is not None,
    })
    return report


def _exercise_fail_session(toolkit, tk_grid, metrics, pixel_size, lifetime_ms):
    # pragma: no cover - needs a real window
    """A real session that falls over, which is the case WI-18 inherits.

    The session does **not** re-raise: it routes the failure into the same
    shutdown path ``q`` uses and keeps it on ``session.failure``.  So the
    event loop returns normally, ``run()`` returns normally, and the only
    evidence that the game crashed is a field nobody is obliged to read.
    This exercise reads it, and reports what the answer would have been if
    it had not.
    """
    held = {}
    composed = {"count": 0}

    def show(frame):
        surface = held.get("surface")
        if surface is not None:
            surface.paint(frame)

    class DeliberateComposeFailure(Exception):
        pass

    def compose(state):
        # The first few pictures compose properly, so that the failure
        # happens on a later tick — inside the event loop, which is the
        # whole point.  This is a collaborator handed to the session by this
        # script, not an alteration of any production code.
        composed["count"] += 1
        if composed["count"] > 3:
            raise DeliberateComposeFailure(
                "the composer fell over on picture {0}".format(composed["count"])
            )
        return real_compose(state)

    session, holder = _real_game_session(show, compose=compose)
    dispatcher = KeyDispatcher(session)
    exercise = Exercise(
        toolkit,
        pixel_size,
        dispatcher,
        lifetime_ms=lifetime_ms,
        name="fail-session",
    )
    holder["end"] = exercise.owner.end_session

    def on_open(target):
        held["surface"] = _surface_on(tk_grid, metrics, target)
        session.start()

    report = exercise.run(on_open=on_open, still_there=_still_there)
    report["measured"].update({
        "pictures_composed": composed["count"],
        "ticks_delivered": dispatcher.ticks,
        "phase_at_the_end": session.phase.value,
        "the_exception_came_back_out_of_run": report["error"] is not None,
        "session_failure": None
        if session.failure is None
        else "{0}: {1}".format(type(session.failure).__name__, session.failure),
    })
    return report


def _exercise_close(toolkit, tk_grid, metrics, pixel_size, lifetime_ms):
    # pragma: no cover - needs a real window
    """The window's own close button, taking the route the window manager takes."""
    held = {}

    def show(frame):
        surface = held.get("surface")
        if surface is not None:
            surface.paint(frame)

    session, holder = _real_game_session(show)
    dispatcher = KeyDispatcher(session)
    exercise = Exercise(
        toolkit, pixel_size, dispatcher, lifetime_ms=lifetime_ms, name="close"
    )
    holder["end"] = exercise.owner.end_session

    def on_open(target):
        held["surface"] = _surface_on(tk_grid, metrics, target)
        held["root"] = target.winfo_toplevel()
        session.start()

    exercise.at(900, lambda: _press_the_close_button(held["root"]))

    report = exercise.run(on_open=on_open, still_there=_still_there)
    report["measured"].update({
        "ticks_delivered": dispatcher.ticks,
        "phase_at_the_end": session.phase.value,
        "ended_before_the_backstop": report["measured"]["lifetime_s"]
        < lifetime_ms / 1000.0,
        "session_failure": None
        if session.failure is None
        else repr(session.failure),
    })
    return report


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
