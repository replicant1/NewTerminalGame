"""The turn resolver — the one place a game in progress changes.

Everything that can happen in a game happens here: the player moves or is
stopped, a dot is eaten and scored, and the game is won or lost.  Nothing else
in the project changes a :class:`~terminal_game.domain.state.GameState`.

**END-3 is structural here, not sequential.**  The requirement — *"eating the
last dot on the square the ghost is standing on is a loss, not a win"* — was
identified in the plan's section 1.6 as the project's single fragility,
because it lived in the order of two statements and **both orderings end the
game**, so a test that merely observed "the game ended" would not notice a
refactor that swapped them.  The architect's caution C6 named the failure
precisely: if the collision test ever migrates into the movement code, the
requirement breaks silently.

:func:`outcome_of` removes that hazard rather than guarding against it.  The
outcome is **one total function of the state**, whose branches are mutually
exclusive by construction and whose first branch is the collision.  There is
no collision test to migrate, no pair of statements to reorder, and no way to
reach the win branch while the player and the ghost are on the same square.
The order the plan asked to be kept "in one readable place" is now a single
expression.

**What makes that safe, and it is load-bearing.**  A derived outcome is a
function of the state, so it is only as stable as the state is.  **END-5 is
what keeps it honest**: once a game is decided the session stops ticking,
ignores moves and leaves the last picture standing, so nothing can change
underneath a decision and re-derive a different answer.  WI-11 owns that
Decided state, and **WI-11's Decided state is what keeps this module's
outcome correct**.  If anything ever makes the state mutable after a
decision, END-3 breaks again in a new way.  This module does its part with
the ``is_over`` guard at the top of both resolvers.
"""

from __future__ import annotations

import enum
from typing import Dict, Optional

from terminal_game.domain.maze import Direction, Position
from terminal_game.domain.state import GameState, Outcome


class Intent(enum.Enum):
    """What the player has asked for — the vocabulary WI-11 and WI-13 share.

    CTRL-1 gives four arrow keys and CTRL-4 gives ``q``; those are the five
    things a key press can mean.  A key that means none of them means nothing
    at all (CTRL-5), which WI-13 expresses by producing no intent rather than
    by an intent for doing nothing.

    Named here so that the input translator and the session controller cannot
    each invent a different alphabet for the same five ideas.
    """

    MOVE_NORTH = "move north"
    MOVE_SOUTH = "move south"
    MOVE_EAST = "move east"
    MOVE_WEST = "move west"
    QUIT = "quit"

    @property
    def direction(self) -> "Optional[Direction]":
        """Which way this intent moves the player, or ``None`` for ``QUIT``."""
        return _DIRECTIONS.get(self)

    @property
    def is_move(self) -> bool:
        return self in _DIRECTIONS

    def __str__(self) -> str:
        return self.value


_DIRECTIONS = {
    Intent.MOVE_NORTH: Direction.NORTH,
    Intent.MOVE_SOUTH: Direction.SOUTH,
    Intent.MOVE_EAST: Direction.EAST,
    Intent.MOVE_WEST: Direction.WEST,
}


def outcome_of(state: GameState) -> Outcome:
    """How the game stands, as one total function of the state.

    * **END-1** — the player and the ghost on the same square is a loss,
      whichever of them walked into the other.
    * **END-2** — no dots left is a win (GAME-2).
    * **END-3** — *both at once is the loss*, and that is this function's
      branch order and nothing else.  The win branch is not merely tested
      second; it is **unreachable** while the player and the ghost share a
      square, because the branches of one expression are mutually exclusive.

    Total: every state has an outcome, and it does not depend on how the state
    was arrived at.  That is what makes END-3 impossible to break by
    reordering statements somewhere else — there are no statements elsewhere.
    """
    if state.player == state.ghost:
        return Outcome.CAUGHT
    if state.dots_remaining == 0:
        return Outcome.CLEARED
    return Outcome.UNDECIDED


