"""WI-2: the Maze value, the questions the rest of the game asks of it.

Every test here uses a small hand-built maze whose answers can be read off the
picture, so each expected value is independent of the code under test.
"""

from __future__ import annotations

import pytest

from terminal_game.domain.maze import Maze

# col:  01234
PLAN = (
    "#####",  # row 0
    "#...#",  # row 1
    "#.#.#",  # row 2
    "#...#",  # row 3
    "#####",  # row 4
)


@pytest.fixture
def ring():
    return Maze.from_rows(PLAN)


def test_a3_text_round_trip(ring):
    assert (ring.width, ring.height) == (5, 5)
    assert ring.to_rows() == PLAN


def test_a3_squares_are_col_then_row_counted_from_the_north_west(ring):
    # (col 2, row 2) is the pillar in the middle; (col 1, row 2) is corridor.
    assert ring.is_wall((2, 2))
    assert ring.is_corridor((1, 2))
    # An asymmetric maze pins the axis order: col 3, row 1 is corridor, col 1, row 3 is not.
    lopsided = Maze.from_rows(["#####", "###.#", "#####"])
    assert lopsided.is_corridor((3, 1))
    assert lopsided.is_wall((1, 1))


def test_a3_wall_and_corridor_inside_the_grid(ring):
    for r, line in enumerate(PLAN):
        for c, ch in enumerate(line):
            assert ring.is_corridor((c, r)) is (ch == ".")
            assert ring.is_wall((c, r)) is (ch == "#")


@pytest.mark.parametrize("square", [(-1, 0), (0, -1), (5, 2), (2, 5), (-1, -1), (5, 5)])
def test_a3_a_square_off_the_grid_is_neither_wall_nor_corridor(ring, square):
    assert ring.contains(square) is False
    assert ring.is_wall(square) is False
    assert ring.is_corridor(square) is False


def test_a3_open_neighbours_are_the_corridor_squares_north_south_east_west_in_that_order():
    maze = Maze.from_rows(
        [
            "#####",
            "##.##",
            "#...#",
            "##.##",
            "#####",
        ]
    )
    assert maze.open_neighbours((2, 2)) == ((2, 1), (2, 3), (3, 2), (1, 2))
    assert maze.open_neighbours((2, 1)) == ((2, 2),)
    assert maze.open_neighbours((0, 0)) == ()


def test_a3_neighbours_leave_out_squares_off_the_grid(ring):
    assert ring.neighbours((0, 0)) == ((0, 1), (1, 0))
    assert ring.neighbours((4, 4)) == ((4, 3), (3, 4))
    assert ring.neighbours((2, 2)) == ((2, 1), (2, 3), (3, 2), (1, 2))


def test_a3_open_neighbours_at_the_edge_of_an_open_grid():
    # A maze with corridor on its edge (a hand-built one may): nothing off-grid is offered.
    maze = Maze.from_rows(["..", ".."])
    assert maze.open_neighbours((0, 0)) == ((0, 1), (1, 0))


def test_a3_corridor_squares_run_row_by_row_from_the_north(ring):
    assert ring.corridor_squares() == (
        (1, 1), (2, 1), (3, 1),
        (1, 2), (3, 2),
        (1, 3), (2, 3), (3, 3),
    )


def test_a3_a_hand_built_maze_may_have_a_dead_end():
    # Other work items (WI-8/C3) need one; the value must not refuse it.
    maze = Maze.from_rows(["#####", "#...#", "#####"])
    assert maze.open_neighbours((1, 1)) == ((2, 1),)


def test_a3_mazes_are_equal_exactly_when_every_square_matches(ring):
    assert Maze.from_rows(PLAN) == ring
    assert hash(Maze.from_rows(PLAN)) == hash(ring)
    other = Maze.from_rows(["#####", "#...#", "#...#", "#...#", "#####"])
    assert other != ring


def test_a3_a_maze_cannot_be_changed(ring):
    with pytest.raises(AttributeError):
        ring.corridors = frozenset()
    assert ring.to_rows() == PLAN


@pytest.mark.parametrize(
    "rows, message",
    [
        ([], "at least one row"),
        (["###", "##"], "row 1 is 2 squares wide, expected 3"),
        (["#x#"], "'x' is neither"),
    ],
)
def test_a3_malformed_text_is_refused(rows, message):
    with pytest.raises(ValueError, match=message):
        Maze.from_rows(rows)


def test_a3_a_corridor_outside_the_grid_is_refused():
    with pytest.raises(ValueError, match=r"outside a 3 x 3 grid: \[\(3, 0\)\]"):
        Maze(3, 3, frozenset({(1, 1), (3, 0)}))


def test_a3_an_empty_grid_is_refused():
    with pytest.raises(ValueError, match="at least 1 x 1"):
        Maze(0, 3, frozenset())
