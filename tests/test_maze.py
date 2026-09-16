"""The maze value and the queries the rest of the system asks of it (WI-5)."""

import unittest

from terminal_game.domain.maze import (
    CORRIDOR_CHARACTER,
    DIRECTIONS,
    Direction,
    Maze,
    Square,
    SquareKind,
    WALL_CHARACTER,
)

# A five-by-five maze whose corridors form a ring around one lone wall square.
# Every corridor square on the ring has exactly two corridor neighbours, so it
# is also the smallest maze that satisfies MAZE-3, MAZE-5 and MAZE-6 at once.
RING = """
#####
#...#
#.#.#
#...#
#####
"""


class SquareTests(unittest.TestCase):
    def test_a_square_is_addressed_by_column_then_row(self):
        square = Square(3, 7)
        self.assertEqual(3, square.column)
        self.assertEqual(7, square.row)

    def test_north_is_one_row_up_the_screen(self):
        self.assertEqual(Square(3, 6), Square(3, 7).neighbour(Direction.NORTH))

    def test_south_east_and_west_step_one_square_each(self):
        self.assertEqual(Square(3, 8), Square(3, 7).neighbour(Direction.SOUTH))
        self.assertEqual(Square(4, 7), Square(3, 7).neighbour(Direction.EAST))
        self.assertEqual(Square(2, 7), Square(3, 7).neighbour(Direction.WEST))


class DirectionTests(unittest.TestCase):
    def test_there_are_exactly_four_directions(self):
        self.assertEqual(4, len(list(Direction)))
        self.assertEqual(set(Direction), set(DIRECTIONS))

    def test_each_direction_reverses_to_the_other_one(self):
        self.assertEqual(Direction.SOUTH, Direction.NORTH.opposite)
        self.assertEqual(Direction.NORTH, Direction.SOUTH.opposite)
        self.assertEqual(Direction.WEST, Direction.EAST.opposite)
        self.assertEqual(Direction.EAST, Direction.WEST.opposite)

    def test_stepping_and_stepping_back_returns_to_where_you_started(self):
        start = Square(5, 5)
        for direction in DIRECTIONS:
            self.assertEqual(
                start, start.neighbour(direction).neighbour(direction.opposite)
            )


class MazeTextNotationTests(unittest.TestCase):
    def test_text_round_trips_through_a_maze_unchanged(self):
        self.assertEqual(RING.strip("\n"), Maze.from_text(RING).to_text())

    def test_the_two_characters_are_the_ones_the_module_names(self):
        maze = Maze.from_text(RING)
        first_line = maze.to_text().splitlines()[0]
        self.assertEqual(WALL_CHARACTER * 5, first_line)
        self.assertIn(CORRIDOR_CHARACTER, maze.to_text())

    def test_an_unknown_character_is_refused_and_named(self):
        with self.assertRaises(ValueError) as caught:
            Maze.from_text("###\n#x#\n###")
        self.assertIn("'x'", str(caught.exception))

    def test_a_ragged_grid_is_refused(self):
        with self.assertRaises(ValueError):
            Maze.from_text("####\n#..#\n###")

    def test_an_empty_grid_is_refused(self):
        with self.assertRaises(ValueError):
            Maze.from_text("")

    def test_a_square_that_is_not_a_kind_is_refused(self):
        with self.assertRaises(ValueError):
            Maze([[SquareKind.WALL, "wall"]])


class MazeShapeTests(unittest.TestCase):
    def setUp(self):
        self.maze = Maze.from_text(RING)

    def test_width_and_height_are_the_squares_across_and_deep(self):
        self.assertEqual(5, self.maze.width)
        self.assertEqual(5, self.maze.height)

    def test_squares_inside_the_grid_are_contained_and_others_are_not(self):
        self.assertTrue(self.maze.contains(Square(0, 0)))
        self.assertTrue(self.maze.contains(Square(4, 4)))
        self.assertFalse(self.maze.contains(Square(5, 0)))
        self.assertFalse(self.maze.contains(Square(0, 5)))
        self.assertFalse(self.maze.contains(Square(-1, 0)))
        self.assertFalse(self.maze.contains(Square(0, -1)))

    def test_squares_walks_the_whole_grid_row_by_row(self):
        walked = list(self.maze.squares())
        self.assertEqual(25, len(walked))
        self.assertEqual(Square(0, 0), walked[0])
        self.assertEqual(Square(1, 0), walked[1])
        self.assertEqual(Square(0, 1), walked[5])
        self.assertEqual(Square(4, 4), walked[-1])


