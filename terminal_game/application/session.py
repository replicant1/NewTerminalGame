"""The session — three states, and the only thing that decides when a game is over.

    **Playing** → **Decided** → **Ended**, and no others.

There is no ready state and no restart edge, and **GAME-3 is met by their
absence**: *"there are no lives, levels, time limits, power-ups, pause or
restart: one maze, one ghost, one outcome."*  A transition that cannot be
spelled cannot be taken, so the test for GAME-3 is largely a test that this
enumeration has three members and that nothing ever re-enters ``PLAYING``.

**Playing** accepts moves and ticks.  **Decided** stops the tick, ignores
moves and leaves the last picture standing (END-5).  **Quit is honoured in
every state** (CTRL-4, END-6) and takes you to **Ended**, which is what ends
the session and, with it, the window — assumption P1, the reading of WIN-5
that contradiction C-1 settles on.

**Why Decided is more load-bearing than END-5 alone.**  WI-10 made END-3
structural: the outcome is one total function of the state, so *"eating the
last dot on the ghost's square is a loss, not a win"* is true by the shape of
an expression rather than by the order of two statements.  A derived outcome
is only stable while the state is.  **Decided is what keeps the state still,
and therefore what keeps WI-10's outcome honest.**  If anything ever makes
the game mutable after a decision, END-3 breaks again in a new way, and it
will break here rather than in the resolver.  That is the condition the
technical lead attached to approving the structural END-3, and it is why the
tests below assert that a decided game is not merely *ignored* but
*unchanged*.

**Nothing here is impure.**  A tick *arrives as a call* — this module names no
clock and no timer, and the cadence of GHOST-1 is WI-14's.  Randomness arrives
as an argument, as it does everywhere below the Shell.  Ending the process is
not Application's to do either: reaching **Ended** calls an ``on_end``
callback and sets :attr:`Session.is_running` false, and the Shell is what acts
on that.
"""

from __future__ import annotations

import enum
from typing import Callable, Optional

from terminal_game.domain.ghost import RandomSource, next_ghost_move
from terminal_game.domain.maze import Direction, Position
from terminal_game.domain.state import GameState, Outcome
from terminal_game.application.turn import (
    Intent,
    outcome_of,
    resolve_ghost_move,
    resolve_player_intent,
)

#: The heading the ghost starts out with.  GHOST-2 says it keeps going
#: straight, so something has to say which way "straight" is on the first
#: tick.  Nothing in the specification chooses, and no other item claimed it —
#: WI-9 noted it as unclaimed state — so this is an arbitrary but *fixed*
#: choice, pinned by a test so that a seeded run is reproducible.
INITIAL_GHOST_HEADING = Direction.EAST


class Phase(enum.Enum):
    """The three states of a session, and there are no others.

    Called *phase* rather than *state* only because
    :class:`~terminal_game.domain.state.GameState` is already the board; the
    plan's three states are these three members.
    """

    #: Accepting moves and ticks.  A session begins here — START-5, *"the game
    #: is under way the moment the window opens"* — and there is nothing to
    #: pass through first.
    PLAYING = "playing"

    #: The outcome is known.  The tick is stopped, moves are ignored, and the
    #: last picture stands (END-5).
    DECIDED = "decided"

    #: The player has quit.  The session is over and the process should follow
    #: (WIN-5 under assumption P1).
    ENDED = "ended"

    def __str__(self) -> str:
        return self.value


