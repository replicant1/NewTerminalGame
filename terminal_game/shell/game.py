"""WI-14 — the live game: everything joined up.

A real generated maze at start-up, a repeating timer at the ghost's cadence,
key events routed through translation into the session, a repaint after each
turn, and the process ending when the session does.

**This module decides nothing.**  Every rule it applies belongs to something
else — WI-2 generates the maze, WI-8 sets the opening position, WI-13 says
what a key means, WI-11 says what the session does about it, WI-10 resolves a
turn, WI-9 moves the ghost, WI-4b composes the picture, WI-12 writes row 29
and WI-5/WI-6 paint it.  What is here is the wiring, and the tests assert the
joins rather than re-proving any of that.

**The cadence is a constant with a name.**  GHOST-1 says *"about seven times
a second"*; :data:`CADENCE_MS` is 143 milliseconds, which is assumption P6.

**The clock is injectable, and the game can be driven with no real time
passing and nothing on the screen.**  :meth:`Game.tick` is one beat and can be
called directly; the scheduler only exists to call it repeatedly.  A test
passes its own scheduler, or none at all and drives the beats itself — which
is what WI-16's journeys do.  Lane C measured that ``mainloop`` runs on a
withdrawn root with ``after`` callbacks firing inside it, so even the timer
can be exercised without a window reaching the screen.

**The public surface of this module is what WI-16 branches against.**
:func:`build_game`, :class:`Game` and its `start`, `tick`, `handle_key`,
`field`, `session`, `window` and `is_running` are the whole of it.
"""

from __future__ import annotations

import random
from typing import Callable, Optional, Tuple

from terminal_game.application.session import Session
from terminal_game.application.turn import Intent
from terminal_game.domain.generation import generate
from terminal_game.domain.maze import Maze
from terminal_game.domain.state import GameState, Outcome, new_game
from terminal_game.presentation import status as status_module
from terminal_game.presentation.field import Cell, Field
from terminal_game.presentation.frame import compose_frame
from terminal_game.presentation.keys import intent_for
from terminal_game.shell.window import GameWindow

#: GHOST-1's *"about seven times a second"*, fixed at 143 ms — assumption P6.
#: 1000 / 143 is 6.99 moves a second.  A named constant rather than a number
#: in a call, because "about" is a judgement somebody made once and should be
#: able to find again.
CADENCE_MS = 143


class Scheduler:
    """What the game needs from a clock: schedule one call, and cancel it.

    :class:`~terminal_game.shell.window.GameWindow` satisfies this already, so
    production passes nothing.  A test passes its own and the game runs with
    no real time passing at all — which is what the plan means by *"the clock
    and the timer are injectable, so the game can be driven from a test
    without waiting"*.
    """

    def after(self, milliseconds: int, callback: "Callable[[], None]") -> str:
        raise NotImplementedError

    def cancel(self, handle: str) -> None:
        raise NotImplementedError


def _status_cells(outcome: Outcome, score: int) -> "Tuple[Cell, ...]":
    """Row 29, asked of WI-12 whole.

    **Nothing about row 29 is decided here, including its padding.**  An
    earlier draft of this module padded WI-12's string to the field width
    itself, which was a mechanical write rather than a composition — but
    WI-12b removed even that: ``status_cells`` returns all 40 cells, so
    STAT-1's *"and nothing else"* stays a statement WI-12 makes on its own.

    **The outcome comes from the session, not from ``GameState.outcome``.**
    That field is a cache the resolver stamps, and WI-11 established that the
    one source of truth is the derived function. Reading the field here would
    put the stale answer on the screen for exactly the boards WI-16 hands in
    by hand — the same defect lane C found in ``Session.__repr__``, wearing
    different clothes.
    """
    return status_module.status_cells(outcome, score)


