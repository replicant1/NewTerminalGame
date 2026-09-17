"""SCRN-3, pinned twice — once by name and once against the picture.

The plan's bar for WI-3 asks for both, and they are not the same test:

* **By name.** Sixteen cases, each written out with the glyph a reader can
  check against the requirement by eye.  This is the human-readable statement
  of SCRN-3, and it is the only place the sixteenth case — the crossing, which
  the specimen picture does not contain — can be pinned at all.
* **Against the picture.** The specimen in ``docs/FUNCTIONAL_REQUIREMENTS.md``
  is normative (assumption P5).  Reading it back and checking every wall square
  in it against the resolver is what stops the named table drifting away from
  the picture it was measured from.  It covers fifteen of the sixteen, over 302
  squares, and it is the test that would catch a table transcribed one row out.

Neither is redundant and neither should be deleted for the other.

There are also two guards, which exist because a test that reads a file can
fail to find anything and still go green: the parse is checked for shape before
it is used, and the set of combinations the specimen covers is asserted
exactly, so that "the specimen covers everything" can never be quietly assumed.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Set, Tuple

import pytest

from terminal_game.presentation.wall_glyphs import (
    ALL_WALL_GLYPHS,
    CORNER_NORTH_EAST,
    CORNER_NORTH_WEST,
    CORNER_SOUTH_EAST,
    CORNER_SOUTH_WEST,
    CROSSING,
    HORIZONTAL,
    LONE_BLOCK,
    TEE_EAST,
    TEE_NORTH,
    TEE_SOUTH,
    TEE_WEST,
    VERTICAL,
    wall_glyph,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIREMENTS = os.path.join(REPO_ROOT, "docs", "FUNCTIONAL_REQUIREMENTS.md")

#: MAZE-1: the grid is 19 squares across and 29 deep.
GRID_COLUMNS = 19
GRID_ROWS = 29

#: Ruling C-2: maze square ``c`` is drawn at screen column ``2c``, so a maze
#: row occupies 37 of the 40 columns.
SCREEN_COLUMNS = 2 * GRID_COLUMNS - 1

#: What a *corridor* square can be drawn as, at the square's own column.  Blank
#: (SCRN-4, a dot already eaten), the dot itself, or an actor.  Deliberately
#: defined without reference to the wall glyphs, so that classifying the
#: specimen does not quietly assume the answer this suite is checking.
CORRIDOR_GLYPHS = frozenset(
    {
        " ",
        "▪",  # SCRN-4, the dim gold dot
        "█",  # SCRN-5, the centre cell of both the player and the ghost
    }
)


# --------------------------------------------------------------------------
# The sixteen cases, by name
# --------------------------------------------------------------------------

#: ``(north, south, east, west) -> glyph``, written out for a reader.  This is
#: the same shape as the module's own table on purpose: the point of the test
#: is that a person can check *these sixteen lines* against SCRN-3 and the
#: picture, which they cannot do with a formula.
SIXTEEN_CASES = [
    ("no wall neighbour at all", False, False, False, False, LONE_BLOCK),
    ("west only", False, False, False, True, HORIZONTAL),
    ("east only", False, False, True, False, HORIZONTAL),
    ("east and west", False, False, True, True, HORIZONTAL),
    ("south only", False, True, False, False, VERTICAL),
    ("south and west", False, True, False, True, CORNER_SOUTH_WEST),
    ("south and east", False, True, True, False, CORNER_SOUTH_EAST),
    ("south, east and west", False, True, True, True, TEE_SOUTH),
    ("north only", True, False, False, False, VERTICAL),
    ("north and west", True, False, False, True, CORNER_NORTH_WEST),
    ("north and east", True, False, True, False, CORNER_NORTH_EAST),
    ("north, east and west", True, False, True, True, TEE_NORTH),
    ("north and south", True, True, False, False, VERTICAL),
    ("north, south and west", True, True, False, True, TEE_WEST),
    ("north, south and east", True, True, True, False, TEE_EAST),
    ("all four", True, True, True, True, CROSSING),
]


@pytest.mark.parametrize(
    "name,north,south,east,west,expected",
    SIXTEEN_CASES,
    ids=[case[0] for case in SIXTEEN_CASES],
)
def test_each_of_the_sixteen_neighbour_combinations_names_its_glyph(
    name: str, north: bool, south: bool, east: bool, west: bool, expected: str
) -> None:
    """SCRN-3, case by case.

    The lone-block case is the first one and it is the only answer that is not
    a box-drawing character, which is what SCRN-3 asks for: *"a wall square
    with no wall next to it is drawn as a single blue block."*
    """
    assert wall_glyph(north=north, south=south, east=east, west=west) == expected


def test_the_sixteen_cases_are_sixteen_distinct_inputs() -> None:
    """A guard on the table above, not on the code.

    A duplicated or missing line in ``SIXTEEN_CASES`` would silently reduce the
    parametrised test's coverage, and the failure would look like a pass.
    """
    inputs = [case[1:5] for case in SIXTEEN_CASES]
    assert len(inputs) == 16
    assert len(set(inputs)) == 16


def test_a_single_wall_neighbour_draws_the_full_line_and_not_a_stub() -> None:
    """Measured from the specimen: 37 squares with one neighbour, no stubs.

    North-only and south-only are both the full vertical, east-only and
    west-only both the full horizontal.  Reaching for ``╨ ╥ ╞ ╡`` is the
    obvious wrong guess and the picture rules it out.
    """
    assert wall_glyph(north=True, south=False, east=False, west=False) == VERTICAL
    assert wall_glyph(north=False, south=True, east=False, west=False) == VERTICAL
    assert wall_glyph(north=False, south=False, east=True, west=False) == HORIZONTAL
    assert wall_glyph(north=False, south=False, east=False, west=True) == HORIZONTAL


# --------------------------------------------------------------------------
# Against the specimen picture
# --------------------------------------------------------------------------


def _specimen_maze_rows() -> List[str]:
    """The 29 maze rows of the specimen picture, as they are printed.

    Raises rather than returning something empty: a test that reads a file and
    finds nothing must fail loudly, not pass on an empty loop.
    """
    with open(REQUIREMENTS, encoding="utf-8") as handle:
        text = handle.read()
    marker = "A game in progress looks like this:"
    if marker not in text:
        raise AssertionError(
            "{} no longer contains {!r}, so the specimen picture cannot be "
            "found. SCRN-3 is pinned against that picture (assumption P5); "
            "fix the locator here rather than deleting the test.".format(
                REQUIREMENTS, marker
            )
        )
    fenced = text.split(marker, 1)[1].split("```")[1]
    # Rows carry a trailing annotation such as "   ← the player".
    rows = [
        re.split(r"\s{3,}←", line)[0]
        for line in fenced.split("\n")
        if line.strip()
    ]
    return rows[:GRID_ROWS]


def _specimen_grid() -> List[List[str]]:
    """The specimen as 29 x 19 squares, one glyph each, at screen column ``2c``."""
    rows = _specimen_maze_rows()
    return [
        [rows[r][2 * c] for c in range(GRID_COLUMNS)] for r in range(GRID_ROWS)
    ]


def test_the_specimen_parses_to_the_shape_the_requirements_describe() -> None:
    """The guard that stops every test below from passing on nothing.

    MAZE-1 and ruling C-2 together say 29 rows of 37 columns; if the parse
    yields anything else, the comparisons below would be checking a handful of
    squares, or none, and would still go green.
    """
    rows = _specimen_maze_rows()
    assert len(rows) == GRID_ROWS
    assert {len(row) for row in rows} == {SCREEN_COLUMNS}


def test_every_specimen_square_is_either_a_wall_glyph_or_a_corridor_glyph() -> None:
    """The two classifications partition the grid, with neither empty.

    Without this, an unrecognised glyph — a specimen redrawn with a different
    dot, say — would be silently classified as corridor and the wall comparison
    would quietly shrink.
    """
    glyphs = {glyph for row in _specimen_grid() for glyph in row}
    walls = glyphs & ALL_WALL_GLYPHS
    corridors = glyphs & CORRIDOR_GLYPHS
    assert not (walls & corridors)
    assert glyphs == walls | corridors, "unclassified glyphs: {}".format(
        sorted(glyphs - walls - corridors)
    )
    assert walls and corridors


def _specimen_wall_cases() -> Dict[Tuple[bool, bool, bool, bool], Set[str]]:
    """Every wall square in the specimen, grouped by its four neighbours.

    A neighbour outside the grid is not a wall — the border corners are the
    evidence, and :func:`test_the_border_corners_show_that_outside_is_not_a_wall`
    is where that is pinned.
    """
    grid = _specimen_grid()

    def is_wall(column: int, row: int) -> bool:
        if not (0 <= column < GRID_COLUMNS and 0 <= row < GRID_ROWS):
            return False
        return grid[row][column] not in CORRIDOR_GLYPHS

    cases = {}  # type: Dict[Tuple[bool, bool, bool, bool], Set[str]]
    for row in range(GRID_ROWS):
        for column in range(GRID_COLUMNS):
            if not is_wall(column, row):
                continue
            key = (
                is_wall(column, row - 1),
                is_wall(column, row + 1),
                is_wall(column + 1, row),
                is_wall(column - 1, row),
            )
            cases.setdefault(key, set()).add(grid[row][column])
    return cases


def test_the_resolver_draws_every_wall_square_of_the_specimen_as_the_specimen_does() -> None:
    """The comparison the plan asks for, over all 302 wall squares.

    This is the test that fails if the table is transcribed wrongly anywhere —
    a swapped corner, a tee facing the wrong way, a row read one out.
    """
    cases = _specimen_wall_cases()
    wrong = []  # type: List[str]
    for (north, south, east, west), drawn in sorted(cases.items()):
        ours = wall_glyph(north=north, south=south, east=east, west=west)
        if drawn != {ours}:
            wrong.append(
                "N={} S={} E={} W={}: specimen draws {}, resolver says {!r}".format(
                    north, south, east, west, sorted(drawn), ours
                )
            )
    assert not wrong, "\n".join(wrong)


def test_each_neighbour_combination_is_drawn_one_way_throughout_the_specimen() -> None:
    """SCRN-3 is a function of the four neighbours and of nothing else.

    If any combination appeared with two different glyphs, no table over four
    booleans could reproduce the picture and WI-3 would be the wrong shape.
    Measured: every combination present is drawn exactly one way.
    """
    ambiguous = {
        key: sorted(drawn)
        for key, drawn in _specimen_wall_cases().items()
        if len(drawn) > 1
    }
    assert not ambiguous, "combinations drawn more than one way: {}".format(ambiguous)


def test_the_specimen_covers_fifteen_cases_and_the_crossing_is_the_missing_one() -> None:
    """Exactly which case is *not* evidence, stated so nobody assumes otherwise.

    The crossing ``╬`` is derived from the double-line family rather than
    observed. If a future specimen contains one, this test fails — and the
    right response is to measure it and relax this assertion, not to delete it.
    """
    covered = set(_specimen_wall_cases())
    every = {
        (north, south, east, west)
        for north in (False, True)
        for south in (False, True)
        for east in (False, True)
        for west in (False, True)
    }
    assert every - covered == {(True, True, True, True)}
    assert len(covered) == 15


def test_the_border_corners_show_that_outside_the_grid_is_not_a_wall() -> None:
    """The measurement behind the resolver's edge convention.

    MAZE-3 makes every border square a wall, so the top-left square has wall
    neighbours to the south and east and nothing to the north or west. The
    specimen draws it ``╔`` — the south-and-east corner. Had "outside" counted
    as a wall it would have had to be ``╬``, and all four corners agree.
    """
    grid = _specimen_grid()
    assert grid[0][0] == CORNER_SOUTH_EAST
    assert grid[0][GRID_COLUMNS - 1] == CORNER_SOUTH_WEST
    assert grid[GRID_ROWS - 1][0] == CORNER_NORTH_EAST
    assert grid[GRID_ROWS - 1][GRID_COLUMNS - 1] == CORNER_NORTH_WEST

    assert wall_glyph(north=False, south=True, east=True, west=False) == grid[0][0]
    assert (
        wall_glyph(north=True, south=False, east=False, west=True)
        == grid[GRID_ROWS - 1][GRID_COLUMNS - 1]
    )


def test_the_lone_block_appears_in_the_specimen_where_the_requirement_says() -> None:
    """SCRN-3's lone block, found in the picture rather than assumed.

    The requirement annotates one of them — *"← a lone wall square"* — and the
    picture contains two. Both must be squares with no wall neighbour at all.
    """
    cases = _specimen_wall_cases()
    assert cases[(False, False, False, False)] == {LONE_BLOCK}

    grid = _specimen_grid()
    lone = [
        (column, row)
        for row in range(GRID_ROWS)
        for column in range(GRID_COLUMNS)
        if grid[row][column] == LONE_BLOCK
    ]
    assert len(lone) == 2
