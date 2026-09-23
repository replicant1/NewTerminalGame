"""WI-4: wall glyphs (SCRN-3)."""

from __future__ import annotations

import itertools

import pytest

import specimen
from terminal_game.presentation import wall_glyphs
from terminal_game.presentation.wall_glyphs import (joining_cell, joining_glyph,
                                                    square_glyph, wall_glyph)

# WI-4/C1, transcribed from the plan: (north, south, east, west) -> character.
N, S, E, W = "north", "south", "east", "west"
EXPECTED = {
    frozenset(): "■",
    frozenset({E}): "═", frozenset({W}): "═", frozenset({E, W}): "═",
    frozenset({N}): "║", frozenset({S}): "║", frozenset({N, S}): "║",
    frozenset({S, E}): "╔",
    frozenset({S, W}): "╗",
    frozenset({N, E}): "╚",
    frozenset({N, W}): "╝",
    frozenset({N, S, E}): "╠",
    frozenset({N, S, W}): "╣",
    frozenset({E, W, S}): "╦",
    frozenset({E, W, N}): "╩",
    frozenset({N, S, E, W}): "╬",
}

ALL_COMBINATIONS = list(itertools.product([False, True], repeat=4))


def test_the_plan_table_covers_all_sixteen_combinations():
    assert len(EXPECTED) == 16


@pytest.mark.parametrize("north, south, east, west", ALL_COMBINATIONS)
def test_c1_a_wall_square_gets_its_character_from_its_wall_neighbours(north, south, east, west):
    walls = frozenset(name for name, on in zip((N, S, E, W), (north, south, east, west)) if on)
    assert wall_glyph(north, south, east, west) == EXPECTED[walls]


@pytest.mark.parametrize("west, east, expected", [
    (True, True, "═"), (True, False, " "), (False, True, " "), (False, False, " "),
])
def test_c2_the_joining_cell_is_a_double_line_only_between_two_walls(west, east, expected):
    assert joining_glyph(west, east) == expected


def _grid(picture):
    """A wall predicate from rows of '#' (wall) and '.' (corridor)."""
    return (lambda col, row: picture[row][col] == "#"), len(picture[0]), len(picture)


def test_c3_squares_beyond_the_edge_count_as_not_wall_so_corners_close():
    is_wall, width, height = _grid(["###", "#.#", "###"])
    assert square_glyph(is_wall, width, height, 0, 0) == "╔"
    assert square_glyph(is_wall, width, height, 2, 0) == "╗"
    assert square_glyph(is_wall, width, height, 0, 2) == "╚"
    assert square_glyph(is_wall, width, height, 2, 2) == "╝"


def test_c3_the_edge_is_the_grid_edge_even_if_the_predicate_says_otherwise():
    """A predicate that calls everything wall still gets closed corners at the edge."""
    everywhere = lambda col, row: True  # noqa: E731
    assert square_glyph(everywhere, 3, 3, 0, 0) == "╔"
    assert square_glyph(everywhere, 3, 3, 2, 2) == "╝"
    assert square_glyph(everywhere, 3, 3, 1, 1) == "╬"
    assert joining_cell(everywhere, 3, 3, 2, 0) == " ", "no square east of the last column"


def test_a_lone_wall_square_is_a_block():
    is_wall, width, height = _grid([".....", "..#..", "....."])
    assert square_glyph(is_wall, width, height, 2, 1) == "■"


# --------------------------------------------------------------------------
# WI-4/C4: the specimen, reproduced
# --------------------------------------------------------------------------

#: Characters the composer draws over the maze for the player and the ghost.
SPRITE_PARTS = set("▐█▌▗▖")

#: The wall characters, written out from the plan's WI-4/C1 table rather than
#: taken from the module, so that deciding which specimen squares are wall does
#: not lean on the code under test.
PLAN_WALL_CHARACTERS = set("■═║╔╗╚╝╠╣╦╩╬")


def test_every_non_wall_square_in_the_specimen_is_a_dot_or_the_player():
    """So no wall character is missing from the set used to classify squares."""
    maze = specimen.maze_rows()
    others = {maze[r][2 * c] for r in range(specimen.MAZE_HEIGHT) for c in range(specimen.MAZE_WIDTH)
              if maze[r][2 * c] not in PLAN_WALL_CHARACTERS}
    assert others == {"▪", "█"}  # a dot on every corridor square but the player's


def test_the_module_draws_exactly_the_plans_wall_characters():
    assert wall_glyphs.WALL_CHARACTERS == PLAN_WALL_CHARACTERS


def _specimen_walls():
    maze = specimen.maze_rows()
    walls = [[maze[row][2 * col] in PLAN_WALL_CHARACTERS
              for col in range(specimen.MAZE_WIDTH)] for row in range(specimen.MAZE_HEIGHT)]
    return maze, (lambda col, row: walls[row][col])


def test_c4_every_wall_square_in_the_specimen_comes_out_as_drawn():
    maze, is_wall = _specimen_walls()
    checked, wrong = 0, []
    for row in range(specimen.MAZE_HEIGHT):
        for col in range(specimen.MAZE_WIDTH):
            if not is_wall(col, row):
                continue
            checked += 1
            got = square_glyph(is_wall, specimen.MAZE_WIDTH, specimen.MAZE_HEIGHT, col, row)
            if got != maze[row][2 * col]:
                wrong.append((col, row, maze[row][2 * col], got))
    assert wrong == []
    assert checked == 29 * 19 - 264  # the lead counted 264 corridor squares (plan, X5)


def test_c4_every_joining_cell_in_the_specimen_comes_out_as_drawn():
    maze, is_wall = _specimen_walls()
    checked, covered, wrong = 0, 0, []
    for row in range(specimen.MAZE_HEIGHT):
        for col in range(specimen.MAZE_WIDTH - 1):
            shown = maze[row][2 * col + 1]
            got = joining_cell(is_wall, specimen.MAZE_WIDTH, specimen.MAZE_HEIGHT, col, row)
            if shown in SPRITE_PARTS:
                covered += 1
                assert got == " ", "a sprite is only ever drawn over a blank joining cell"
                continue
            checked += 1
            if got != shown:
                wrong.append((col, row, shown, got))
    assert wrong == []
    assert covered == 4  # ▐ ▌ around the player, ▗ ▖ around the ghost
    assert checked == 29 * 18 - 4


def test_c4_the_specimen_has_the_lone_blocks_it_points_at():
    maze, is_wall = _specimen_walls()
    lone = [(col, row) for row in range(specimen.MAZE_HEIGHT)
            for col in range(specimen.MAZE_WIDTH)
            if is_wall(col, row)
            and square_glyph(is_wall, specimen.MAZE_WIDTH, specimen.MAZE_HEIGHT, col, row) == "■"]
    assert lone == [(6, 18), (6, 22)]  # cell 12 of rows 18 and 22
