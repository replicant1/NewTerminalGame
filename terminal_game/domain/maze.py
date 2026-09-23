"""The maze: a rectangular grid of squares, each either wall or corridor.

A square is a ``(col, row)`` tuple counted from 0: ``col`` runs west to east,
``row`` runs north to south. The game's maze is ``WIDTH`` x ``HEIGHT``
(19 x 29, MAZE-1), but the value accepts any rectangle so that other work
items can hand-build small mazes for their tests, including ones that break
the generator's invariants (a dead end, say).

A square outside the grid is neither wall nor corridor: nothing can move onto
it, and a caller asking "is my neighbour a wall?" at the edge is told no.

Pure domain code: standard library only, no clock, no randomness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

Square = tuple[int, int]

WIDTH = 19
HEIGHT = 29

WALL_CHAR = "#"
CORRIDOR_CHAR = "."

# North, south, east, west, as (dcol, drow). The order is fixed so that every
# neighbour query returns squares in the same order every time.
DIRECTIONS: tuple[Square, ...] = ((0, -1), (0, 1), (1, 0), (-1, 0))


@dataclass(frozen=True)
class Maze:
    """An immutable grid. Two mazes are equal when every square matches."""

    width: int
    height: int
    corridors: frozenset[Square]

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError(f"maze must be at least 1 x 1, got {self.width} x {self.height}")
        outside = sorted(sq for sq in self.corridors if not self.contains(sq))
        if outside:
            raise ValueError(f"corridor squares outside a {self.width} x {self.height} grid: {outside}")

    @classmethod
    def from_rows(cls, rows: Iterable[str]) -> Maze:
        """Build a maze from text, one string per row: ``#`` wall, ``.`` corridor."""
        rows = list(rows)
        if not rows:
            raise ValueError("a maze needs at least one row")
        width = len(rows[0])
        corridors = set()
        for row, line in enumerate(rows):
            if len(line) != width:
                raise ValueError(f"row {row} is {len(line)} squares wide, expected {width}")
            for col, ch in enumerate(line):
                if ch == CORRIDOR_CHAR:
                    corridors.add((col, row))
                elif ch != WALL_CHAR:
                    raise ValueError(f"row {row}, col {col}: {ch!r} is neither {WALL_CHAR!r} nor {CORRIDOR_CHAR!r}")
        return cls(width, len(rows), frozenset(corridors))

    def to_rows(self) -> tuple[str, ...]:
        """The inverse of :meth:`from_rows`."""
        return tuple(
            "".join(CORRIDOR_CHAR if (col, row) in self.corridors else WALL_CHAR for col in range(self.width))
            for row in range(self.height)
        )

    def contains(self, square: Square) -> bool:
        col, row = square
        return 0 <= col < self.width and 0 <= row < self.height

    def is_corridor(self, square: Square) -> bool:
        return square in self.corridors

    def is_wall(self, square: Square) -> bool:
        return self.contains(square) and square not in self.corridors

    def neighbours(self, square: Square) -> tuple[Square, ...]:
        """The squares north, south, east and west of ``square``, in that order,
        leaving out any that fall outside the grid."""
        col, row = square
        return tuple(
            (col + dc, row + dr) for dc, dr in DIRECTIONS if self.contains((col + dc, row + dr))
        )

    def open_neighbours(self, square: Square) -> tuple[Square, ...]:
        """The corridor squares north, south, east and west of ``square``, in that order."""
        return tuple(sq for sq in self.neighbours(square) if sq in self.corridors)

    def corridor_squares(self) -> tuple[Square, ...]:
        """Every corridor square, row by row from the north, west to east within a row."""
        return tuple(sorted(self.corridors, key=lambda sq: (sq[1], sq[0])))
