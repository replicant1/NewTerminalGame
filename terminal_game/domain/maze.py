"""The maze as data: a fixed 19 x 29 grid of squares, and how to walk it.

MAZE-1 fixes the shape — *"19 squares across and 29 squares deep"* — and this
module takes that literally: **no other shape is representable.**  The width
and the height are module constants rather than constructor arguments, and
every route to a :class:`Maze` goes through a check that the result is that
size.  A 19 x 30 maze is not a bug waiting to be found downstream; it cannot
be built.

MAZE-2 fixes the contents — *"each square of the grid is either corridor or
wall"* — and :class:`Square` has exactly two members, so there is nowhere for
a third kind to live.

**Coordinates.** ``x`` runs 0 to 18 left to right, ``y`` runs 0 to 28 top to
bottom, and ``Position(0, 0)`` is the top-left square.  ``y`` increasing
downwards matches the order the rows are drawn in and the order the specimen
picture reads in, which is worth more than matching school graph paper.  North
is therefore ``y - 1``.

**Nothing here is impure.**  No clock, no filesystem, no toolkit, and in
particular no module-level random source: MAZE-4 says a new maze is laid out
at random every time, and WI-2 does that by being *handed* a random source.
That is what lets every rule in this module be tested with no window and no
clock, and ``tools/layer_rule.py`` keeps it true.
"""

from __future__ import annotations

import enum
from typing import Dict, FrozenSet, Iterable, Iterator, List, NamedTuple, Sequence, Tuple

#: MAZE-1.  Squares across.  Not a default, not a parameter.
WIDTH = 19

#: MAZE-1.  Squares deep.
HEIGHT = 29


class Square(enum.Enum):
    """What a square is.  MAZE-2 allows exactly these two and no others."""

    WALL = "wall"
    CORRIDOR = "corridor"

    def __str__(self) -> str:
        return self.value


#: The characters :meth:`Maze.from_rows` reads and :meth:`Maze.to_rows` writes.
#: A test that hand-builds a maze reads as a picture of one, which matters more
#: here than in most places: every structural property in this module is a
#: property of a shape.
WALL_CHAR = "#"
CORRIDOR_CHAR = "."

_CHARACTERS = {WALL_CHAR: Square.WALL, CORRIDOR_CHAR: Square.CORRIDOR}
_GLYPHS = {Square.WALL: WALL_CHAR, Square.CORRIDOR: CORRIDOR_CHAR}


class Position(NamedTuple):
    """One square's place in the grid.  ``y`` increases downwards."""

    x: int
    y: int

    def step(self, direction: "Direction") -> "Position":
        """The position one square away in ``direction``, bounds ignored.

        Bounds are the maze's business, not a position's: see
        :meth:`Maze.contains` and :meth:`Maze.neighbours`.
        """
        dx, dy = direction.value
        return Position(self.x + dx, self.y + dy)

    def neighbours(self) -> Tuple["Position", ...]:
        """The four orthogonally adjacent positions, in reading order.

        MAZE-2 says corridors *"run only north-south and east-west"*, so there
        are four neighbours and never eight.  Some of these may be off the
        grid; :meth:`Maze.neighbours` is the one that filters.
        """
        return tuple(self.step(direction) for direction in Direction)

    def __str__(self) -> str:
        return "({}, {})".format(self.x, self.y)


class Direction(enum.Enum):
    """The four ways a corridor can run, as ``(dx, dy)`` steps.

    Declared north, south, east, west in reading order of the square they
    reach, so that anything iterating ``Direction`` visits neighbours top,
    bottom, left, right and two runs agree about order without having to say
    so.
    """

    NORTH = (0, -1)
    WEST = (-1, 0)
    EAST = (1, 0)
    SOUTH = (0, 1)

    def opposite(self) -> "Direction":
        """The way back.  GHOST-3 is about exactly this and nothing else."""
        dx, dy = self.value
        return _OPPOSITES[(-dx, -dy)]


_OPPOSITES = {direction.value: direction for direction in Direction}


def _in_bounds(position: Position) -> bool:
    return 0 <= position.x < WIDTH and 0 <= position.y < HEIGHT


