# -*- coding: utf-8 -*-
"""WI-15 — the session controller: three states, and no fourth.

**Playing**, **Decided**, **Ended**.  There is no restart edge, no lives, no
levels, no pause and no timer state, because GAME-3 rules every one of them
out in as many words.  The three are not a field that could hold something
else: :attr:`Session.phase` is *derived* from whether the session has been
shut down and whether the game's outcome is decided, so a fourth state has
nowhere to live.

* **Playing** — arrows go to the turn resolver, ticks move the ghost, and
  each change composes a new picture.
* **Decided** — an outcome has been set.  The ghost is no longer ticked, the
  arrow keys do nothing, and the last picture stays exactly as it is
  (END-5).  The status line says which ending happened, which it does by
  itself: the outcome is in the state the composer is handed.
* **Ended** — ``q`` has been pressed (CTRL-4, END-6), or a callback failed.
  The session asks to be shut down, exactly once, and the process exits —
  and because the process owns its window, the window closes without the
  player closing it (assumption **A3**).

**The game is under way the moment the window opens** (START-5).
:meth:`Session.start` composes and shows the first picture before control is
handed to any event loop, and the ghost begins ticking without anything
being pressed.

Assumption A3, and where a reversal would land
----------------------------------------------
WIN-5 says the window *"closes by itself as soon as the game ends"*; END-5
says the last picture stays on screen; END-6 says ``q`` is the only way out
of a finished game.  All three cannot hold on WIN-5's literal reading — that
is **contradiction C-2**, and the user has not ruled.  We proceed on **A3**:
the outcome is decided, the final picture stands, the player presses ``q``,
the process exits, the window closes itself.

**A3 is implemented here and nowhere else.**  If the user rules the other
way — the window closing the instant the outcome is decided — the change is
one line in :meth:`_apply`: enter Ended rather than Decided when the outcome
is set.  One work item, not a hunt.

The seams, and why they are callables
-------------------------------------
This module is the Application layer, so it may name the Domain and nothing
above it.  Everything it needs from above is handed in:

* ``compose(state) -> frame`` — **the one-call seam WI-12 implements**
  (amendment 3).  A game state goes in and a frame comes out.  What is *in*
  that frame — every glyph, the draw order, the status line on row 29 — is
  WI-12's and WI-13's, and nothing here asserts or assumes any of it.
* ``show(frame) -> None`` — where a composed frame goes.  The real one is
  the character grid surface; a test's is a list.
* ``random_source`` — handed straight to the turn resolver for the ghost.
  Nothing here draws from it.
* ``shut_down() -> None`` — what to call on reaching Ended.  The real one is
  the window owner's ``end_session``.  It is called **exactly once**.

There is deliberately **no clock object**.  The session reads no clock and
schedules nothing: it exposes :meth:`tick` and something else decides when
to call it.  In the real game that is the window owner's timer, which starts
before the event loop is entered; in a test it is the test.  *A whole game
therefore runs headless as fast as it can be driven, which is what WI-19
consumes.*

There is no ``Intent`` here either, for the same layering reason: intents
are WI-9's, in the Presentation layer.  A key arrives as one of the two
things it can mean — :meth:`move` with a Domain ``Direction``, or
:meth:`quit`.  The Shell's collaborator in WI-18 is already unpacking a
``KeyPress`` and calling ``translate``; dispatching the intent it gets back
is three lines in the same place, and so exists once.

A failure must not be left to propagate
---------------------------------------
*Amendment 1, from a Tk 8.5 behaviour measured during WI-3.*  **Tk swallows
an exception raised inside an ``after()`` callback**: it reaches
``report_callback_exception``, a traceback is printed, and the main loop
carries on.  So a session that let an error out of a tick would not shut
down — it would sit there with a broken game on screen and an unquittable
window.

:meth:`tick` and :meth:`move` therefore **route a failure into the same
shutdown path ``q`` uses**, deliberately, and do not re-raise.  It is not
absorbed silently: the exception is kept on :attr:`Session.failure` for the
caller to report after the loop returns.  :meth:`start` is different and is
left to raise, because it runs *before* the event loop, where propagation
works and a game that cannot compose its first picture should not open.
"""

