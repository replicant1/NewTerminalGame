# -*- coding: utf-8 -*-
"""WI-18 — the wiring: the game, assembled, from a single command.

    /usr/bin/python3 -m terminal_game
    /usr/bin/python3 -m terminal_game --seed 20260916
    /usr/bin/python3 -m terminal_game --seconds 20

This is the **composition root**: the one place that knows about all four
layers at once and joins them together.  Nothing else in the project does,
and nothing else should.  Everything it joins has its own tests; this module
owns the joins and nothing else.

What it does, in the order the plan gives:

1. seed a random source,
2. lay out a maze and build the opening position,
3. work out how many pixels 40 x 30 cells need, from the font,
4. ask where the window goes,
5. create the window at that anchor, at that size, titled *Terminal Game*,
6. paint the first frame **before** the event loop is entered (START-5),
7. start ticking and hand over,
8. and when the session ends, close the window and exit.

The two traps, and why they are two
-----------------------------------
Both were measured on a real window in WI-17
(``docs/findings/WI-17-real-window-manners.md``).  Neither would have been
found by reading the code, because the code below them is correct.

**A crashed game exits looking clean.**  Tk swallows an exception raised
inside an ``after()`` callback, so the session cannot raise: it routes a
failure into the same shutdown path ``q`` uses and keeps it on
``session.failure``.  Measured consequence — the window is reaped, the phase
reaches Ended, **stderr is empty**, ``run()`` returns **normally**, and
nothing anywhere says the game fell over.  So :meth:`Game.run` **reads that
field**, and :attr:`Game.exit_code` is the only thing that turns it into an
outcome anybody can see.

**The close button would defeat that check.**  ``WindowOwner.open()`` binds
the close request to its **own** ``end_session``, so pressing the close
button takes the window and the process away *without the session ever
knowing* — skipping its shutdown, and with it the failure above.  Measured:
the session's phase was still ``playing`` after a close-button exit.
:meth:`Game.start` therefore **rebinds the close request to the session's
quit**, after opening.  The binding is last-writer-wins, so this needs no
change to :mod:`terminal_game.shell.window_owner`, which is another lane's
landed file — and the window owner's ``end_session`` still runs, because it
is what the session was given as its ``shut_down``.

Why the key dispatch is three lines and not none
------------------------------------------------
A key reaches the session as ``move(Direction)`` or ``quit()``, never as an
``Intent``.  :class:`~terminal_game.presentation.input_translator.Intent` is
Presentation vocabulary and the Application layer may not name Presentation,
so the translation has to happen on this side of that boundary.  The plan
(amendment 5) calls that the layer rule biting correctly rather than a
workaround, and puts the three lines here.  They are in
:class:`GameCollaborator`.
"""

from __future__ import annotations

import random
import sys
from typing import Any, Callable, Optional

from ..application.session import Session, new_session
from ..domain.game_state import GameState
from ..domain.maze_generator import generate_maze
from ..presentation.frame_composer import compose_frame
from ..presentation.input_translator import IntentKind, translate
from ..presentation.status_line import status_row
from .anchor import WindowAnchor
from .toolkit import KeyPress, PixelSize, ScreenPosition, Toolkit
from .window_owner import WindowOwner

__all__ = [
    "compose_picture",
    "GameCollaborator",
    "Game",
    "build_game",
    "main",
]


def compose_picture(state: GameState):
    """A game state in, the whole picture out — WI-15's ``compose`` seam.

    Two lines, and they are the join between WI-12's rows 0–28 and WI-13's
    row 29: the composer places whatever status row it is handed and writes
    nothing there itself.  **This is the production home of that join.**

    A note for whoever tidies up: the same two lines also exist in
    ``tools/the_look.py`` and ``tests/scripted.py``, both DEV-B's, and in
    ``tools/window_manners.py``, mine.  This is the only one in production.
    Consolidating the other three is a one-line change each and is not done
    here, because three of the four are another lane's files.
    """
    return compose_frame(state, status_row(state.score.points, state.outcome))


