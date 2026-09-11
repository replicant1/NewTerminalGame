# -*- coding: utf-8 -*-
"""Glyph and colour tables — SCRN-3, SCRN-4, SCRN-5, SCRN-6.

This module is part of the pure core. It imports nothing impure and, in
particular, **it does not import curses** (plan §2.4, architecture C6). What
it publishes instead is a *style identifier* — a plain string — for each
colour-and-attribute the specification names, and a table saying what colour
and what attributes that identifier stands for. The curses adapter is the
only thing in the project that turns one of those into a colour pair.

The wall glyph rule
-------------------

A wall cell's glyph is a pure function of a four-bit mask of which of its
north / south / east / west **cell**-neighbours are also wall:

======  ====  =========================================================
bit     name  meaning
======  ====  =========================================================
1       N     the cell one row up is wall
2       S     the cell one row down is wall
4       E     the cell one column right is wall
8       W     the cell one column left is wall
======  ====  =========================================================

A neighbour that falls **outside** the grid is *not* wall. That is not a
detail: the maze's border cells rely on it, and it is why the top-left corner
of the mock-up is ``╔`` (south and east only) rather than a crossing.

Fifteen of the sixteen entries in :data:`WALL_GLYPHS` were read directly off
the specification's mock-up, and every one of those fifteen is unambiguous —
every wall cell in the mock-up sharing a mask also shares a glyph, with no
exceptions. The sixteenth, ``N | S | E | W``, does not occur in the mock-up
at all and is the one inferred entry: a crossing, ``╬``.

The joiner columns
------------------

The picture is twice as wide as the maze. Even picture column ``2c`` carries
maze column ``c``; odd column ``2c + 1`` is a *joiner*, and holds a
horizontal bar if and only if the cells on both sides of it are wall. That
rule, decoded from the mock-up, has no exceptions either — and it is what
makes the three-character player and ghost safe, because a joiner beside a
corridor cell is always blank.
"""

from typing import Dict, Tuple

from termgame.model import STYLE_DEFAULT, Maze, Outcome, Position

# --------------------------------------------------------------------------
# The neighbour mask
# --------------------------------------------------------------------------

#: The cell one row up is wall.
NORTH = 1
#: The cell one row down is wall.
SOUTH = 2
#: The cell one column right is wall.
EAST = 4
#: The cell one column left is wall.
WEST = 8

#: The four mask bits with the ``(dr, dc)`` step each one asks about, in a
#: fixed order so that the mask is reproducible.
MASK_BITS: Tuple[Tuple[int, int, int], ...] = (
    (NORTH, -1, 0),
    (SOUTH, 1, 0),
    (EAST, 0, 1),
    (WEST, 0, -1),
)

#: Every mask, 0 to 15.
ALL_MASKS: Tuple[int, ...] = tuple(range(16))


def mask_name(mask: int) -> str:
    """A readable name for a mask, e.g. ``'NS-W'`` — for test messages."""
    return "".join(
        letter if mask & bit else "-"
        for letter, bit in (("N", NORTH), ("S", SOUTH), ("E", EAST), ("W", WEST))
    )


# --------------------------------------------------------------------------
# Glyphs
# --------------------------------------------------------------------------

#: A wall cell's glyph, indexed by its neighbour mask (SCRN-3). Read off the
#: specification's mock-up for masks 0..14; mask 15 is inferred.
WALL_GLYPHS: Tuple[str, ...] = (
    u"■",  #  0  ----  a lone wall square, no wall next to it
    u"║",  #  1  N---  vertical
    u"║",  #  2  -S--  vertical
    u"║",  #  3  NS--  vertical
    u"═",  #  4  --E-  horizontal
    u"╚",  #  5  N-E-  bottom-left corner
    u"╔",  #  6  -SE-  top-left corner
    u"╠",  #  7  NSE-  tee pointing east
    u"═",  #  8  ---W  horizontal
    u"╝",  #  9  N--W  bottom-right corner
    u"╗",  # 10  -S-W  top-right corner
    u"╣",  # 11  NS-W  tee pointing west
    u"═",  # 12  --EW  horizontal
    u"╩",  # 13  N-EW  tee pointing north
    u"╦",  # 14  -SEW  tee pointing south
    u"╬",  # 15  NSEW  crossing -- INFERRED, absent from the mock-up
)

