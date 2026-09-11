"""Frozen value types — the shared vocabulary of the whole project.

Everything here is immutable. Every transition anywhere in this project
returns a **new** value; nothing mutates.

This module is part of the pure core: it imports nothing impure, holds no
game logic, and knows nothing about a terminal, a window or a clock.

The vocabulary
--------------

============  =========================================================
:class:`Position`   a ``(row, col)`` pair; it *is* a tuple, so a plain
                    ``(r, c)`` compares and hashes equal to it
:class:`Direction`  one of :data:`UP`, :data:`DOWN`, :data:`LEFT`,
                    :data:`RIGHT`, carrying its ``(dr, dc)`` delta
:class:`Outcome`    :data:`Outcome.PLAYING`, :data:`Outcome.CAUGHT`,
                    :data:`Outcome.CLEARED`
:class:`Maze`       a grid of wall/corridor cells that can answer, for any
                    cell, whether it is corridor and which of its four
                    neighbours are corridor
:class:`GameState`  maze, player, ghost, ghost heading, remaining dots,
                    score, outcome — and nothing else (GAME-3)
:class:`Frame`      the picture: a 30 x 40 grid of character-plus-style
                    that can be read back as 30 plain strings
============  =========================================================
"""

import enum
from dataclasses import dataclass, field, fields
from typing import Dict, FrozenSet, Iterable, NamedTuple, Optional, Tuple

# --------------------------------------------------------------------------
# Geometry constants
# --------------------------------------------------------------------------

#: The maze is 29 squares deep and 19 across (MAZE-1).
MAZE_ROWS = 29
MAZE_COLS = 19

#: The window is 30 rows deep and 40 columns across (WIN-2).
SCREEN_ROWS = 30
SCREEN_COLS = 40


# --------------------------------------------------------------------------
# Position
# --------------------------------------------------------------------------


class Position(NamedTuple):
    """A cell of the maze grid, counted from the top-left.

    It is a :class:`tuple` subclass, so ``Position(3, 4) == (3, 4)`` and the
    two hash alike. Code elsewhere may use whichever reads better.
    """

    row: int
    col: int

    def shifted(self, direction: "Direction") -> "Position":
        """This position moved one square in ``direction``."""
        return Position(self.row + direction.dr, self.col + direction.dc)


# --------------------------------------------------------------------------
# Direction
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Direction:
    """One of the four ways on, with the row/column delta that realises it."""

    name: str
    dr: int
    dc: int

    def opposite(self) -> "Direction":
        """The direction that undoes this one."""
        return _DIRECTION_BY_DELTA[(-self.dr, -self.dc)]


UP = Direction("UP", -1, 0)
DOWN = Direction("DOWN", 1, 0)
LEFT = Direction("LEFT", 0, -1)
RIGHT = Direction("RIGHT", 0, 1)

#: The four directions in a fixed, canonical order. Anything that picks a
#: direction at random must iterate in this order, or seeded runs stop being
#: reproducible.
DIRECTIONS: Tuple[Direction, ...] = (UP, DOWN, LEFT, RIGHT)

_DIRECTION_BY_DELTA: Dict[Tuple[int, int], Direction] = {
    (d.dr, d.dc): d for d in DIRECTIONS
}

#: Look a direction up by name, e.g. ``DIRECTION_BY_NAME["UP"]``.
DIRECTION_BY_NAME: Dict[str, Direction] = {d.name: d for d in DIRECTIONS}


# --------------------------------------------------------------------------
# Outcome
# --------------------------------------------------------------------------


class Outcome(enum.Enum):
    """How the game stands: still on, lost, or won."""

    PLAYING = "PLAYING"
    CAUGHT = "CAUGHT"
    CLEARED = "CLEARED"


# --------------------------------------------------------------------------
# Maze
# --------------------------------------------------------------------------

WALL = False
CORRIDOR = True