class GameCollaborator:
    """What the window owner delivers ticks and keys to.

    Structurally a ``SessionCollaborator`` (see
    :mod:`terminal_game.shell.window_owner`); it is not declared as one
    because that protocol is a description rather than a base class.

    It holds no state of its own and makes no decisions.  A tick is a tick.
    A key is translated and dispatched, and **that is the whole of this
    class** — three lines, in :meth:`on_key`.
    """

    __slots__ = ("_session",)

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session

    def attach(self, session: Session) -> None:
        """Give it the session.

        Separate from construction because the session needs the window
        owner's shutdown and the window owner needs this collaborator, so
        one of the three has to be wired up second.
        """
        self._session = session

    @property
    def session(self) -> Optional[Session]:
        return self._session

    def on_tick(self) -> None:
        """GHOST-1: the ghost's cadence, arriving from the Shell's timer."""
        if self._session is None:
            return
        self._session.tick()

    def on_key(self, key: KeyPress) -> None:
        """CTRL-1, CTRL-4, CTRL-5: a key, translated, and acted on.

        An unmapped key reaches the session as nothing at all — not as a
        move of no direction, not as a no-op call.  Nothing is echoed
        anywhere, here or in the translator.
        """
        if self._session is None:
            return
        intent = translate(key.keysym, key.char)
        if intent is None:
            return
        if intent.kind is IntentKind.QUIT:
            self._session.quit()
        else:
            self._session.move(intent.direction)


class Game:
    """The four layers, joined.  Every collaborator is an argument.

    Naming no toolkit is what lets the whole assembly be driven by a
    recording double, with no window anywhere — which is the only way the
    joins below can be in the suite at all.

    *make_surface* is handed the drawing target the window gives back and
    returns something with a ``paint(frame)``.  *make_session* is handed
    ``show`` and ``shut_down`` and returns a session; it is a factory rather
    than a session because the session needs this object's window owner
    before this object exists.
    """

    __slots__ = (
        "_toolkit",
        "_pixel_size",
        "_make_surface",
        "_surface",
        "_collaborator",
        "_owner",
        "_session",
        "_frames_shown",
    )

    def __init__(
        self,
        toolkit: Toolkit,
        pixel_size: PixelSize,
        make_surface: Callable[[Any], Any],
        make_session: Callable[..., Session],
        *,
        position: ScreenPosition,
        tick_interval_ms: Optional[int] = None,
    ) -> None:
        self._toolkit = toolkit
        self._pixel_size = PixelSize(*pixel_size)
        self._make_surface = make_surface
        self._surface = None  # type: Any
        self._frames_shown = 0

        self._collaborator = GameCollaborator()
        owner_arguments = {"position": ScreenPosition(*position)}
        if tick_interval_ms is not None:
            owner_arguments["tick_interval_ms"] = tick_interval_ms
        self._owner = WindowOwner(
            toolkit, self._pixel_size, self._collaborator, **owner_arguments
        )
        self._session = make_session(
            show=self._show, shut_down=self._owner.end_session
        )
        self._collaborator.attach(self._session)

    # -- what it is -------------------------------------------------------

    @property
    def owner(self) -> WindowOwner:
        return self._owner

    @property
    def session(self) -> Session:
        return self._session

    @property
    def collaborator(self) -> GameCollaborator:
        return self._collaborator

    @property
    def surface(self):
        """The surface, once the window has been opened."""
        return self._surface

    @property
    def frames_shown(self) -> int:
        """How many pictures have reached the surface."""
        return self._frames_shown

    @property
    def failure(self) -> Optional[BaseException]:
        """What the session recorded, if it fell over.  ``None`` otherwise."""
        return self._session.failure

    @property
    def exit_code(self) -> int:
        """``0`` for a game that ended, ``1`` for one that fell over.

        **This is the whole of the first trap.**  Nothing else distinguishes
        a crashed game from a finished one: the window closes either way,
        the loop returns either way, and nothing is printed either way.
        """
        return 0 if self._session.failure is None else 1

    # -- the run ----------------------------------------------------------

    def start(self):
        """Open the window, paint the first frame, and rebind the close button.

        START-5 — *"the game is under way the moment the window opens"* —
        is this method: the session composes and shows its first picture
        here, **before** any event loop is entered, and the ghost's timer
        starts in :meth:`run` a moment later without anything being pressed.

        Returns the surface.
        """
        target = self._owner.open()
        self._surface = self._make_surface(target)
        # The second trap.  The window owner bound this to its own
        # end_session, which takes the window and the process without the
        # session ever knowing -- skipping its shutdown and the failure
        # check with it.  Last writer wins, so the window owner's file is
        # untouched, and its end_session still runs as the session's
        # shut_down.
        self._toolkit.bind_close_request(self._session.quit)
        self._session.start()
        return self._surface

    def run(self) -> None:
        """Start if necessary, then hand control to the event loop.

        Returns when the session has ended, by whatever route.  **It does
        not raise on a failed session** — it cannot, because the session
        does not raise either; read :attr:`failure` or :attr:`exit_code`
        afterwards, which is what :func:`main` does.
        """
        if not self._owner.is_open:
            self.start()
        try:
            self._owner.run()
        finally:
            self._owner.end_session()

    def _show(self, frame) -> None:
        """Where a composed frame goes.  The one call into the surface."""
        self._frames_shown += 1
        if self._surface is not None:
            self._surface.paint(frame)