#: The mask that does not occur in the specification's mock-up. Named so the
#: tests can say out loud which entry is the inferred one.
INFERRED_MASK = NORTH | SOUTH | EAST | WEST

#: The bar that fills a joiner column between two wall cells (SCRN-3).
JOINER_GLYPH = u"═"

#: A dot — one to a corridor square (SCRN-4).
DOT_GLYPH = u"▪"

#: The player, three characters wide and centred on its cell (SCRN-5).
PLAYER_GLYPHS = (u"▐", u"█", u"▌")  # ``▐█▌``

#: The ghost, three characters wide, a different outline (SCRN-5).
GHOST_GLYPHS = (u"▗", u"█", u"▖")  # ``▗█▖``

#: What an unclaimed picture cell holds.
BLANK_GLYPH = u" "

#: Every glyph any wall cell or joiner can carry.
WALL_ALPHABET = frozenset(WALL_GLYPHS) | {JOINER_GLYPH}


# --------------------------------------------------------------------------
# Style identifiers
# --------------------------------------------------------------------------

#: Blue double lines (SCRN-3).
STYLE_WALL = "wall"
#: A small dim gold square (SCRN-4).
STYLE_DOT = "dot"
#: A bright yellow block (SCRN-5).
STYLE_PLAYER = "player"
#: A pink block (SCRN-5).
STYLE_GHOST = "ghost"
#: The status line, in cyan (SCRN-6).
STYLE_STATUS = "status"


class Style(object):
    """What a style identifier stands for, in terms nothing curses-shaped.

    ``colour`` is a 256-colour index (the architecture measured ``COLORS`` at
    256 on this machine). ``attributes`` is a tuple of plain names — at
    present ``"bold"`` and ``"dim"`` are the only two used. The curses
    adapter maps a name to ``A_BOLD`` / ``A_DIM``; **this module must never
    name a curses constant**, or the picture stops being comparable without a
    terminal attached.
    """

    __slots__ = ("name", "colour", "attributes", "description")

    def __init__(self, name, colour, attributes=(), description=""):
        # type: (str, int, Tuple[str, ...], str) -> None
        self.name = name
        self.colour = colour
        self.attributes = tuple(attributes)
        self.description = description

    def __repr__(self):  # pragma: no cover - debugging convenience
        return "Style(%r, %r, %r)" % (self.name, self.colour, self.attributes)

    def __eq__(self, other):
        if not isinstance(other, Style):
            return NotImplemented
        return (
            self.name == other.name
            and self.colour == other.colour
            and self.attributes == other.attributes
        )

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        return hash((self.name, self.colour, self.attributes))


#: Bold and dim, as names rather than curses attributes.
ATTR_BOLD = "bold"
ATTR_DIM = "dim"

#: The colour a plain unclaimed cell takes: the terminal's own foreground.
DEFAULT_COLOUR = 7

#: Every style the picture can carry, by identifier. The curses adapter
#: allocates one colour pair per entry.
STYLES: Dict[str, Style] = {
    STYLE_DEFAULT: Style(STYLE_DEFAULT, DEFAULT_COLOUR, (), "unclaimed background"),
    STYLE_WALL: Style(STYLE_WALL, 33, (), "blue double lines (SCRN-3)"),
    STYLE_DOT: Style(STYLE_DOT, 178, (ATTR_DIM,), "dim gold dot (SCRN-4)"),
    STYLE_PLAYER: Style(STYLE_PLAYER, 226, (ATTR_BOLD,), "bright yellow player (SCRN-5)"),
    STYLE_GHOST: Style(STYLE_GHOST, 213, (), "pink ghost (SCRN-5)"),
    STYLE_STATUS: Style(STYLE_STATUS, 51, (), "cyan status line (SCRN-6)"),
}

