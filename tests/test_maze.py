"""The maze as data — MAZE-1, MAZE-2, and walking the grid.

Two requirements are pinned here and they are pinned as *impossibilities*
rather than as defaults, because that is what they say.  MAZE-1 fixes the
grid at 19 x 29, and the plan asks that **no other shape be representable**:
every route to a maze either produces that shape or refuses.  MAZE-2 says a
square is corridor or wall, and there is nowhere for a third kind to live.
"""

from __future__ import annotations

import pytest

from terminal_game.domain.maze import (
    CORRIDOR_CHAR,
    HEIGHT,
    WALL_CHAR,
    WIDTH,
    Direction,
    Maze,
    Position,
    Square,
)

SOLID_ROW = WALL_CHAR * WIDTH
SOLID_ROWS = [SOLID_ROW] * HEIGHT


# --------------------------------------------------------------------------
# MAZE-1 — 19 across, 29 deep, and no other shape
# --------------------------------------------------------------------------


def test_the_grid_is_nineteen_across_and_twenty_nine_deep() -> None:
    maze = Maze.all_walls()
    assert (maze.width, maze.height) == (19, 29)


def test_the_grid_holds_five_hundred_and_fifty_one_squares() -> None:
    """19 x 29. Counted rather than multiplied, so the iteration is pinned too."""
    assert len(list(Maze.all_walls().positions())) == 551


def test_positions_are_produced_in_reading_order() -> None:
    """Left to right, top to bottom, with ``y`` increasing downwards.

    Everything built on top of a maze inherits this order — the dot field,
    START-2's furthest-square search, the rows the frame composer draws — so
    it is worth pinning rather than assuming.
    """
    positions = list(Maze.all_walls().positions())
    assert positions[0] == Position(0, 0)
    assert positions[1] == Position(1, 0)
    assert positions[WIDTH] == Position(0, 1)
    assert positions[-1] == Position(WIDTH - 1, HEIGHT - 1)


@pytest.mark.parametrize("rows", [SOLID_ROWS[:-1], SOLID_ROWS + [SOLID_ROW]])
def test_a_maze_of_the_wrong_depth_cannot_be_built(rows) -> None:
    with pytest.raises(ValueError) as raised:
        Maze.from_rows(rows)
    assert "29 rows deep" in str(raised.value)


@pytest.mark.parametrize("width", [WIDTH - 1, WIDTH + 1])
def test_a_maze_of_the_wrong_width_cannot_be_built(width) -> None:
    with pytest.raises(ValueError) as raised:
        Maze.from_rows([WALL_CHAR * width] * HEIGHT)
    assert "19 squares across" in str(raised.value)


def test_a_ragged_maze_cannot_be_built() -> None:
    """One short row is the way a hand-built maze usually goes wrong."""
    rows = list(SOLID_ROWS)
    rows[7] = WALL_CHAR * (WIDTH - 1)
    with pytest.raises(ValueError) as raised:
        Maze.from_rows(rows)
    assert "row 7" in str(raised.value)


@pytest.mark.parametrize(
    "outside", [Position(WIDTH, 0), Position(0, HEIGHT), Position(-1, 0), Position(0, -1)]
)
def test_a_square_outside_the_grid_cannot_be_carved(outside) -> None:
    with pytest.raises(ValueError) as raised:
        Maze.all_walls().with_corridors_at([outside])
    assert str(outside) in str(raised.value)


def test_the_grid_is_the_same_shape_however_it_was_built() -> None:
    """The two construction routes cannot disagree about the shape."""
    from_nothing = Maze.all_walls()
    from_picture = Maze.from_rows(SOLID_ROWS)
    assert from_nothing.to_rows() == from_picture.to_rows()
    assert len(from_picture.to_rows()) == HEIGHT
    assert {len(row) for row in from_picture.to_rows()} == {WIDTH}


# --------------------------------------------------------------------------
# MAZE-2 — corridor or wall, and nothing else
# --------------------------------------------------------------------------


def test_a_square_has_exactly_two_kinds() -> None:
    assert set(Square) == {Square.WALL, Square.CORRIDOR}
    assert len(Square) == 2


def test_every_square_of_a_maze_is_one_of_those_two_kinds(sound_maze) -> None:
    kinds = {sound_maze.square_at(p) for p in sound_maze.positions()}
    assert kinds <= {Square.WALL, Square.CORRIDOR}