class Game:
    """The assembled game: a window, a session, a timer and the wiring between.

    Built by :func:`build_game`.  Nothing is on the screen and no timer is
    running until :meth:`start` is called.
    """

    def __init__(
        self,
        window: GameWindow,
        session: Session,
        scheduler: "Optional[Scheduler]" = None,
        cadence_ms: int = CADENCE_MS,
    ) -> None:
        self._window = window
        self._session = session
        self._scheduler = scheduler if scheduler is not None else window
        self._cadence_ms = cadence_ms
        self._handle = None  # type: Optional[str]
        self._field = None  # type: Optional[Field]
        self._started = False

    # -- what it is --------------------------------------------------------

    @property
    def window(self) -> GameWindow:
        return self._window

    @property
    def session(self) -> Session:
        return self._session

    @property
    def state(self) -> GameState:
        """The board as it stands — and, once decided, the last picture's."""
        return self._session.game

    @property
    def outcome(self) -> Outcome:
        return self._session.outcome

    @property
    def field(self) -> "Optional[Field]":
        """The last field composed, or ``None`` before the first paint."""
        return self._field

    @property
    def cadence_ms(self) -> int:
        return self._cadence_ms

    @property
    def is_running(self) -> bool:
        return self._session.is_running

    # -- starting ----------------------------------------------------------

    def start(self) -> None:
        """Paint the first frame, wire the keys, and start the timer.

        START-5: *"the game is under way the moment the window opens: the
        ghost is already moving, and nothing has to be pressed to begin."*
        So the frame is painted and the timer is running before this returns,
        and before the window is ever shown.

        Idempotent, so that an entry point and a test cannot start the timer
        twice between them and double the ghost's speed.
        """
        if self._started:
            return
        self._started = True
        self._window.bind_key("<Key>", self._on_key)
        self.repaint()
        self._schedule()

    # -- the two things that happen -----------------------------------------

    def handle_key(self, keysym: str) -> None:
        """Route one key press: WI-13 translates it, WI-11 acts on it.

        CTRL-5 is the ``None`` coming back from
        :func:`~terminal_game.presentation.keys.intent_for` — a key that means
        nothing gets no further than this line, and nothing is repainted for
        it either.
        """
        intent = intent_for(keysym)
        if intent is None:
            return
        self._session.handle(intent)
        self.repaint()

    def tick(self) -> None:
        """One beat of GHOST-1: the ghost moves whether or not a key arrived.

        Public and callable directly, which is how WI-16 drives a whole game
        without waiting. The scheduler exists only to call this repeatedly.
        """
        self._session.tick()
        self.repaint()

    def repaint(self) -> None:
        """Compose the picture from the session's board and present it.

        Composing it fresh each time rather than mutating the last one is what
        keeps the picture a pure function of the state: there is no way for
        the screen to remember something the board has forgotten.
        """
        state = self.state
        self._field = compose_frame(
            maze=state.maze,
            dots=state.dots,
            player=state.player,
            ghost=state.ghost,
            status_row=_status_cells(self.outcome, state.score),
        )
        if self._window.is_open:
            self._window.present(self._field)

    # -- the timer ---------------------------------------------------------

    def _schedule(self) -> None:
        """Ask for the next beat, if the session still wants one.

        The timer stops when the session stops accepting play, which is END-5:
        *"in Decided a tick moves nothing"*, and a timer still firing into a
        decided game would be a tick that moves nothing, forever.
        """
        self._handle = None
        if not self._session.accepts_play:
            return
        self._handle = self._scheduler.after(self._cadence_ms, self._beat)

    def _beat(self) -> None:
        """What the timer calls: one tick, then ask for the next."""
        self.tick()
        self._schedule()

    def stop(self) -> None:
        """Cancel any pending beat. The window and the board are untouched."""
        if self._handle is not None:
            self._scheduler.cancel(self._handle)
            self._handle = None

    @property
    def timer_is_running(self) -> bool:
        """Whether a beat is currently scheduled."""
        return self._handle is not None

    def _on_key(self, event: "object") -> None:
        self.handle_key(getattr(event, "keysym", ""))

    def __repr__(self) -> str:
        return "Game({}, {}, score {})".format(
            self._session.phase, self.outcome, self.state.score
        )


def build_game(
    master: "Optional[object]" = None,
    random_source: "Optional[object]" = None,
    seed: "Optional[int]" = None,
    maze: "Optional[Maze]" = None,
    scheduler: "Optional[Scheduler]" = None,
    cadence_ms: int = CADENCE_MS,
) -> Game:
    """Assemble a game. Nothing is shown and no timer runs until :meth:`Game.start`.

    :param master: passed to :class:`~terminal_game.shell.window.GameWindow`.
        ``None`` in production, where the game owns the one Tk interpreter;
        a test's own root otherwise, because a second ``tkinter.Tk()`` in one
        process can crash this build.
    :param random_source: where the maze and the ghost's choices come from.
        Anything with ``choice`` and ``randrange``; ``random.Random``
        satisfies it.
    :param seed: a convenience — ``random.Random(seed)`` if no
        ``random_source`` is given. A seeded game is reproducible, which is
        what WI-16's journeys need.
    :param maze: skip generation and play this one. **A test fixture**, and
        the only way to play a board chosen rather than found — WI-16's END-3
        board arrives this way.
    :param scheduler: who calls the tick. Defaults to the window.
    :param cadence_ms: how often. Defaults to :data:`CADENCE_MS`.

    MAZE-4 is met by generating here: *"a new maze is laid out at random every
    time the game is started"*.
    """
    if random_source is None:
        random_source = random.Random(seed)
    if maze is None:
        maze = generate(random_source)

    session_holder = {}  # type: dict

    def on_end() -> None:
        # WIN-5 under assumption P1: reaching Ended closes the window, and
        # the entry point has nothing after run(), so the process follows.
        window.close()

    window = GameWindow(master=master, on_close=lambda: _quit_session(session_holder))
    session = Session(
        new_game(maze), random_source=random_source, on_end=on_end
    )
    session_holder["session"] = session
    return Game(window, session, scheduler=scheduler, cadence_ms=cadence_ms)


def _quit_session(holder: dict) -> None:
    """The window closing is a quit, wherever it came from.

    The close button is a way to leave the game, so it has to reach the
    session — otherwise a player who clicks it ends the window with the
    session still nominally playing. ``Session.quit`` is idempotent and so is
    ``GameWindow.close``, so the two calling each other settles immediately.
    """
    session = holder.get("session")
    if session is not None:
        session.quit()


def run_game(
    master: "Optional[object]" = None,
    seed: "Optional[int]" = None,
    watchdog_ms: "Optional[int]" = None,
) -> Game:
    """Build a game, show it, and run until it ends.

    :param watchdog_ms: close the window unconditionally after this long.
        **Not set in production** — a game that closed itself on a timer would
        be a time limit, and GAME-3 forbids one. It exists so that a test
        which maps a real window cannot leave one on somebody's desk.
    """
    game = build_game(master=master, seed=seed)
    game.start()
    game.window.show()
    if watchdog_ms is not None:
        game.window.after(watchdog_ms, game.window.close)
    game.window.run()
    return game


def main() -> None:
    """The entry point. Returns when the window closes, and nothing follows."""
    run_game()


if __name__ == "__main__":  # pragma: no cover - the entry point itself
    main()