from __future__ import annotations

import enum
from typing import Any, Callable, Optional

from ..domain.game_state import GameState, Outcome
from ..domain.maze import Direction, Maze
from ..domain.opening_position import opening_position
from ..domain.turn_resolver import resolve_move, resolve_tick

__all__ = ["Phase", "Session", "new_session"]


class Phase(enum.Enum):
    """The three states a session can be in, and GAME-3 says no more.

    There is no ``PAUSED``, no ``RESTARTING`` and no ``STARTING``: the
    specification rules out everything but these, and a member added here
    would have to be given a transition before it could ever be reached.
    """

    PLAYING = "playing"
    DECIDED = "decided"
    ENDED = "ended"


class Session:
    """One game, from the first picture to the process exiting.

    Hand it the opening state and the four seams above; call
    :meth:`start` once, then :meth:`tick`, :meth:`move` and :meth:`quit` as
    the clock and the player ask for them.
    """

    __slots__ = (
        "_state",
        "_compose",
        "_show",
        "_random_source",
        "_shut_down",
        "_started",
        "_ended",
        "_frame",
        "_failure",
    )

    def __init__(
        self,
        state: GameState,
        *,
        compose: Callable[[GameState], Any],
        show: Callable[[Any], None],
        random_source: Any,
        shut_down: Callable[[], None],
    ) -> None:
        if not isinstance(state, GameState):
            raise TypeError(
                "a session is started from a GameState, not {0!r}".format(state)
            )
        for name, seam in (
            ("compose", compose),
            ("show", show),
            ("shut_down", shut_down),
        ):
            if not callable(seam):
                raise TypeError(
                    "{0} must be callable, not {1!r}".format(name, seam)
                )
        self._state = state
        self._compose = compose
        self._show = show
        self._random_source = random_source
        self._shut_down = shut_down
        self._started = False
        self._ended = False
        self._frame = None  # type: Any
        self._failure = None  # type: Optional[BaseException]

    # -- what the session is ---------------------------------------------

    @property
    def phase(self) -> Phase:
        """Which of the three states this is, worked out rather than stored.

        Ended wins over Decided, because ``q`` is honoured in every state
        (CTRL-4) — a game that was already lost and has now been quit is
        Ended, not Decided.
        """
        if self._ended:
            return Phase.ENDED
        if self._state.is_over:
            return Phase.DECIDED
        return Phase.PLAYING

    @property
    def state(self) -> GameState:
        """The game as it stands.  In Decided this never changes again."""
        return self._state

    @property
    def outcome(self) -> Outcome:
        """Which ending happened, or ``UNDECIDED``.  The resolver's, not ours."""
        return self._state.outcome

    @property
    def frame(self) -> Any:
        """The last picture composed, or ``None`` before :meth:`start`.

        END-5's *"the last picture stays on screen"* is this not changing:
        in Decided nothing new is composed, so the frame the player is
        looking at is the one that showed them how the game ended.
        """
        return self._frame

    @property
    def failure(self) -> Optional[BaseException]:
        """The exception that ended the session, if one did.

        ``None`` for every ordinary game.  It is here so that a failure
        routed into the shutdown path is *reported* rather than absorbed:
        the caller checks it once the event loop has returned.
        """
        return self._failure

    # -- the three things that can happen ---------------------------------

    def start(self) -> None:
        """Compose and show the first picture (START-5).

        Called before control is handed to any event loop.  Starting twice
        does nothing the second time; starting after the session has ended
        raises, because there is no restart edge (GAME-3).

        This one is **not** guarded: it runs outside the event loop, where an
        exception propagates properly, and a game whose first picture cannot
        be composed should fail loudly rather than open a window.
        """
        if self._ended:
            raise RuntimeError("the session has ended; there is no restart")
        if self._started:
            return
        self._started = True
        self._paint()

    def tick(self) -> None:
        """The clock ticked: the ghost moves and the collision is tested.

        Does nothing at all unless the session is Playing — in Decided the
        ghost stands still (END-5) and in Ended there is no game.  Nothing is
        composed when nothing changed.
        """
        self._guarded(self._tick)

    def move(self, direction: Direction) -> None:
        """The player pressed an arrow (CTRL-1, CTRL-2).

        Does nothing at all unless the session is Playing — in Decided the
        arrow keys do nothing (END-5).  A press towards a wall changes
        nothing and composes nothing, which is CTRL-3 arriving here as the
        resolver handing back the state it was given.

        Something that is not a direction is refused **outside** the guard
        below: that is a caller's mistake rather than a game falling over,
        and turning it into a quiet shutdown would hide it.
        """
        if not isinstance(direction, Direction):
            raise ValueError(
                "{0!r} is not one of the four directions".format(direction)
            )
        self._guarded(lambda: self._move(direction))

    def quit(self) -> None:
        """``q`` was pressed: end the session (CTRL-4, END-6).

        Honoured in **every** state, which is what makes ``q`` the only way
        out of a finished game.  Quitting a session that has already ended
        does nothing and does not ask for a second shutdown.
        """
        self._end()

    # -- the steps, one each ----------------------------------------------

    def _tick(self) -> None:
        if self.phase is not Phase.PLAYING:
            return
        self._advance(resolve_tick(self._state, self._random_source))

    def _move(self, direction: Direction) -> None:
        if self.phase is not Phase.PLAYING:
            return
        self._advance(resolve_move(self._state, direction))

    def _advance(self, state: GameState) -> None:
        """Take the resolver's answer, and repaint if anything changed.

        *The picture follows the state.*  A turn that changed nothing — a
        press towards a wall — composes nothing, and so does every tick once
        the game is Decided, because the resolver hands back the same state.
        One rule, and END-5's half of it falls out of it.

        **Here is where assumption A3 lives.**  When the outcome is set the
        session enters Decided, not Ended: the final picture is composed and
        stands until the player presses ``q``.  Ruling the other way is
        calling :meth:`_end` here instead.
        """
        if state != self._state:
            self._state = state
            self._paint()

    def _paint(self) -> None:
        """The one call out to the composer, and the one call to show it.

        What the frame contains is WI-12's and WI-13's; this asks for one
        and passes it on.
        """
        self._frame = self._compose(self._state)
        self._show(self._frame)

    def _end(self, failure: Optional[BaseException] = None) -> None:
        """Enter Ended and ask to be shut down, exactly once."""
        if self._ended:
            return
        self._ended = True
        if failure is not None:
            self._failure = failure
        self._shut_down()

    def _guarded(self, call: Callable[[], None]) -> None:
        """Run *call*; if it fails, end the session rather than raise.

        Amendment 1: Tk swallows an exception raised inside an ``after()``
        callback, so raising here would leave a broken game on an
        unquittable screen.  The failure goes down the same path ``q`` takes
        and is kept on :attr:`failure` so the caller can report it.
        """
        try:
            call()
        except Exception as failure:  # noqa: BLE001 - deliberate, see above
            self._end(failure)


def new_session(
    maze: Maze,
    *,
    compose: Callable[[GameState], Any],
    show: Callable[[Any], None],
    random_source: Any,
    shut_down: Callable[[], None],
) -> Session:
    """A session at the opening position of *maze*, not yet started.

    The opening position — player nearest the middle, ghost furthest away, a
    dot on every other corridor square, score zero — is WI-6's
    (START-1..START-4) and is not restated here.  Call :meth:`Session.start`
    to compose the first picture.
    """
    return Session(
        opening_position(maze),
        compose=compose,
        show=show,
        random_source=random_source,
        shut_down=shut_down,
    )