def test_wall_and_corridor_are_exact_complements(sound_maze) -> None:
    """There is no square that is both, and none that is neither."""
    for position in sound_maze.positions():
        assert sound_maze.is_wall(position) != sound_maze.is_corridor(position)


def test_a_third_kind_of_square_cannot_be_read_in() -> None:
    rows = list(SOLID_ROWS)
    rows[3] = WALL_CHAR * 5 + "?" + WALL_CHAR * (WIDTH - 6)
    with pytest.raises(ValueError) as raised:
        Maze.from_rows(rows)
    assert "row 3 column 5" in str(raised.value)


def test_every_square_is_accounted_for_as_wall_or_corridor(sound_maze) -> None:
    assert len(sound_maze.corridors()) + len(sound_maze.walls()) == 551


# --------------------------------------------------------------------------
# Reading and writing a maze as a picture
# --------------------------------------------------------------------------


def test_a_maze_survives_a_round_trip_through_its_picture(sound_maze) -> None:
    assert Maze.from_rows(sound_maze.to_rows()) == sound_maze


def test_a_picture_uses_hash_for_wall_and_dot_for_corridor(draw) -> None:
    maze = draw("..", at=(2, 1))
    assert maze.to_rows()[1][:5] == WALL_CHAR * 2 + CORRIDOR_CHAR * 2 + WALL_CHAR


# --------------------------------------------------------------------------
# Carving, and the fact that it does not change the maze it came from
# --------------------------------------------------------------------------


def test_carving_returns_a_new_maze_and_leaves_the_old_one_alone() -> None:
    """WI-2 holds on to a maze it has checked while it tries a repair."""
    solid = Maze.all_walls()
    carved = solid.with_corridors_at([Position(5, 5)])

    assert carved.is_corridor(Position(5, 5))
    assert solid.is_wall(Position(5, 5))
    assert solid.corridors() == ()


def test_filling_a_square_back_in_returns_a_new_maze(sound_maze) -> None:
    corner = sound_maze.corridors()[0]
    filled = sound_maze.with_walls_at([corner])

    assert filled.is_wall(corner)
    assert sound_maze.is_corridor(corner)


def test_carving_a_square_that_is_already_corridor_changes_nothing(sound_maze) -> None:
    corner = sound_maze.corridors()[0]
    assert sound_maze.with_corridors_at([corner]) == sound_maze


def test_two_mazes_with_the_same_corridors_are_equal_and_hash_alike() -> None:
    one = Maze.all_walls().with_corridors_at([Position(3, 4), Position(3, 5)])
    other = Maze.all_walls().with_corridors_at([Position(3, 5), Position(3, 4)])
    assert one == other
    assert len({one, other}) == 1


def test_a_maze_is_not_equal_to_something_that_is_not_a_maze() -> None:
    assert Maze.all_walls() != "#"


# --------------------------------------------------------------------------
# Corridors, walls and the border ring
# --------------------------------------------------------------------------


def test_corridors_come_back_in_reading_order(draw) -> None:
    """START-2's tie-breaking rests on this being the same every run."""
    maze = draw(
        """
        ..
        ..
        """,
        at=(6, 9),
    )
    assert maze.corridors() == (
        Position(6, 9),
        Position(7, 9),
        Position(6, 10),
        Position(7, 10),
    )


def test_the_border_ring_is_the_outermost_squares() -> None:
    border = set(Maze.all_walls().border())
    assert Position(0, 0) in border
    assert Position(WIDTH - 1, HEIGHT - 1) in border
    assert Position(1, 1) not in border
    assert Position(WIDTH - 2, HEIGHT - 2) not in border


def test_the_border_ring_has_ninety_two_squares() -> None:
    """19 + 19 along the top and bottom, plus 27 + 27 down the sides."""
    assert len(Maze.all_walls().border()) == 92


def test_the_border_ring_counts_each_corner_once() -> None:
    border = Maze.all_walls().border()
    assert len(border) == len(set(border))


# --------------------------------------------------------------------------
# Positions and directions
# --------------------------------------------------------------------------


def test_there_are_four_directions_and_they_are_axis_aligned() -> None:
    """MAZE-2: corridors run only north-south and east-west."""
    assert len(Direction) == 4
    for direction in Direction:
        dx, dy = direction.value
        assert (dx == 0) != (dy == 0)
        assert {abs(dx), abs(dy)} == {0, 1}


