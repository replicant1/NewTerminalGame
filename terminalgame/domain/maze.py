"""The maze as a value, and the queries the rest of the system may ask of it.

Domain layer. This module names nothing above it: no windowing toolkit, no
clock, no global random source. It is handed everything it needs.

Coordinates
-----------
A square is addressed by ``Square(column, row)``. Columns run left to right
from 0, rows run top to bottom from 0, so ``Direction.NORTH`` decreases the
row. A maze of width 19 and height 29 therefore has columns 0..18 and rows
0..28, which is the grid MAZE-1 asks for.

Ownership note for other work items
-----------------------------------
WI-5 owns this query surface. If a later work item needs a question asked of
the maze that is not here, ask for it to be added rather than reaching into
``Maze`` internals or re-deriving the answer from the grid.
"""

from __future__ import annotations

import enum
from typing import Dict, FrozenSet, Iterator, List, NamedTuple, Sequence, Tuple

__all__ = [
    "Direction",
    "DIRECTIONS",
    "Square",
    "SquareKind",
    "Maze",
    "WALL_CHARACTER",
    "CORRIDOR_CHARACTER",
]


#: The two characters ``Maze.from_text`` reads and ``Maze.to_text`` writes.
#: These are a Domain-level debugging and test-fixture notation and have
#: nothing to do with what the player sees; the wall glyphs of SCRN-3 are the
#: Presentation layer's business (WI-8).
WALL_CHARACTER = "#"
CORRIDOR_CHARACTER = "."


class Direction(enum.Enum):
    """The four ways on. The value is the (column, row) step it takes."""

    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)

    @property
    def column_step(self) -> int:
        return self.value[0]

    @property
    def row_step(self) -> int:
        return self.value[1]

    @property
    def opposite(self) -> "Direction":
        return _OPPOSITES[self]


_OPPOSITES: Dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
}

#: A stable order for the four directions, so that anything iterating over
#: them is reproducible from a seed.
DIRECTIONS: Tuple[Direction, ...] = (
    Direction.NORTH,
    Direction.EAST,
    Direction.SOUTH,
    Direction.WEST,
)


class Square(NamedTuple):
    """One square of the grid."""

    column: int
    row: int

    def neighbour(self, direction: Direction) -> "Square":
        return Square(self.column + direction.column_step, self.row + direction.row_step)


class SquareKind(enum.Enum):
    """MAZE-2: each square is either corridor or wall, and nothing else."""

    WALL = "wall"
    CORRIDOR = "corridor"


