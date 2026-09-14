"""The screen port: a character-cell surface, a whole frame, and a key.

Nothing in this module knows that `curses` exists, or that a terminal exists.
It is the vocabulary the rest of the game speaks when it wants to put
something on the screen or find out what the player pressed. The one
implementation that talks to a real terminal lives in `curses_adapter`.

Three operations, and only three (implementation plan, M0 / WI-2):

* put a cell into a frame,
* present a whole frame in one pass,
* read a key with a timeout.

The timeout is a parameter rather than a constant because WI-11 recomputes it
on every pass of the game loop, as the time remaining until the next ghost
tick (architecture caution C7).
"""

from __future__ import annotations

import abc
from typing import Iterator, List, Optional, Tuple

# The window the launcher creates is 40 x 30 (WIN-2), and the picture is
# composed to exactly that: 29 rows of maze and one status row (SCRN-1). A
# terminal smaller than this cannot show the picture, so the game refuses to
# draw a truncated one.
REQUIRED_WIDTH = 40
REQUIRED_HEIGHT = 30

BLANK = " "


class ScreenTooSmall(RuntimeError):
    """The terminal is smaller than the picture the game must draw.

    Raised loudly rather than drawing a truncated picture. The terminal is
    always restored before this leaves the session.
    """

    def __init__(self, actual_width, actual_height,
                 required_width=REQUIRED_WIDTH, required_height=REQUIRED_HEIGHT):
        self.actual_width = actual_width
        self.actual_height = actual_height
        self.required_width = required_width
        self.required_height = required_height
        super().__init__(
            "This game needs a terminal of at least {0} columns by {1} rows; "
            "this one is {2} by {3}. Make the window bigger and run it again."
            .format(required_width, required_height, actual_width, actual_height)
        )


class Colour:
    """The colours the specification names, as names rather than as numbers.

    Presentation asks for `Colour.WALL`; only the terminal adapter knows that
    that means a curses colour pair with blue on black. Keeping the numbers
    out of here is what stops curses leaking above the port.
    """

    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Colour.{0}".format(self.name.upper())

    def __eq__(self, other):
        return isinstance(other, Colour) and other.name == self.name

    def __hash__(self):
        return hash(("Colour", self.name))


def _colour(name):
    return Colour(name)


#: Whatever the terminal's own foreground is. Used for blanks and margins.
Colour.DEFAULT = _colour("default")
#: SCRN-3 — the blue double-line walls.
Colour.WALL = _colour("wall")
#: SCRN-4 — a dim gold dot.
Colour.DOT = _colour("dot")
#: SCRN-5 — the bright yellow player.
Colour.PLAYER = _colour("player")
#: SCRN-5 — the pink ghost.
Colour.GHOST = _colour("ghost")
#: SCRN-6 — the cyan status line.
Colour.STATUS = _colour("status")

ALL_COLOURS = (
    Colour.DEFAULT,
    Colour.WALL,
    Colour.DOT,
    Colour.PLAYER,
    Colour.GHOST,
    Colour.STATUS,
)


class Cell(object):
    """One character cell: what is there, and what colour it is."""

    __slots__ = ("character", "colour")

    def __init__(self, character, colour):
        self.character = character
        self.colour = colour

    def __eq__(self, other):
        return (isinstance(other, Cell)
                and other.character == self.character
                and other.colour == self.colour)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.character, self.colour))

    def __repr__(self):
        return "Cell({0!r}, {1!r})".format(self.character, self.colour)