@pytest.mark.parametrize(
    "direction,expected",
    [
        (Direction.NORTH, Position(5, 4)),
        (Direction.SOUTH, Position(5, 6)),
        (Direction.EAST, Position(6, 5)),
        (Direction.WEST, Position(4, 5)),
    ],
)
def test_a_step_goes_where_the_direction_says(direction, expected) -> None:
    """North is ``y`` minus one, because ``y`` increases down the screen."""
    assert Position(5, 5).step(direction) == expected


@pytest.mark.parametrize(
    "direction,expected",
    [
        (Direction.NORTH, Direction.SOUTH),
        (Direction.SOUTH, Direction.NORTH),
        (Direction.EAST, Direction.WEST),
        (Direction.WEST, Direction.EAST),
    ],
)
def test_every_direction_has_an_opposite(direction, expected) -> None:
    """GHOST-3 is about the way back, so the way back has to be nameable."""
    assert direction.opposite() is expected


def test_a_positions_four_neighbours_are_the_four_steps() -> None:
    position = Position(9, 14)
    assert set(position.neighbours()) == {
        position.step(direction) for direction in Direction
    }
    assert len(position.neighbours()) == 4


# --------------------------------------------------------------------------
# Neighbour queries on the maze, which know where the grid ends
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "position,expected",
    [
        (Position(0, 0), 2),
        (Position(WIDTH - 1, 0), 2),
        (Position(0, HEIGHT - 1), 2),
        (Position(WIDTH - 1, HEIGHT - 1), 2),
        (Position(5, 0), 3),
        (Position(0, 5), 3),
        (Position(5, 5), 4),
    ],
)
def test_neighbours_stop_at_the_edge_of_the_grid(position, expected) -> None:
    assert len(Maze.all_walls().neighbours(position)) == expected


def test_every_neighbour_returned_is_on_the_grid() -> None:
    maze = Maze.all_walls()
    for position in maze.positions():
        for neighbour in maze.neighbours(position):
            assert maze.contains(neighbour)


def test_corridor_neighbours_are_the_squares_you_could_step_onto(draw) -> None:
    maze = draw(
        """
        .#.
        ...
        .#.
        """,
        at=(7, 7),
    )
    middle = Position(8, 8)
    assert set(maze.corridor_neighbours(middle)) == {Position(7, 8), Position(9, 8)}


def test_a_corridor_square_walled_in_on_every_side_has_no_ways_on(draw) -> None:
    maze = draw(".", at=(9, 9))
    assert maze.corridor_neighbours(Position(9, 9)) == ()


def test_ways_on_name_the_direction_as_well_as_the_square(draw) -> None:
    """A ghost needs to know which way it came, not only where it can go."""
    maze = draw(
        """
        .#
        ..
        """,
        at=(3, 3),
    )
    assert maze.ways_on_from(Position(3, 4)) == {
        Direction.NORTH: Position(3, 3),
        Direction.EAST: Position(4, 4),
    }


def test_ways_on_and_corridor_neighbours_agree(draw) -> None:
    """Two ways of asking the same question must not be able to disagree."""
    maze = draw(
        """
        .....
        .###.
        .....
        """,
        at=(6, 6),
    )
    for position in maze.corridors():
        assert set(maze.ways_on_from(position).values()) == set(
            maze.corridor_neighbours(position)
        )


def test_ways_on_from_a_square_at_the_edge_does_not_run_off_the_grid() -> None:
    """``ways_on_from`` filters bounds itself; MAZE-3 should mean it never has to."""
    maze = Maze.all_walls().with_corridors_at([Position(0, 0)])
    assert maze.ways_on_from(Position(0, 0)) == {}


# --------------------------------------------------------------------------
# Asking about somewhere that is not on the grid
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "outside", [Position(WIDTH, 0), Position(0, HEIGHT), Position(-1, 4), Position(4, -1)]
)
def test_asking_what_is_outside_the_grid_is_an_error_not_a_wall(outside) -> None:
    """A silent ``WALL`` would make an out-of-bounds bug look like a dead end."""
    maze = Maze.all_walls()
    assert not maze.contains(outside)
    with pytest.raises(IndexError):
        maze.square_at(outside)
    with pytest.raises(IndexError):
        maze.neighbours(outside)


def test_contains_accepts_every_square_on_the_grid() -> None:
    maze = Maze.all_walls()
    assert all(maze.contains(position) for position in maze.positions())
