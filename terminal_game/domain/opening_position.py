"""WI-6 — where everything stands when the window opens.

The opening position is a **pure function of the maze**.  Nothing here is
handed a random source, unlike the maze generator (WI-5) and the ghost's
movement policy (WI-7): given the same maze, the game always starts the same
way.  The randomness the player sees comes from the maze being new every time
(MAZE-4).

The four requirements this module owns:

* **START-1** — the player begins on the corridor square nearest the middle
  of the maze.
* **START-2** — the ghost begins on the corridor square furthest from the
  player, **measured across the grid and not along the corridors**.  Those
  two measures pick different squares on a real maze, and the requirement is
  explicit about which one it means.
* **START-3** — every other corridor square holds a dot; the player's does
  not.
* **START-4** — the score starts at zero.

Ties, and why they are broken the way they are
----------------------------------------------
The requirements say *the* nearest and *the* furthest square, as though each
were unique.  On a real 19 x 29 maze neither is: the centre of the grid falls
on a connector square, so when that connector happens to be wall there are
two corridor squares equally near the middle; and the furthest square from
something near the middle is a four-way tie between the corners.

Ties are broken by taking the **first square in row-major order** — top row
first, and left to right within a row.  It is deterministic, so the same maze
always opens the same way, which is what WI-19's scripted game needs.

What that costs is written down in ``docs/findings/WI-6-start-squares.md``
and is worth knowing: measured over 200 generated mazes, **the ghost always
starts in the left-hand column**, at (1, 1) or (1, 27).  A random tie-break
would spread it over all four corners, but that would mean handing this
module a random source, which the work item pointedly does not do.  If that
is wanted, it is a change to :func:`ghost_start_square` and nowhere else.
"""

from __future__ import annotations

from typing import Tuple

from .dot_field import DotField
from .game_state import GameState, Outcome, Score
from .maze import Maze, Square

__all__ = [
    "straight_line_distance_squared",
    "player_start_square",
    "ghost_start_square",
    "opening_position",
]


def straight_line_distance_squared(one: Square, other: Square) -> int:
    """How far apart two squares are across the grid, squared.

    Squared, so the arithmetic stays in whole numbers: nothing compares a
    distance to anything but another distance, and squaring preserves the
    order. This is START-2's *"measured across the grid"* — the corridors
    play no part in it.
    """
    return (one.column - other.column) ** 2 + (one.row - other.row) ** 2


def player_start_square(maze: Maze) -> Square:
    """START-1: the corridor square nearest the middle of the maze.

    The middle of a 19 x 29 grid is the point (9, 14), and of an even-sided
    grid it falls between squares, so distances are measured in doubled
    coordinates to keep them whole. Ties go to the first square in row-major
    order.
    """
    corridors = _require_corridors(maze)
    doubled_centre_column = maze.width - 1
    doubled_centre_row = maze.height - 1

    def distance_from_centre(square: Square) -> int:
        return (2 * square.column - doubled_centre_column) ** 2 + (
            2 * square.row - doubled_centre_row
        ) ** 2

    return min(corridors, key=lambda square: (distance_from_centre(square), square.row, square.column))


def ghost_start_square(maze: Maze, player: Square) -> Square:
    """START-2: the corridor square furthest from the player across the grid.

    **Not the furthest along the corridors.** A square two steps away in a
    straight line can be twenty steps away through the maze, and the
    requirement says the straight line. Ties go to the first square in
    row-major order.
    """
    corridors = _require_corridors(maze)
    if not maze.is_corridor(player):
        raise ValueError(
            "the player starts on a corridor square, not %r" % (tuple(player),)
        )
    if len(corridors) < 2:
        raise ValueError(
            "a maze needs at least two corridor squares for the two to start apart"
        )
    return max(
        corridors,
        key=lambda square: (
            straight_line_distance_squared(square, player),
            -square.row,
            -square.column,
        ),
    )


def opening_position(maze: Maze) -> GameState:
    """The whole game, at the moment the window opens.

    GAME-1: one player, one ghost, one maze, dots along its corridors.
    """
    player = player_start_square(maze)
    ghost = ghost_start_square(maze, player)
    return GameState(
        maze=maze,
        dots=DotField.over_corridors_except(maze, player),
        player=player,
        ghost=ghost,
        score=Score.zero(),
        outcome=Outcome.UNDECIDED,
    )


def _require_corridors(maze: Maze) -> Tuple[Square, ...]:
    corridors = maze.corridor_squares()
    if not corridors:
        raise ValueError("a maze with no corridor has nowhere for a game to start")
    return corridors