#: The style identifiers, in a fixed order. The adapter may rely on this
#: ordering to number its colour pairs.
STYLE_NAMES: Tuple[str, ...] = (
    STYLE_DEFAULT,
    STYLE_WALL,
    STYLE_DOT,
    STYLE_PLAYER,
    STYLE_GHOST,
    STYLE_STATUS,
)

#: The attribute names the adapter has to understand, and nothing else.
ATTRIBUTE_NAMES: Tuple[str, ...] = (ATTR_BOLD, ATTR_DIM)


# --------------------------------------------------------------------------
# The wall glyph rule
# --------------------------------------------------------------------------


def neighbour_is_wall(maze: Maze, row: int, col: int) -> bool:
    """Whether cell ``(row, col)`` counts as wall *for the glyph rule*.

    A cell outside the grid is **not** wall here, which is the opposite of
    :meth:`termgame.model.Maze.is_wall`. The difference is deliberate and it
    matters: the maze's own border would otherwise draw itself as crossings
    joining on to something that is not there.
    """
    if not maze.contains((row, col)):
        return False
    return maze.is_wall((row, col))


def wall_mask(maze: Maze, position: Position) -> int:
    """The four-bit neighbour mask of the wall cell at ``position``."""
    row, col = position
    mask = 0
    for bit, dr, dc in MASK_BITS:
        if neighbour_is_wall(maze, row + dr, col + dc):
            mask |= bit
    return mask


def wall_glyph(maze: Maze, position: Position) -> str:
    """The glyph a wall cell is drawn with (SCRN-3)."""
    return WALL_GLYPHS[wall_mask(maze, position)]


def glyph_for_mask(mask: int) -> str:
    """The glyph for a neighbour mask, checked."""
    if not 0 <= mask <= 15:
        raise ValueError("a neighbour mask is four bits, got %r" % (mask,))
    return WALL_GLYPHS[mask]


def joins_horizontally(maze: Maze, row: int, col: int) -> bool:
    """Whether the joiner column right of maze column ``col`` carries a bar.

    True exactly when the cells on both sides of it are wall. Blank
    otherwise — including beside a corridor cell, which is what lets the
    three-character player and ghost spill into a joiner safely.
    """
    return neighbour_is_wall(maze, row, col) and neighbour_is_wall(maze, row, col + 1)


def joiner_glyph(maze: Maze, row: int, col: int) -> str:
    """The character the joiner column right of ``(row, col)`` carries."""
    return JOINER_GLYPH if joins_horizontally(maze, row, col) else BLANK_GLYPH


# --------------------------------------------------------------------------
# The status line — STAT-1, STAT-2, STAT-3
# --------------------------------------------------------------------------

#: The specification's three quoted strings, verbatim. The score is the only
#: thing substituted, and nothing else appears on the row (STAT-1).
STATUS_TEMPLATES: Dict[Outcome, str] = {
    Outcome.PLAYING: "score %d    arrows, q quits",
    Outcome.CAUGHT: "CAUGHT  score %d   q quits",
    Outcome.CLEARED: "CLEARED  score %d  q quits",
}

#: How far in from the left edge the status line starts.
#:
#: **Assumption A3, not a ruling.** The specification's two end-of-game
#: examples do not align with each other — ``q quits`` begins at offset 19 in
#: ``CAUGHT  score 37   q quits`` and at offset 20 in
#: ``CLEARED  score 274  q quits`` — and the mock-up shows a leading blank
#: column that neither quoted string contains. We reproduce all three strings
#: verbatim and indent each by one column, which satisfies both the quotes
#: and the picture. If the user answers A3 differently, this constant and the
#: templates above are the whole of the change.
STATUS_INDENT = 1


def status_text(outcome: Outcome, score: int) -> str:
    """The status line's text for an outcome and a score, without its indent.

    STAT-2 during play, STAT-3 at either ending — so the line says which of
    the two endings happened and what the final score was. SCORE-5's "the
    score is shown" is this function.
    """
    try:
        template = STATUS_TEMPLATES[outcome]
    except KeyError:
        raise ValueError("no status line for outcome %r" % (outcome,))
    return template % (score,)