@dataclass(frozen=True)
class Maze:
    """An immutable grid of wall/corridor cells.

    ``cells[row][col]`` is :data:`CORRIDOR` (``True``) or :data:`WALL`
    (``False``). The neighbour lookup is derived once at construction, so
    :meth:`open_directions` is a dictionary hit rather than a recount.

    The neighbour query is deliberately part of this type rather than of any
    caller: the player's movement rules and the ghost's movement policy both
    need exactly this answer.
    """

    cells: Tuple[Tuple[bool, ...], ...]

    # Derived, and excluded from equality and repr: two mazes with the same
    # cells are the same maze.
    _open: Dict[Position, Tuple[Direction, ...]] = field(
        default_factory=dict, compare=False, repr=False
    )

    def __post_init__(self) -> None:
        rows = tuple(tuple(bool(c) for c in row) for row in self.cells)
        if not rows or not rows[0]:
            raise ValueError("a maze needs at least one cell")
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError("a maze must be rectangular")
        object.__setattr__(self, "cells", rows)

        opens: Dict[Position, Tuple[Direction, ...]] = {}
        height = len(rows)
        for r in range(height):
            for c in range(width):
                if not rows[r][c]:
                    continue
                here = Position(r, c)
                found = []
                for d in DIRECTIONS:
                    nr, nc = r + d.dr, c + d.dc
                    if 0 <= nr < height and 0 <= nc < width and rows[nr][nc]:
                        found.append(d)
                opens[here] = tuple(found)
        object.__setattr__(self, "_open", opens)

    # -- shape -------------------------------------------------------------

    @property
    def height(self) -> int:
        """How many rows deep the maze is."""
        return len(self.cells)

    @property
    def width(self) -> int:
        """How many columns across the maze is."""
        return len(self.cells[0])

    def contains(self, position: Tuple[int, int]) -> bool:
        """Whether ``position`` is inside the grid at all."""
        row, col = position
        return 0 <= row < self.height and 0 <= col < self.width

    # -- the corridor / open-neighbour query -------------------------------

    def is_corridor(self, position: Tuple[int, int]) -> bool:
        """Whether ``position`` is a corridor square.

        A position outside the grid is not corridor, so callers never need a
        bounds check of their own.
        """
        if not self.contains(position):
            return False
        return self.cells[position[0]][position[1]]

    def is_wall(self, position: Tuple[int, int]) -> bool:
        """Whether ``position`` is a wall square, or off the grid."""
        return not self.is_corridor(position)

    def open_directions(self, position: Tuple[int, int]) -> Tuple[Direction, ...]:
        """Which of the four neighbours of ``position`` are corridor.

        Returned in :data:`DIRECTIONS` order, so a seeded choice over them is
        reproducible. Empty for a wall square or a square off the grid.
        """
        return self._open.get(Position(position[0], position[1]), ())

    def open_neighbours(self, position: Tuple[int, int]) -> Tuple[Position, ...]:
        """The corridor neighbours of ``position``, as positions."""
        here = Position(position[0], position[1])
        return tuple(here.shifted(d) for d in self.open_directions(here))

    def corridor_degree(self, position: Tuple[int, int]) -> int:
        """How many ways on there are from ``position`` (MAZE-5 is ``>= 2``)."""
        return len(self.open_directions(position))

    def is_open(self, position: Tuple[int, int], direction: Direction) -> bool:
        """Whether one can step from ``position`` in ``direction``."""
        return direction in self.open_directions(position)

    # -- whole-grid queries ------------------------------------------------

    def corridors(self) -> FrozenSet[Position]:
        """Every corridor square in the maze."""
        return frozenset(self._open)

    def rows(self) -> Tuple[str, ...]:
        """The grid as text, ``'.'`` for corridor and ``'#'`` for wall.

        Round-trips through :func:`termgame.maze.from_text`.
        """
        return tuple(
            "".join("." if cell else "#" for cell in row) for row in self.cells
        )


# --------------------------------------------------------------------------
# GameState
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class GameState:
    """Everything there is to know about a game in progress.

    There is no lives field, no level, no timer, no power-up, no pause and no
    restart, because the game has none of those things (GAME-3). Nothing
    anywhere may add one.
    """

    maze: Maze
    player: Position
    ghost: Position
    ghost_dir: Direction
    dots: FrozenSet[Position]
    score: int
    outcome: Outcome

    def __post_init__(self) -> None:
        object.__setattr__(self, "player", Position(*self.player))
        object.__setattr__(self, "ghost", Position(*self.ghost))
        object.__setattr__(
            self, "dots", frozenset(Position(*d) for d in self.dots)
        )


#: The field names of :class:`GameState`, in declaration order. GAME-3 holds
#: by this tuple being exactly this long.
GAME_STATE_FIELDS: Tuple[str, ...] = tuple(f.name for f in fields(GameState))


# --------------------------------------------------------------------------
# The picture
# --------------------------------------------------------------------------

#: The style of a cell nothing has claimed. Style identifiers are plain
#: strings; the glyph-and-colour tables own the rest of the vocabulary and
#: the curses adapter is the only thing that maps one to a colour pair.
STYLE_DEFAULT = "default"


class Cell(NamedTuple):
    """One character of the picture, and the style identifier it carries."""

    char: str
    style: str