class Session:
    """One game being played, and the state it is in.

    :param game: the opening position, from
        :func:`~terminal_game.domain.state.new_game`.
    :param random_source: where the ghost's choices at a junction come from.
        Consulted only on a tick, and only when the ghost has a choice.
    :param heading: the way the ghost is going to begin with.
    :param on_end: called once, when the session reaches :attr:`Phase.ENDED`.
        This is how WIN-5 reaches the window without Application naming a
        process or a toolkit — the Shell passes something that closes the
        window, and a test passes something that records the call.
    """

    def __init__(
        self,
        game: GameState,
        random_source: RandomSource,
        heading: Direction = INITIAL_GHOST_HEADING,
        on_end: Optional[Callable[[], None]] = None,
    ) -> None:
        self._game = game
        self._random_source = random_source
        self._heading = heading
        self._on_end = on_end
        # START-5: under way immediately.  A board that is already over —
        # which new_game cannot produce, but a hand-built or resumed state
        # can — starts in Decided rather than pretending to be playable.
        self._phase = Phase.PLAYING
        self._settle()

    # -- what it is now ----------------------------------------------------

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def game(self) -> GameState:
        """The board as it stands — and, once decided, the last picture."""
        return self._game

    @property
    def ghost_heading(self) -> Direction:
        """Which way the ghost is going.  Needed to work out its next move."""
        return self._heading

    @property
    def outcome(self) -> Outcome:
        """How the game stands, asked of WI-10 rather than answered here.

        :func:`~terminal_game.application.turn.outcome_of` is one total
        function of the board, and it is what makes END-3 structural. The
        session reads it rather than keeping an opinion, so the two can never
        disagree.
        """
        return outcome_of(self._game)

    @property
    def is_running(self) -> bool:
        """Whether the Shell should still be showing this.

        False only in :attr:`Phase.ENDED`.  A decided game is still running:
        END-5 leaves its last picture on the screen and END-6 says ``q`` is
        the only way out of it.
        """
        return self._phase is not Phase.ENDED

    @property
    def accepts_play(self) -> bool:
        """Whether a move or a tick would do anything.  Only while Playing."""
        return self._phase is Phase.PLAYING

    # -- what happens to it ------------------------------------------------

    def handle(self, intent: Intent) -> None:
        """Act on one thing the player asked for.

        ``QUIT`` is honoured in **every** state (CTRL-4, END-6).  A move is
        honoured only while Playing: in Decided it changes nothing at all, and
        in Ended there is nothing left to change.
        """
        if intent is Intent.QUIT:
            self.quit()
            return
        if self._phase is not Phase.PLAYING:
            return
        self._advance(resolve_player_intent(self._game, intent))

    def tick(self) -> None:
        """One beat of GHOST-1 — the ghost moves whether or not a key arrived.

        The beat *arrives as a call*; this module owns no clock and no timer,
        and how often it happens is WI-14's (143 ms, assumption P6).

        In Decided and in Ended a tick does nothing whatever: not the ghost,
        not the heading, not the board.  That is END-5, and it is also what
        keeps WI-10's derived outcome honest — see the module docstring.
        """
        if self._phase is not Phase.PLAYING:
            return
        move = next_ghost_move(
            self._game.maze, self._game.ghost, self._heading, self._random_source
        )
        self._heading = move.direction
        self._advance(resolve_ghost_move(self._game, move.square))

    def quit(self) -> None:
        """Leave, from wherever we are.  CTRL-4, END-6, and WIN-5's trigger.

        Idempotent: quitting a session that has already ended does nothing and
        does not call ``on_end`` a second time.  The Shell may well hear about
        a quit twice — a key and a closing window — and neither should have to
        know whether the other got there first.
        """
        if self._phase is Phase.ENDED:
            return
        self._phase = Phase.ENDED
        if self._on_end is not None:
            self._on_end()

    # -- the one place the phase changes on its own ------------------------

    def _advance(self, game: GameState) -> None:
        """Take the resolver's answer, and settle what phase that leaves us in."""
        self._game = game
        self._settle()

    def _settle(self) -> None:
        """Move to Decided if the board is over. The only non-quit transition.

        **It asks WI-10's total function rather than reading the state's
        stored outcome**, and that is deliberate.  ``GameState.outcome`` is a
        field that the resolver stamps; a board built by hand — as a test, a
        fixture or a resumed game might be — can carry ``UNDECIDED`` while the
        player and the ghost are on the same square.  Trusting the field would
        let such a board be *playable*, and since Decided is what holds END-3
        up, that is precisely the crack to keep shut.  Asking
        :func:`~terminal_game.application.turn.outcome_of` means the session's
        idea of *over* is the rules' idea of it, always.
        """
        if outcome_of(self._game) is not Outcome.UNDECIDED:
            self._phase = Phase.DECIDED

    def __repr__(self) -> str:
        return "Session({}, {}, score {})".format(
            self._phase, self._game.outcome, self._game.score
        )
