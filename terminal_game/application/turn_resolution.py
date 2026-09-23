"""Turn resolution: the rules of play, in one place, in a fixed order.

(CTRL-1, CTRL-2, CTRL-3, SCORE-1, SCORE-2, SCORE-3, SCORE-5, END-1, END-2,
END-3, GAME-2; architecture F3 and caution C6.)

Two kinds of turn, each a pure function from one ``GameState`` to the next:

``move_player(state, direction)``, where ``direction`` is one of
``maze.DIRECTIONS`` as ``(dcol, drow)``:

1. **Decided?** Once the game is won or lost, nothing changes.
2. **Wall?** If the square that way is not corridor, nothing changes at all
   (CTRL-3). The same state comes back.
3. **Move** the player one square that way (CTRL-1, CTRL-2).
4. **Collision.** If the ghost is on that square, the game is lost (END-1),
   and the step ends here: the dot there is not eaten and the score stays as
   it was. Meeting the ghost is decided before eating, so when the last dot is
   on the ghost's square, walking onto it is a loss, not a win (END-3).
5. **Eat.** If the square holds a dot, it is removed and the score goes up by
   exactly one (SCORE-1, SCORE-2). A square already eaten adds nothing
   (SCORE-3).
6. **Win.** If that was the last dot, the game is won (END-2).

``step_ghost(state, rng)``:

1. **Decided?** Once the game is won or lost, nothing changes.
2. **Move** the ghost by its policy (WI-8, ``ghost.ghost_step``), carrying its
   heading. The dots are not touched (SCORE-4).
3. **Collision.** If the ghost is now on the player's square, the game is lost
   (END-1).

Moves happen one at a time, never together, so the player and the ghost can
never pass through each other: whichever moves onto the other's square ends
the game on that step.

The score never goes down: the only change to it is ``+ 1`` (SCORE-5).

Application layer: no clock, no toolkit, no presentation. Ticks and moves
arrive as calls; the random source is handed in.
"""

from __future__ import annotations

from dataclasses import replace

from terminal_game.domain.game_state import LOST, PLAYING, WON, GameState
from terminal_game.domain.ghost import Chooser, ghost_step
from terminal_game.domain.maze import DIRECTIONS, Square


def move_player(state: GameState, direction: Square) -> GameState:
    """The state after the player tries to move one square in ``direction``."""
    if direction not in DIRECTIONS:
        raise ValueError(f"a direction is one of {DIRECTIONS}, not {direction!r}")
    if state.outcome is not PLAYING:
        return state
    target = (state.player[0] + direction[0], state.player[1] + direction[1])
    if not state.maze.is_corridor(target):
        return state
    if target == state.ghost:
        return replace(state, player=target, outcome=LOST)
    if target not in state.dots:
        return replace(state, player=target)
    dots = state.dots - {target}
    return replace(state, player=target, dots=dots, score=state.score + 1, outcome=PLAYING if dots else WON)


def step_ghost(state: GameState, rng: Chooser) -> GameState:
    """The state after one step of the ghost."""
    if state.outcome is not PLAYING:
        return state
    move = ghost_step(state.maze, state.ghost, state.ghost_heading, rng)
    outcome = LOST if move.square == state.player else PLAYING
    return replace(state, ghost=move.square, ghost_heading=move.heading, outcome=outcome)
