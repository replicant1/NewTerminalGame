"""WI-11 — the one place the rules of a turn are applied, in a fixed order.

Two things happen in this game: the player presses an arrow, and the clock
ticks. Each is one function here, and each begins with the order of its
steps written out as a list you can read at a glance.

**Why the order is in one place (caution C6).** END-3 says that eating the
last dot on the square the ghost is standing on is a *loss*, not a win. That
is not a rule of its own — it is a consequence of testing the collision
before testing the win. If the collision test ever migrates into the
movement code, or the two tests swap places, END-3 breaks and both the
losing case and the winning case still "end the game", so nothing obviously
fails. Keeping the order visible is the mitigation the architect asked for.

**And a second guard, so the order is not the only thing holding END-3 up.**
An outcome, once decided, cannot be replaced: :func:`_decided` refuses. So
even if the win test somehow ran first, the collision could not be
overwritten by a later win, nor a win by a later collision. The requirement
is held up by two independent things, and neither of them is discipline.

**END-1 has two arms.** *"whether the player walked into the ghost or the
ghost walked into the player"* — so the collision test is the step after the
player moves **and** the step after the ghost moves. Both are in the lists
below.

This module names nothing above the Domain layer. It is handed a random
source for the ghost and reads no clock: whose turn it is and how often is
the session controller's business (WI-15), not a rule of the game.
"""

from __future__ import annotations

from .game_state import GameState, Outcome
from .ghost import next_step
from .maze import Direction, Square

__all__ = ["resolve_move", "resolve_tick"]


def resolve_move(state: GameState, direction: Direction) -> GameState:
    """The player presses an arrow.

    The order, and it is the whole rule:

    1. a target square that is wall, or off the grid, means **nothing
       happens at all** — no move, no score, no tick consumed (CTRL-3);
    2. otherwise the player **moves**, exactly one square (CTRL-1, CTRL-2);
    3. then the **collision** is tested (END-1);
    4. then the dot is **eaten**, if there is one (SCORE-1, SCORE-2);
    5. then the **win** is tested (END-2).

    Steps 3 and 5 in that order are END-3, and they are why the game is lost
    rather than won when the last dot is on the ghost's square.
    """
    if state.is_over:
        return state  # END-5: the arrow keys do nothing once a game has ended

    target = state.player.neighbour(direction)
    if not _can_stand_on(state, target):
        return state  # CTRL-3: a press towards a wall does nothing at all

    state = state.with_player_at(target)
    state = _test_the_collision(state)
    state = _eat_any_dot_under_the_player(state)
    state = _test_the_win(state)
    return state


def resolve_tick(state: GameState, random_source) -> GameState:
    """The clock ticks and the ghost moves (GHOST-1).

    The order:

    1. the ghost **moves** one square, the way its policy says (WI-7);
    2. then the **collision** is tested (END-1's second arm).

    There is no third step. The ghost neither eats a dot nor scores a point
    (SCORE-4), and the only way to be sure of that is for this function
    never to touch the dot field or the score — which it does not.
    """
    if state.is_over:
        return state  # END-5: the ghost stands still once a game has ended

    step = next_step(state.maze, state.ghost, state.ghost_heading, random_source)
    state = state.with_ghost_at(step.square).with_ghost_heading(step.direction)
    state = _test_the_collision(state)
    return state


# ----------------------------------------------------------------------
# The steps, one each, each doing one thing
# ----------------------------------------------------------------------


def _can_stand_on(state: GameState, square: Square) -> bool:
    """CTRL-3 and MAZE-3: corridor squares inside the maze, and nothing else."""
    return state.maze.contains(square) and state.maze.is_corridor(square)


def _test_the_collision(state: GameState) -> GameState:
    """END-1: the game is lost the moment the two stand on the same square."""
    if state.actors_share_a_square:
        return _decided(state, Outcome.CAUGHT)
    return state


def _eat_any_dot_under_the_player(state: GameState) -> GameState:
    """SCORE-1, SCORE-2 and SCORE-3, which are one step and not three.

    A dot is eaten and a point scored together, or neither happens. That is
    what makes an already-eaten square score nothing: there is no dot to
    take, so there is no point to add.
    """
    if not state.dots.has_dot(state.player):
        return state
    return state.with_dots(state.dots.without_dot_at(state.player)).with_score(
        state.score.plus_one()
    )


def _test_the_win(state: GameState) -> GameState:
    """END-2: the game is won when the last dot is eaten."""
    if state.dots.is_empty:
        return _decided(state, Outcome.CLEARED)
    return state


def _decided(state: GameState, outcome: Outcome) -> GameState:
    """Set the ending, unless one has already happened.

    **The first ending to happen is the ending.** This is the second thing
    holding END-3 up, independently of the order of the steps above: a win
    cannot overwrite a collision decided a moment earlier in the same turn.
    """
    if state.outcome.is_decided:
        return state
    return state.with_outcome(outcome)