@dataclass(frozen=True)
class Frame:
    """The picture: an immutable grid of character-plus-style.

    It carries **style identifiers, not curses attributes**, so a frame can be
    built and compared with no terminal present. The curses adapter is the
    only thing that turns a style identifier into a colour pair.

    Build one with :class:`FrameBuilder`; read one back with :meth:`rows`.
    """

    cells: Tuple[Tuple[Cell, ...], ...]

    def __post_init__(self) -> None:
        rows = tuple(tuple(Cell(c.char, c.style) for c in row) for row in self.cells)
        if not rows or not rows[0]:
            raise ValueError("a frame needs at least one cell")
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError("a frame must be rectangular")
        for row in rows:
            for cell in row:
                if len(cell.char) != 1:
                    raise ValueError(
                        "every frame cell holds exactly one character, got %r"
                        % (cell.char,)
                    )
        object.__setattr__(self, "cells", rows)

    @property
    def height(self) -> int:
        """How many rows deep the picture is."""
        return len(self.cells)

    @property
    def width(self) -> int:
        """How many columns across the picture is."""
        return len(self.cells[0])

    def cell(self, row: int, col: int) -> Cell:
        """The character and style at ``(row, col)``."""
        return self.cells[row][col]

    def char_at(self, row: int, col: int) -> str:
        """The character at ``(row, col)``."""
        return self.cells[row][col].char

    def style_at(self, row: int, col: int) -> str:
        """The style identifier at ``(row, col)``."""
        return self.cells[row][col].style

    def rows(self) -> Tuple[str, ...]:
        """The picture as plain strings, one per row, styles discarded."""
        return tuple("".join(cell.char for cell in row) for row in self.cells)

    def styles(self) -> Tuple[Tuple[str, ...], ...]:
        """The style identifiers as a grid, characters discarded."""
        return tuple(tuple(cell.style for cell in row) for row in self.cells)

    def text(self) -> str:
        """The picture as one newline-joined block of text."""
        return "\n".join(self.rows())


class FrameBuilder:
    """A scratch pad for composing a :class:`Frame`.

    It is mutable on purpose and is meant to live inside a single pure
    function: fill it in, call :meth:`build`, and let it go. Nothing outside
    that function ever sees it, so the core stays immutable at its seams.
    """

    def __init__(
        self,
        height: int = SCREEN_ROWS,
        width: int = SCREEN_COLS,
        char: str = " ",
        style: str = STYLE_DEFAULT,
    ) -> None:
        if height < 1 or width < 1:
            raise ValueError("a frame needs at least one cell")
        if len(char) != 1:
            raise ValueError("the fill must be exactly one character")
        self.height = height
        self.width = width
        self._cells = [[Cell(char, style) for _ in range(width)] for _ in range(height)]

    def put(self, row: int, col: int, char: str, style: str = STYLE_DEFAULT) -> "FrameBuilder":
        """Write one character at ``(row, col)``. Returns ``self``."""
        if len(char) != 1:
            raise ValueError("put writes exactly one character, got %r" % (char,))
        if not (0 <= row < self.height and 0 <= col < self.width):
            raise IndexError("(%d, %d) is outside the %d x %d frame"
                             % (row, col, self.height, self.width))
        self._cells[row][col] = Cell(char, style)
        return self

    def put_text(self, row: int, col: int, text: str, style: str = STYLE_DEFAULT) -> "FrameBuilder":
        """Write ``text`` rightwards from ``(row, col)``. Returns ``self``.

        Raises rather than clipping if the text would run off the row: a
        picture that does not fit is a bug, not something to hide.
        """
        if col < 0 or row < 0 or row >= self.height or col + len(text) > self.width:
            raise IndexError(
                "%r at (%d, %d) does not fit in the %d x %d frame"
                % (text, row, col, self.height, self.width)
            )
        for offset, ch in enumerate(text):
            self._cells[row][col + offset] = Cell(ch, style)
        return self

    def build(self) -> Frame:
        """The finished, immutable picture."""
        return Frame(tuple(tuple(row) for row in self._cells))


def frame_from_rows(
    rows: Iterable[str], style: str = STYLE_DEFAULT, styles: Optional[Iterable[Iterable[str]]] = None
) -> Frame:
    """A :class:`Frame` from plain strings — handy in tests and fixtures."""
    text_rows = tuple(rows)
    if styles is None:
        return Frame(
            tuple(tuple(Cell(ch, style) for ch in row) for row in text_rows)
        )
    style_rows = tuple(tuple(s) for s in styles)
    if len(style_rows) != len(text_rows):
        raise ValueError("one style row is needed per text row")
    return Frame(
        tuple(
            tuple(Cell(ch, st) for ch, st in zip(row, srow))
            for row, srow in zip(text_rows, style_rows)
        )
    )