class MazeKindTests(unittest.TestCase):
    def setUp(self):
        self.maze = Maze.from_text(RING)

    def test_the_border_is_wall_and_the_ring_is_corridor(self):
        self.assertEqual(SquareKind.WALL, self.maze.kind_at(Square(0, 0)))
        self.assertEqual(SquareKind.WALL, self.maze.kind_at(Square(2, 2)))
        self.assertEqual(SquareKind.CORRIDOR, self.maze.kind_at(Square(1, 1)))
        self.assertEqual(SquareKind.CORRIDOR, self.maze.kind_at(Square(3, 3)))

    def test_is_wall_and_is_corridor_are_the_two_kinds_and_nothing_else(self):
        for square in self.maze.squares():
            self.assertNotEqual(
                self.maze.is_wall(square),
                self.maze.is_corridor(square),
                "%r is neither or both" % (square,),
            )

    def test_asking_about_a_square_outside_the_grid_is_refused(self):
        with self.assertRaises(ValueError):
            self.maze.kind_at(Square(5, 0))
        with self.assertRaises(ValueError):
            self.maze.is_wall(Square(-1, 1))
        with self.assertRaises(ValueError):
            self.maze.is_corridor(Square(1, 99))

    def test_corridor_squares_are_every_corridor_in_row_major_order(self):
        self.assertEqual(
            (
                Square(1, 1),
                Square(2, 1),
                Square(3, 1),
                Square(1, 2),
                Square(3, 2),
                Square(1, 3),
                Square(2, 3),
                Square(3, 3),
            ),
            self.maze.corridor_squares(),
        )


class MazeNeighbourTests(unittest.TestCase):
    def setUp(self):
        self.maze = Maze.from_text(RING)

    def test_corridor_neighbours_are_the_adjacent_corridors_north_east_south_west(self):
        self.assertEqual(
            (Square(2, 1), Square(1, 2)), self.maze.corridor_neighbours(Square(1, 1))
        )

    def test_a_corridor_square_in_the_middle_of_a_run_has_two_neighbours(self):
        self.assertEqual(
            (Square(3, 1), Square(1, 1)), self.maze.corridor_neighbours(Square(2, 1))
        )

    def test_a_wall_square_may_be_asked_which_corridors_touch_it(self):
        self.assertEqual(
            (Square(2, 1), Square(3, 2), Square(2, 3), Square(1, 2)),
            self.maze.corridor_neighbours(Square(2, 2)),
        )

    def test_a_wall_square_with_no_corridor_beside_it_has_none(self):
        self.assertEqual((), self.maze.corridor_neighbours(Square(0, 0)))

    def test_ways_on_names_the_direction_of_each_corridor_neighbour(self):
        self.assertEqual(
            {Direction.EAST: Square(2, 1), Direction.SOUTH: Square(1, 2)},
            self.maze.ways_on(Square(1, 1)),
        )

    def test_the_border_leaves_no_way_out_of_the_maze(self):
        for square in self.maze.corridor_squares():
            for destination in self.maze.ways_on(square).values():
                self.assertTrue(self.maze.contains(destination))

    def test_wall_neighbours_of_a_corner_exclude_what_is_off_the_grid(self):
        self.assertEqual(
            frozenset({Direction.EAST, Direction.SOUTH}),
            self.maze.wall_neighbours(Square(0, 0)),
        )
        self.assertEqual(
            frozenset({Direction.WEST, Direction.NORTH}),
            self.maze.wall_neighbours(Square(4, 4)),
        )

    def test_wall_neighbours_along_an_edge_run_with_the_edge(self):
        self.assertEqual(
            frozenset({Direction.EAST, Direction.WEST}),
            self.maze.wall_neighbours(Square(2, 0)),
        )

    def test_a_wall_square_with_no_wall_beside_it_has_no_wall_neighbours(self):
        self.assertEqual(frozenset(), self.maze.wall_neighbours(Square(2, 2)))

    def test_asking_about_neighbours_outside_the_grid_is_refused(self):
        with self.assertRaises(ValueError):
            self.maze.corridor_neighbours(Square(9, 9))
        with self.assertRaises(ValueError):
            self.maze.wall_neighbours(Square(9, 9))


class MazeValueTests(unittest.TestCase):
    def test_two_mazes_built_from_the_same_grid_are_the_same_value(self):
        one = Maze.from_text(RING)
        another = Maze.from_text(RING)
        self.assertEqual(one, another)
        self.assertEqual(hash(one), hash(another))
        self.assertEqual(1, len({one, another}))

    def test_mazes_differing_in_one_square_are_different_values(self):
        one = Maze.from_text(RING)
        another = Maze.from_text("#####\n#...#\n#...#\n#...#\n#####")
        self.assertNotEqual(one, another)
        self.assertEqual(2, len({one, another}))

    def test_a_maze_is_not_equal_to_something_that_is_not_a_maze(self):
        self.assertNotEqual(Maze.from_text(RING), RING)


if __name__ == "__main__":
    unittest.main()