class Frame(object):
    """A whole picture, composed off-screen, presented in one go.

    A frame is built cell by cell and then handed to `Screen.present` as a
    unit. Nothing ever presents a half-built frame, and nothing presents a
    single cell: that is what keeps SCRN-7's "without flicker" true, and it is
    why a dirty-cell optimisation has nowhere to live (caution C9).
    """

    __slots__ = ("_width", "_height", "_cells")

    def __init__(self, width, height, character=BLANK, colour=None):
        if width <= 0 or height <= 0:
            raise ValueError(
                "A frame needs a positive width and height; got {0} x {1}."
                .format(width, height))
        _check_single_character(character)
        if colour is None:
            colour = Colour.DEFAULT
        self._width = width
        self._height = height
        self._cells = [[Cell(character, colour) for _ in range(width)]
                       for _ in range(height)]

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def put(self, column, row, character, colour=None):
        """Put one character, in one colour, at one cell.

        Out-of-range coordinates raise rather than being silently clipped or,
        worse, wrapping round the way a negative Python index would.
        """
        _check_single_character(character)
        self._check_bounds(column, row)
        if colour is None:
            colour = Colour.DEFAULT
        self._cells[row][column] = Cell(character, colour)

    def put_text(self, column, row, text, colour=None):
        """Put a run of characters left to right from `column`, on one row."""
        if not isinstance(text, str):
            raise TypeError("put_text needs a string, got {0!r}.".format(text))
        for offset, character in enumerate(text):
            self.put(column + offset, row, character, colour)

    def cell(self, column, row):
        self._check_bounds(column, row)
        return self._cells[row][column]

    def cells(self):
        # type: () -> Iterator[Tuple[int, int, Cell]]
        """Every cell, in reading order. Every one, every time."""
        for row in range(self._height):
            for column in range(self._width):
                yield column, row, self._cells[row][column]

    def row_runs(self, row):
        # type: (int) -> List[Tuple[int, str, Colour]]
        """One row, split into the longest runs that share a colour.

        The whole row is always covered — this groups cells, it never skips
        them. The adapter writes a run at a time because a run is one call to
        the terminal instead of forty, not because anything is being left out.
        """
        if not 0 <= row < self._height:
            raise IndexError("Row {0} is outside a frame {1} rows deep."
                             .format(row, self._height))
        runs = []
        start = 0
        cells = self._cells[row]
        while start < self._width:
            colour = cells[start].colour
            end = start + 1
            while end < self._width and cells[end].colour == colour:
                end += 1
            runs.append((start,
                         "".join(c.character for c in cells[start:end]),
                         colour))
            start = end
        return runs

    def text_rows(self):
        # type: () -> List[str]
        """The frame as plain text, one string per row. Colour discarded."""
        return ["".join(cell.character for cell in row) for row in self._cells]

    def __eq__(self, other):
        return (isinstance(other, Frame)
                and other._width == self._width
                and other._height == self._height
                and other._cells == self._cells)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "Frame({0} x {1})".format(self._width, self._height)

    def _check_bounds(self, column, row):
        if not isinstance(column, int) or not isinstance(row, int):
            raise TypeError("Cell coordinates must be whole numbers; got "
                            "({0!r}, {1!r}).".format(column, row))
        if not 0 <= column < self._width or not 0 <= row < self._height:
            raise IndexError(
                "Cell ({0}, {1}) is outside a frame {2} x {3}."
                .format(column, row, self._width, self._height))


def _check_single_character(character):
    if not isinstance(character, str):
        raise TypeError("A cell holds one character, got {0!r}."
                        .format(character))
    if len(character) != 1:
        raise ValueError("A cell holds exactly one character, got {0!r}."
                         .format(character))


class Key(object):
    """A key the player pressed, named rather than numbered.

    The four arrows are named because a terminal reports them as escape
    sequences that only the adapter should have to know about. Anything the
    player typed arrives as a printable key carrying its character, so `q`
    and `Q` are the adapter's business to report and the game loop's business
    to interpret (CTRL-4). Anything else — a function key, a mouse report —
    arrives as `Key.other`, which the loop discards (CTRL-5).
    """

    __slots__ = ("name", "character", "code")

    def __init__(self, name, character=None, code=None):
        self.name = name
        self.character = character
        self.code = code

    @classmethod
    def printable(cls, character):
        _check_single_character(character)
        return cls("printable", character=character)

    @classmethod
    def other(cls, code):
        return cls("other", code=code)

    @property
    def is_printable(self):
        return self.name == "printable"

    @property
    def is_arrow(self):
        return self.name in ("up", "down", "left", "right")

    def __eq__(self, other):
        return (isinstance(other, Key)
                and other.name == self.name
                and other.character == self.character
                and other.code == self.code)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.name, self.character, self.code))

    def __repr__(self):
        if self.is_printable:
            return "Key.printable({0!r})".format(self.character)
        if self.name == "other":
            return "Key.other({0!r})".format(self.code)
        return "Key.{0}".format(self.name.upper())


Key.UP = Key("up")
Key.DOWN = Key("down")
Key.LEFT = Key("left")
Key.RIGHT = Key("right")

ARROW_KEYS = (Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT)


class Screen(abc.ABC):
    """The port. Three operations and a size.

    Everything above this line — presentation, the game loop, the domain —
    depends on this and never on a terminal.
    """

    @abc.abstractmethod
    def size(self):
        # type: () -> Tuple[int, int]
        """(width, height) in character cells."""

    @abc.abstractmethod
    def new_frame(self):
        # type: () -> Frame
        """A blank frame the size of this screen, ready to compose into."""

    @abc.abstractmethod
    def present(self, frame):
        # type: (Frame) -> None
        """Put the whole frame on the screen, in one visible update.

        Every cell of the frame is written every time. There is no dirty-cell
        path and there must not be one: the actor glyphs are three columns
        wide and overwrite a column of the neighbouring square, so anything
        that skipped unchanged cells would leave debris behind (caution C9).
        """

    @abc.abstractmethod
    def read_key(self, timeout_seconds):
        # type: (float) -> Optional[Key]
        """Wait up to `timeout_seconds` for a key.

        Returns the key as soon as one is available, or `None` if the timeout
        expires with nothing pressed. A timeout of zero polls and returns at
        once; a negative timeout — the tick is already due — is treated as
        zero rather than as "wait forever", because a game loop that blocks
        forever has stopped being a game loop.
        """
