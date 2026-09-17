"""SCRN-3 — which character a wall square is drawn as.

    *"The walls are drawn as blue double lines that join up neatly with their
    neighbours into corners, tees and crossings; a wall square with no wall
    next to it is drawn as a single blue block."*

A wall square's appearance depends on nothing but whether each of its four
orthogonal grid neighbours is also a wall.  Four booleans, sixteen
combinations, sixteen answers — which is why WI-3 does not wait for WI-1 and
why there is nothing impure anywhere in this module.

**Where the table came from.**  Fifteen of the sixteen were *measured*, not
recalled: the specimen picture in ``docs/FUNCTIONAL_REQUIREMENTS.md`` was
parsed square by square, each wall square classified by its four neighbours,
and the glyph it is drawn with read off.  Every one of the fifteen occurs with
exactly one glyph across all 19 x 29 squares, so the mapping really is a
function of the four booleans and not of anything else.
``tests/test_wall_glyphs.py`` re-runs that comparison against the specimen on
every suite run, so the table cannot drift away from the picture it came from.

Two things the measurement settled that are easy to guess wrong:

* **A single wall neighbour gets the full line, not a stub.**  North-only and
  south-only are both ``║`` — never ``╨`` or ``╥`` — and east-only and
  west-only are both ``═``, never ``╞`` or ``╡``.  The specimen has 37 such
  squares and not one of them is a stub.
* **Outside the grid is not a wall.**  The border corners prove it: the
  top-left square has no northern and no western neighbour and is drawn ``╔``,
  which is the glyph for *south and east only*.  Had "outside" counted as a
  wall it would have had to be ``╬``.  A caller at the edge therefore passes
  ``False`` for the neighbours that do not exist; MAZE-3's solid border ring
  means every edge square is a wall, so this case is reached constantly.

The sixteenth — all four neighbours walls — **does not occur in the specimen**
and could not be measured.  It is ``╬``, taken from the same double-line family
as the other fifteen, and it is marked as derived wherever it appears so that
nobody later mistakes it for something that was observed.

This module is **Presentation as data**: it returns a character.  It names no
toolkit, no colour and no pixel.  SCRN-3 also calls the walls *blue*; that is
a colour, and colour belongs to the whole-field composition in WI-4 rather
than here.
"""

from __future__ import annotations

from typing import Dict, Tuple

# --------------------------------------------------------------------------
# The glyphs, each named once so that no caller writes a bare escape.
# --------------------------------------------------------------------------

#: U+25A0 BLACK SQUARE — a wall square with no wall neighbour at all.  SCRN-3
#: calls it "a single blue block".  It is not a box-drawing character, which is
#: the point: there is nothing for it to join up to.
LONE_BLOCK = "■"

#: U+2550 BOX DRAWINGS DOUBLE HORIZONTAL — east and/or west, and nothing else.
HORIZONTAL = "═"

#: U+2551 BOX DRAWINGS DOUBLE VERTICAL — north and/or south, and nothing else.
VERTICAL = "║"

#: U+2554 BOX DRAWINGS DOUBLE DOWN AND RIGHT — the corner opening south-east.
CORNER_SOUTH_EAST = "╔"

#: U+2557 BOX DRAWINGS DOUBLE DOWN AND LEFT — the corner opening south-west.
CORNER_SOUTH_WEST = "╗"

#: U+255A BOX DRAWINGS DOUBLE UP AND RIGHT — the corner opening north-east.
CORNER_NORTH_EAST = "╚"

#: U+255D BOX DRAWINGS DOUBLE UP AND LEFT — the corner opening north-west.
CORNER_NORTH_WEST = "╝"

#: U+2560 BOX DRAWINGS DOUBLE VERTICAL AND RIGHT — a tee with its stem east.
TEE_EAST = "╠"

#: U+2563 BOX DRAWINGS DOUBLE VERTICAL AND LEFT — a tee with its stem west.
TEE_WEST = "╣"

#: U+2566 BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL — a tee with its stem south.
TEE_SOUTH = "╦"

#: U+2569 BOX DRAWINGS DOUBLE UP AND HORIZONTAL — a tee with its stem north.
TEE_NORTH = "╩"

#: U+256C BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL — all four.  **Derived,
#: not observed:** this is the one combination the specimen picture does not
#: contain.  See the module docstring.
CROSSING = "╬"

#: Every glyph this module can return, for a caller that needs the alphabet
#: rather than one answer — WI-5's font check wants exactly this set.
ALL_WALL_GLYPHS = frozenset(
    {
        LONE_BLOCK,
        HORIZONTAL,
        VERTICAL,
        CORNER_SOUTH_EAST,
        CORNER_SOUTH_WEST,
        CORNER_NORTH_EAST,
        CORNER_NORTH_WEST,
        TEE_EAST,
        TEE_WEST,
        TEE_SOUTH,
        TEE_NORTH,
        CROSSING,
    }
)

# --------------------------------------------------------------------------
# The sixteen cases, written out.
# --------------------------------------------------------------------------

#: Key order is ``(north, south, east, west)``.  All sixteen are present and
#: each is written out rather than computed, because the table *is* the
#: specification of SCRN-3 — a reader should be able to check it against the
#: picture without running anything.
_TABLE = {
    #  N      S      E      W
    (False, False, False, False): LONE_BLOCK,
    (False, False, False, True): HORIZONTAL,
    (False, False, True, False): HORIZONTAL,
    (False, False, True, True): HORIZONTAL,
    (False, True, False, False): VERTICAL,
    (False, True, False, True): CORNER_SOUTH_WEST,
    (False, True, True, False): CORNER_SOUTH_EAST,
    (False, True, True, True): TEE_SOUTH,
    (True, False, False, False): VERTICAL,
    (True, False, False, True): CORNER_NORTH_WEST,
    (True, False, True, False): CORNER_NORTH_EAST,
    (True, False, True, True): TEE_NORTH,
    (True, True, False, False): VERTICAL,
    (True, True, False, True): TEE_WEST,
    (True, True, True, False): TEE_EAST,
    (True, True, True, True): CROSSING,
}  # type: Dict[Tuple[bool, bool, bool, bool], str]


def wall_glyph(north: bool, south: bool, east: bool, west: bool) -> str:
    """The character a wall square is drawn as, given its four neighbours.

    Each argument says whether the neighbour in that direction is **also a
    wall**.  A neighbour that lies outside the grid is not a wall, so an edge
    square passes ``False`` for it — see the module docstring for the evidence.

    :param north: the square above is a wall.
    :param south: the square below is a wall.
    :param east: the square to the right is a wall.
    :param west: the square to the left is a wall.
    :returns: one character from :data:`ALL_WALL_GLYPHS`.

    >>> wall_glyph(north=False, south=True, east=True, west=False)
    '╔'
    >>> wall_glyph(north=False, south=False, east=False, west=False)
    '■'
    """
    return _TABLE[(bool(north), bool(south), bool(east), bool(west))]
