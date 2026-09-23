"""How the ghost moves.  (GHOST-2, GHOST-3, GHOST-4, SCORE-4)

The ghost is a square and a heading, kept in the game state as
``GameState.ghost`` and ``GameState.ghost_heading`` (WI-7).  The heading is the
direction of its last move, as a ``(dcol, drow)`` step from
:data:`terminal_game.domain.maze.DIRECTIONS`, or ``None`` before it has moved.

One step of the policy, :func:`ghost_step`:

1. **No heading yet** (its first move): it moves to one of its open
   neighbours, chosen at random.
2. **The square ahead is corridor**: it moves there, along corridors and
   straight through junctions alike, for as long as the corridor lets it
   (GHOST-2).
3. **The square ahead is wall** (or off the grid): it moves to one of its other
   open neighbours, leaving out the square it came from, chosen at random.  Only
   when there is no such square does it turn back the way it came (GHOST-3).

It is handed the maze, the ghost's square and heading, and a random source:
**nothing about the player** (GHOST-4) and **nothing about the dots** (SCORE-4).
It returns the ghost's next square and heading and nothing else, so it cannot
eat or hide a dot, and where the player stands cannot change where it goes.

Turn resolution (WI-11) applies it as::

    move = ghost_step(state.maze, state.ghost, state.ghost_heading, rng)
    state = replace(state, ghost=move.square, ghost_heading=move.heading)

and then decides the collision.

Pure domain code: standard library only, no clock, and the only randomness is
the source it is handed (``random.Random(seed)`` fits).
"""

from __future__ import annotations

from typing import NamedTuple, Optional, Protocol, Sequence, TypeVar

from terminal_game.domain.maze import DIRECTIONS, Maze, Square

T = TypeVar("T")

Heading = Square  # a (dcol, drow) step, one of DIRECTIONS


class Chooser(Protocol):
    """What the policy needs from a random source.  ``random.Random`` fits."""

    def choice(self, seq: Sequence[T]) -> T: ...


class GhostMove(NamedTuple):
    """Where the ghost went, and the heading it went in."""

    square: Square
    heading: Heading


class GhostStuck(ValueError):
    """The ghost's square has no open neighbour at all, so it cannot move."""


def _step(square: Square, heading: Heading) -> Square:
    return (square[0] + heading[0], square[1] + heading[1])


def ghost_step(maze: Maze, square: Square, heading: Optional[Heading], rng: Chooser) -> GhostMove:
    """The ghost's next square and heading.  See the module docstring for the rules."""
    if heading is not None and heading not in DIRECTIONS:
        raise ValueError(f"a heading is one of {DIRECTIONS} or None, not {heading!r}")
    exits = maze.open_neighbours(square)  # always in the order north, south, east, west
    if not exits:
        raise GhostStuck(f"the ghost at {square} has no open neighbour to move to")

    if heading is None:
        nxt = rng.choice(exits)
    else:
        ahead = _step(square, heading)
        if maze.is_corridor(ahead):
            nxt = ahead
        else:
            came_from = _step(square, (-heading[0], -heading[1]))
            others = tuple(sq for sq in exits if sq != came_from)
            nxt = rng.choice(others) if others else came_from
    return GhostMove(nxt, (nxt[0] - square[0], nxt[1] - square[1]))