def _ways_on(state: GameState) -> "Dict[Direction, Position]":
    """The moves the player actually has, bounds and walls already applied."""
    return state.maze.ways_on_from(state.player)


def resolve_player_move(state: GameState, direction: Direction) -> GameState:
    """Resolve one player move — CTRL-1, CTRL-2, CTRL-3, SCORE-1/2/3, END-1/2/3.

    :param state: the game as it stands.
    :param direction: the way the player has asked to go.
    :returns: the game after the move, which may be the very same state.

    **One square, then stop** (CTRL-1, CTRL-2): a direction is a single step,
    and nothing here repeats it or carries momentum into the next call.

    **A blocked move changes nothing at all** (CTRL-3): not the position, not
    the score, not the outcome.  The identical state comes back.

    **A move cannot leave the grid** (MAZE-3).  The legal moves are exactly
    the ways on from the player's square, and
    :meth:`~terminal_game.domain.maze.Maze.ways_on_from` yields only corridor
    squares that are on the grid.  So a move at the edge is stopped by there
    being no way on — **not** by asking about a square outside the grid and
    handling what comes back.  Movement cannot wrap because a wrapped square
    is not adjacent and so is never a way on.

    The steps, in order, in this one place:

    1. a decided game does not move at all (END-5, WI-11's, guarded here too);
    2. if the direction is not a way on, return the same state (CTRL-3);
    3. move one square (CTRL-1, CTRL-2);
    4. eat the dot if there is one, scoring it (SCORE-1, SCORE-2; a square
       whose dot has gone scores nothing, which is SCORE-3);
    5. read the outcome off the result (:func:`outcome_of`).

    Step 4 happens before step 5 because a win cannot be seen until the last
    dot is gone.  A player who eats the last dot on the ghost's square
    therefore does eat it and does score it — and is still **caught**, because
    that is what :func:`outcome_of` says.  SCORE-1 agrees: they did move onto
    a square that still had a dot.
    """
    if state.is_over:
        return state

    ways = _ways_on(state)
    if direction not in ways:
        return state

    target = ways[direction]
    moved = state.with_player_at(target)
    eaten = moved.ate_dot_at(target)
    return eaten.decided(outcome_of(eaten))


def resolve_ghost_move(state: GameState, square: Position) -> GameState:
    """Resolve one ghost move — END-1's other arm, and SCORE-4.

    :param state: the game as it stands.
    :param square: where the ghost's policy says it goes next.  **The policy
        is not a parameter and is not called from here**: WI-9 decides where
        the ghost goes, this decides what that means.  Handing in the square
        rather than the policy is what let this item be written without
        waiting for that one.
    :returns: the game after the ghost has moved.
    :raises ValueError: if ``square`` is not a corridor square on the grid,
        which is a fault in the policy rather than a move to be resolved.

    **The ghost eats nothing** (SCORE-4): no dot is touched and the score does
    not change, so a dot under the ghost is still there to be taken.

    **The ghost walking into the player is a loss** (END-1), exactly as the
    player walking into the ghost is, and it is the same
    :func:`outcome_of` that says so for both.
    """
    if state.is_over:
        return state

    if not state.maze.contains(square) or not state.maze.is_corridor(square):
        raise ValueError(
            "the ghost cannot stand on {}: it is not a corridor square on the "
            "grid. The policy that produced it is wrong.".format(square)
        )

    moved = state.with_ghost_at(square)
    return moved.decided(outcome_of(moved))


def resolve_player_intent(state: GameState, intent: Intent) -> GameState:
    """Resolve an :class:`Intent` that moves the player.

    A convenience for WI-11, so that the session controller does not have to
    unpack an intent into a direction itself.  ``QUIT`` is not a move and
    leaves the game untouched: leaving is the session's business (CTRL-4),
    not the resolver's.
    """
    direction = intent.direction
    if direction is None:
        return state
    return resolve_player_move(state, direction)