class Maze:
    """An immutable grid of wall and corridor squares.

    ``Maze`` is a value: two mazes built from the same grid compare equal and
    hash alike. It carries no notion of dots, actors or score.
    """

    __slots__ = ("_rows", "_width", "_height", "_corridor_squares")

    def __init__(self, rows: Sequence[Sequence[SquareKind]]) -> None:
        frozen: Tuple[Tuple[SquareKind, ...], ...] = tuple(tuple(row) for row in rows)
        if not frozen:
            raise ValueError("a maze must have at least one row")
        width = len(frozen[0])
        if width == 0:
            raise ValueError("a maze must have at least one column")
        for index, row in enumerate(frozen):
            if len(row) != width:
                raise ValueError(
                    "every row must be the same width: row 0 has %d squares, row %d has %d"
                    % (width, index, len(row))
                )
            for kind in row:
                if not isinstance(kind, SquareKind):
                    raise ValueError("every square must be a SquareKind, got %r" % (kind,))
        self._rows = frozen
        self._width = width
        self._height = len(frozen)
        self._corridor_squares = tuple(
            Square(column, row)
            for row in range(self._height)
            for column in range(self._width)
            if frozen[row][column] is SquareKind.CORRIDOR
        )

    # ------------------------------------------------------------------
    # Shape
    # ------------------------------------------------------------------

    @property
    def width(self) -> int:
        """How many squares across."""
        return self._width

    @property
    def height(self) -> int:
        """How many squares deep."""
        return self._height

    def contains(self, square: Square) -> bool:
        """Is this square inside the grid at all?"""
        return 0 <= square.column < self._width and 0 <= square.row < self._height

    def squares(self) -> Iterator[Square]:
        """Every square of the grid, row by row, left to right."""
        for row in range(self._height):
            for column in range(self._width):
                yield Square(column, row)

    # ------------------------------------------------------------------
    # What is at a square
    # ------------------------------------------------------------------

    def kind_at(self, square: Square) -> SquareKind:
        """Wall or corridor. Raises for a square outside the grid."""
        self._require_inside(square)
        return self._rows[square.row][square.column]

    def is_wall(self, square: Square) -> bool:
        return self.kind_at(square) is SquareKind.WALL

    def is_corridor(self, square: Square) -> bool:
        return self.kind_at(square) is SquareKind.CORRIDOR

    def corridor_squares(self) -> Tuple[Square, ...]:
        """Every corridor square, in row-major order."""
        return self._corridor_squares

    # ------------------------------------------------------------------
    # Neighbours
    # ------------------------------------------------------------------

    def corridor_neighbours(self, square: Square) -> Tuple[Square, ...]:
        """The orthogonally adjacent squares, inside the grid, that are corridor.

        Ordered north, east, south, west. The square itself need not be
        corridor: asking a wall square which corridors touch it is legitimate.
        """
        return tuple(self.ways_on(square).values())

    def ways_on(self, square: Square) -> Dict[Direction, Square]:
        """The directions a mover on this square may take, and where each leads.

        Only corridor squares inside the grid count as a way on, so the solid
        border of MAZE-3 is what stops anything leaving the maze.
        """
        self._require_inside(square)
        exits: Dict[Direction, Square] = {}
        for direction in DIRECTIONS:
            neighbour = square.neighbour(direction)
            if self.contains(neighbour) and self._rows[neighbour.row][neighbour.column] is SquareKind.CORRIDOR:
                exits[direction] = neighbour
        return exits

    def wall_neighbours(self, square: Square) -> FrozenSet[Direction]:
        """The directions in which this square's orthogonal neighbour is a wall.

        A neighbour outside the grid is **not** a wall, so the square in the
        top-left corner of a bordered maze reports ``{EAST, SOUTH}``. That is
        what makes the border ring resolve to the corner and edge glyphs the
        specimen picture shows.
        """
        self._require_inside(square)
        found = []
        for direction in DIRECTIONS:
            neighbour = square.neighbour(direction)
            if self.contains(neighbour) and self._rows[neighbour.row][neighbour.column] is SquareKind.WALL:
                found.append(direction)
        return frozenset(found)

    # ------------------------------------------------------------------
    # Text notation, for fixtures and debugging
    # ------------------------------------------------------------------

    @classmethod
    def from_text(cls, text: str) -> "Maze":
        """Build a maze from lines of ``#`` (wall) and ``.`` (corridor).

        Blank leading and trailing lines are ignored so that a fixture can be
        written as a triple-quoted block.
        """
        lines = [line for line in text.strip("\n").splitlines()]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            raise ValueError("a maze must have at least one row")
        rows: List[List[SquareKind]] = []
        for row_index, line in enumerate(lines):
            row: List[SquareKind] = []
            for column_index, character in enumerate(line):
                if character == WALL_CHARACTER:
                    row.append(SquareKind.WALL)
                elif character == CORRIDOR_CHARACTER:
                    row.append(SquareKind.CORRIDOR)
                else:
                    raise ValueError(
                        "unknown character %r at column %d of row %d: expected %r or %r"
                        % (character, column_index, row_index, WALL_CHARACTER, CORRIDOR_CHARACTER)
                    )
            rows.append(row)
        return cls(rows)

    def to_text(self) -> str:
        """The inverse of :meth:`from_text`."""
        return "\n".join(
            "".join(
                WALL_CHARACTER if kind is SquareKind.WALL else CORRIDOR_CHARACTER
                for kind in row
            )
            for row in self._rows
        )

    # ------------------------------------------------------------------
    # Value semantics
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Maze):
            return NotImplemented
        return self._rows == other._rows

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash(self._rows)

    def __repr__(self) -> str:
        return "Maze(width=%d, height=%d)" % (self._width, self._height)

    # ------------------------------------------------------------------

    def _require_inside(self, square: Square) -> None:
        if not isinstance(square, Square):
            raise TypeError("expected a Square, got %r" % (square,))
        if not self.contains(square):
            raise ValueError(
                "square %r is outside a %d x %d maze" % (tuple(square), self._width, self._height)
            )
