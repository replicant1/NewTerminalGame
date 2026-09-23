"""The starting position of a game (START-1 to START-4, GAME-1).

``new_game(maze)`` returns the first :class:`GameState`:

* The player starts on the corridor square nearest the maze's centre square,
  ``(width // 2, height // 2)``, which is column 9, row 14 on the 19 x 29 maze,
  by straight-line distance in grid squares (plan §1.8, Q6). If the centre is
  corridor, that is the centre itself.
* The ghost starts on the corridor square furthest from the player's start, by
  straight-line distance in grid squares, not by distance along the corridors.
* Ties go to the first tied square in row-by-row order, north row first and
  west to east within a row (``Maze.corridor_squares`` order), so the same maze
  always gives the same start.
* Every corridor square but the player's holds a dot; walls hold none. The
  score is 0, the outcome is undecided, and the ghost has no heading yet.

Distances are compared squared, as whole numbers, so ties are exact.

Pure domain code: no clock, and no randomness of its own.
"""

from __future__ import annotations

from terminal_game.domain.game_state import PLAYING, GameState
from terminal_game.domain.maze import Maze, Square


def _squared_distance(a: Square, b: Square) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def centre_square(maze: Maze) -> Square:
    return (maze.width // 2, maze.height // 2)


def new_game(maze: Maze) -> GameState:
    """The starting state for ``maze``. Refuses a maze with fewer than two corridor squares."""
    corridors = maze.corridor_squares()
    if len(corridors) < 2:
        raise ValueError(f"a game needs at least two corridor squares, this maze has {len(corridors)}")
    centre = centre_square(maze)
    # min() and max() return the first of equal keys, which is row-by-row order.
    player = min(corridors, key=lambda sq: _squared_distance(sq, centre))
    ghost = max(corridors, key=lambda sq: _squared_distance(sq, player))
    dots = frozenset(corridors) - {player}
    return GameState(maze=maze, player=player, ghost=ghost, dots=dots, score=0, outcome=PLAYING, ghost_heading=None)
