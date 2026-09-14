"""The player's move: one square, one direction, and what it costs the maze.

CTRL-1 to CTRL-3 and SCORE-1 to SCORE-3, SCORE-5. One function does all of it,
because they are all consequences of the same step:

* **CTRL-1** — the four directions, and no others.
* **CTRL-2** — *one* square per call. There is no repeat, no acceleration and
  no momentum, because there is nowhere to keep any: the move is a function of
  a state and a direction, and the state has no velocity in it. "The player
  never drifts on their own" is true here by construction, and the loop (WI-11)
  only has to not call this when nothing was pressed.
* **CTRL-3** — a press towards a wall does **nothing at all**. Not the square,
  not the score, not the dots, not the outcome. This returns *the state it was
  given*, the same object, so "nothing at all" is checkable by identity rather
  than by listing the things that did not change and hoping the list is
  complete.
* **SCORE-1 / SCORE-2** — stepping onto a dot takes it, for good, and adds one.
* **SCORE-3** — stepping onto a square whose dot has gone scores nothing.
* **SCORE-5** — the score never goes down. Nothing here subtracts; the only
  arithmetic in the module is `+ 1`.

**What this does not do.** It does not decide whether the game is over: the
player may now be standing on the ghost, or may have taken the last dot, and
which of those matters is WI-10's ordered question, not this one's. It does not
move the ghost and it does not read the ghost's position — a move into the
ghost's square is a legal move that WI-10 then reads as a loss. And it leaves
`outcome` exactly as it found it, so a finished game is not accidentally
restarted by a stray key.
"""

from __future__ import annotations

from terminalgame.domain.maze import DIRECTIONS


class NotADirection(ValueError):
    """Something that is not one of the four was offered as a move.

    Plan §11.8 — refuse rather than degrade. The alternative is to treat an
    unrecognised key as "no move", which is indistinguishable from CTRL-3's
    wall and would hide a wiring mistake in the one place CTRL-5 says nothing
    should happen quietly.
    """


def move_player(state, direction):
    """The state after the player steps one square `direction`.

    Returns a new :class:`~terminalgame.domain.game_state.GameState`, or **the
    state it was given, unchanged and identical**, if the way is blocked.

    The order inside matters and is worth reading once: the wall is checked
    before anything else, so a blocked move cannot eat a dot, cannot score, and
    cannot half-happen.
    """
    if direction not in DIRECTIONS:
        raise NotADirection(
            "%r is not one of the four directions (CTRL-1); the four are %s"
            % (direction, ", ".join(each.name for each in DIRECTIONS)))

    target = direction.from_square(*state.player)

    # CTRL-3, and it comes first. Anything off the grid reads as wall too, so
    # the border ring needs no special case.
    if state.maze.is_wall(*target):
        return state

    changes = {"player": target}
    if state.dot_at(target):
        # SCORE-1: gone for the rest of the game. SCORE-2: exactly one point.
        # SCORE-3 is the absence of this branch — an already-eaten square is
        # not in `dots`, so there is nothing to remove and nothing to add.
        changes["dots"] = state.dots - {target}
        changes["score"] = state.score + 1
    return state.with_changes(**changes)