class Maze:
    """A 19 x 29 grid of wall and corridor squares.

    Immutable.  Carving returns a new maze rather than changing this one,
    which is what lets WI-2 hold on to a maze it has already checked while it
    tries a repair on a copy.

    Internally a maze is the set of its corridor squares and nothing else:
    every square not in that set is wall, which is MAZE-2 made structural
    rather than remembered.
    """

    __slots__ = ("_corridors",)

    def __init__(self, corridors: Iterable[Position]) -> None:
        """Prefer :meth:`all_walls` or :meth:`from_rows`; both go through here.

        Every position is bounds-checked on the way in, so a maze can never
        hold a square outside 19 x 29 — the other half of "no other shape is
        representable".
        """
        checked = frozenset(Position(*position) for position in corridors)
        outside = sorted(p for p in checked if not _in_bounds(p))
        if outside:
            raise ValueError(
                "corridor squares outside the {} x {} grid: {}".format(
                    WIDTH, HEIGHT, ", ".join(str(p) for p in outside)
                )
            )
        self._corridors = checked  # type: FrozenSet[Position]

    # -- building ---------------------------------------------------------

    @classmethod
    def all_walls(cls) -> "Maze":
        """A solid maze, which is where carving starts."""
        return cls(())

    @classmethod
    def from_rows(cls, rows: Sequence[str]) -> "Maze":
        """Read a maze from 29 rows of 19 characters — ``#`` wall, ``.`` corridor.

        Strict about the shape on purpose.  A test that hand-builds a maze one
        row short should say so at the point of building, not produce a maze
        that quietly disagrees with MAZE-1.
        """
        if len(rows) != HEIGHT:
            raise ValueError(
                "a maze is {} rows deep (MAZE-1); got {}".format(HEIGHT, len(rows))
            )
        corridors = []  # type: List[Position]
        for y, row in enumerate(rows):
            if len(row) != WIDTH:
                raise ValueError(
                    "a maze is {} squares across (MAZE-1); row {} is {}".format(
                        WIDTH, y, len(row)
                    )
                )
            for x, character in enumerate(row):
                if character not in _CHARACTERS:
                    raise ValueError(
                        "a square is wall {!r} or corridor {!r} and nothing else "
                        "(MAZE-2); row {} column {} is {!r}".format(
                            WALL_CHAR, CORRIDOR_CHAR, y, x, character
                        )
                    )
                if _CHARACTERS[character] is Square.CORRIDOR:
                    corridors.append(Position(x, y))
        return cls(corridors)

    def with_corridors_at(self, positions: Iterable[Position]) -> "Maze":
        """This maze with those squares carved to corridor."""
        return Maze(self._corridors | frozenset(positions))

    def with_walls_at(self, positions: Iterable[Position]) -> "Maze":
        """This maze with those squares filled back in to wall."""
        return Maze(self._corridors - frozenset(positions))

    # -- reading ----------------------------------------------------------

    @property
    def width(self) -> int:
        return WIDTH

    @property
    def height(self) -> int:
        return HEIGHT

    def contains(self, position: Position) -> bool:
        """Whether ``position`` is on the grid at all."""
        return _in_bounds(position)

    def square_at(self, position: Position) -> Square:
        """What is at ``position``.  Off the grid is an error, not a wall.

        Returning ``WALL`` for somewhere that does not exist would make an
        out-of-bounds bug look like an ordinary dead end, and MAZE-3's border
        is what keeps anything from asking in the first place.
        """
        if not _in_bounds(position):
            raise IndexError(
                "{} is outside the {} x {} grid".format(position, WIDTH, HEIGHT)
            )
        return Square.CORRIDOR if position in self._corridors else Square.WALL

    def is_corridor(self, position: Position) -> bool:
        return self.square_at(position) is Square.CORRIDOR

    def is_wall(self, position: Position) -> bool:
        return self.square_at(position) is Square.WALL

    def positions(self) -> Iterator[Position]:
        """Every square on the grid, in reading order."""
        for y in range(HEIGHT):
            for x in range(WIDTH):
                yield Position(x, y)

    def corridors(self) -> Tuple[Position, ...]:
        """Every corridor square, in reading order.

        Sorted rather than returned as a set, so that anything built on top of
        it — a dot field, a furthest-square search, a failure message — reads
        the same way twice.  START-2's tie-breaking depends on that.
        """
        return tuple(sorted(self._corridors, key=lambda p: (p.y, p.x)))

    def walls(self) -> Tuple[Position, ...]:
        """Every wall square, in reading order."""
        return tuple(p for p in self.positions() if p not in self._corridors)

    def border(self) -> Tuple[Position, ...]:
        """The outermost ring of squares, in reading order.

        MAZE-3's *"solid wall right around the outside"* is a statement about
        exactly these, so they are named once here rather than recomputed by
        everyone who cares.
        """
        return tuple(
            p
            for p in self.positions()
            if p.x in (0, WIDTH - 1) or p.y in (0, HEIGHT - 1)
        )

    # -- walking ----------------------------------------------------------

    def neighbours(self, position: Position) -> Tuple[Position, ...]:
        """The orthogonally adjacent squares that are on the grid."""
        if not _in_bounds(position):
            raise IndexError(
                "{} is outside the {} x {} grid".format(position, WIDTH, HEIGHT)
            )
        return tuple(p for p in position.neighbours() if _in_bounds(p))

    def corridor_neighbours(self, position: Position) -> Tuple[Position, ...]:
        """The adjacent squares a player or ghost could step onto.

        MAZE-5 is a statement about the size of this tuple: *"from any
        corridor square there are always at least two ways on"*.
        """
        return tuple(p for p in self.neighbours(position) if p in self._corridors)

    def ways_on_from(self, position: Position) -> Dict[Direction, Position]:
        """Each direction that leads to a corridor square, and where it lands.

        The same information as :meth:`corridor_neighbours` with the direction
        kept, which is what a ghost needs in order to know which way it came.
        """
        ways = {}  # type: Dict[Direction, Position]
        for direction in Direction:
            target = position.step(direction)
            if _in_bounds(target) and target in self._corridors:
                ways[direction] = target
        return ways

    # -- rendering, equality, and looking at one in a failure message -----

    def to_rows(self) -> Tuple[str, ...]:
        """The maze as 29 strings of 19 characters, the inverse of :meth:`from_rows`."""
        return tuple(
            "".join(_GLYPHS[self.square_at(Position(x, y))] for x in range(WIDTH))
            for y in range(HEIGHT)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Maze):
            return NotImplemented
        return self._corridors == other._corridors

    def __hash__(self) -> int:
        return hash(self._corridors)

    def __repr__(self) -> str:
        return "<Maze {}x{}, {} corridor squares>".format(
            WIDTH, HEIGHT, len(self._corridors)
        )

    def __str__(self) -> str:
        return "\n".join(self.to_rows())