def build_game(
    toolkit: Toolkit,
    pixel_size: PixelSize,
    make_surface: Callable[[Any], Any],
    *,
    position: ScreenPosition,
    random_source: random.Random,
    maze=None,
    compose: Callable[[GameState], Any] = compose_picture,
    tick_interval_ms: Optional[int] = None,
) -> Game:
    """A :class:`Game` over a freshly generated maze.

    *maze* is an argument only so that a caller with a maze already in hand
    need not generate a second one; left out, one is laid out from
    *random_source*, which is the same source the ghost then roams with.
    """
    laid_out = generate_maze(random_source) if maze is None else maze

    def make_session(*, show, shut_down) -> Session:
        return new_session(
            laid_out,
            compose=compose,
            show=show,
            random_source=random_source,
            shut_down=shut_down,
        )

    return Game(
        toolkit,
        pixel_size,
        make_surface,
        make_session,
        position=position,
        tick_interval_ms=tick_interval_ms,
    )


# ---------------------------------------------------------------------------
# Everything below here touches the real toolkit and the real screen.
# ---------------------------------------------------------------------------


def main(argv=()) -> int:  # pragma: no cover - measured by playing it
    """The single command.  Returns the process's exit code.

    ``--seed N`` replays a particular maze.  ``--seconds N`` ends the game
    by itself after N seconds, which is what the bounded exercises this item
    and WI-21 owe are run with; left out, the game lasts until the player
    presses ``q`` or closes the window, which is what a game should do.
    """
    from . import tk_grid
    from .grid_surface import pixel_size_for
    from .tk_anchor import pointer_anchor
    from .tk_toolkit import TkToolkit

    argv = list(argv)
    seed = None
    if "--seed" in argv:
        seed = int(argv[argv.index("--seed") + 1])
    seconds = None
    if "--seconds" in argv:
        seconds = float(argv[argv.index("--seconds") + 1])

    random_source = random.Random(seed)

    # Measured before any window exists, on an interpreter that is withdrawn
    # before it can be mapped.  WIN-2 comes from this and nothing else, and
    # a missing font raises here rather than silently resizing the game.
    metrics = tk_grid.measure_metrics()
    pixel_size = pixel_size_for(metrics)

    # WIN-4, under assumption A2.  Asked once; a query that sees nothing or
    # raises gives the fixed fallback, and the game starts either way.
    position = WindowAnchor(pointer_anchor).position_for(pixel_size)

    toolkit = TkToolkit()
    game = build_game(
        toolkit,
        pixel_size,
        lambda target: tk_grid.surface_on(target, metrics),
        position=position,
        random_source=random_source,
    )

    try:
        game.start()
        if seconds is not None:
            toolkit.schedule_once(int(seconds * 1000), game.session.quit)
        game.run()
    finally:
        game.owner.end_session()

    failure = game.failure
    if failure is not None:
        # Nothing is printed on the ordinary path — CTRL-5 asks for a game
        # that echoes nothing.  A game that fell over is the exception, and
        # saying so is the whole point of reading the recorded failure.
        print(
            "the game fell over: {0}: {1}".format(
                type(failure).__name__, failure
            ),
            file=sys.stderr,
        )
    return game.exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
