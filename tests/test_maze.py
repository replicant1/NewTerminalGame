"""The maze model on its own, against mazes built by hand.

Nothing here is generated. Every maze in this file is written out as text, so
each assertion is about a grid the reader can see, and a failure says which
square was wrong rather than which seed was unlucky. The generated-maze
properties — MAZE-2 to MAZE-6 over several hundred seeds — are in
`test_maze_generator.py`.
"""

from __future__ import annotations

import unittest

from terminalgame.domain.maze import (
    CORRIDOR,
    DIRECTIONS,
    EAST,
    HEIGHT,
    NORTH,
    SOUTH,
    WALL,
    WEST,
    WIDTH,
    Maze,
    solid,
)


# A small maze with a ring of corridor in it and one square of wall in the
# middle. Every corridor square on the ring has exactly two ways on.
RING = """
#####
#   #
# # #
#   #
#####
"""

# Two corridor squares that never touch: the left-hand one and the right-hand
# one are separated by a column of wall all the way down.
TWO_ROOMS = """
#####
# # #
# # #
# # #
#####
"""


class MazeShapeTest(unittest.TestCase):

    def test_the_specified_grid_is_nineteen_across_and_twenty_nine_deep(self):
        # MAZE-1. The numbers live in the domain because they are the size of
        # the maze, not the size of anything on a screen.
        self.assertEqual(19, WIDTH)
        self.assertEqual(29, HEIGHT)

    def test_a_solid_grid_is_all_wall_and_the_size_asked_for(self):
        maze = Maze(solid(5, 7))
        self.assertEqual(5, maze.width)
        self.assertEqual(7, maze.height)
        self.assertEqual([], maze.corridor_squares())

    def test_solid_defaults_to_the_specified_grid(self):
        maze = Maze(solid())
        self.assertEqual((19, 29), (maze.width, maze.height))

    def test_rows_of_different_widths_are_refused(self):
        with self.assertRaises(ValueError):
            Maze([[WALL, WALL], [WALL]])

    def test_a_square_that_is_neither_corridor_nor_wall_is_refused(self):
        with self.assertRaises(ValueError):
            Maze([[WALL, "door"]])

    def test_an_empty_grid_is_refused(self):
        with self.assertRaises(ValueError):
            Maze([])


class ReadingSquaresTest(unittest.TestCase):

    def setUp(self):
        self.maze = Maze.from_text(RING)

    def test_the_text_form_round_trips(self):
        self.assertEqual(RING.strip("\n"), self.maze.as_text())

    def test_a_square_inside_the_ring_is_corridor(self):
        self.assertTrue(self.maze.is_corridor(1, 1))
        self.assertEqual(CORRIDOR, self.maze.square_at(1, 1))

    def test_the_middle_of_the_ring_is_wall(self):
        self.assertTrue(self.maze.is_wall(2, 2))
        self.assertEqual(WALL, self.maze.square_at(2, 2))

    def test_everything_off_the_grid_is_wall(self):
        # MAZE-3 says nothing can leave the maze. A caller that walks a square
        # past the edge should be told it is solid, not handed an exception,
        # and not handed the far side of the grid by a negative index.
        for off_the_grid in [(-1, 1), (1, -1), (5, 1), (1, 5), (-1, -1)]:
            self.assertTrue(self.maze.is_wall(*off_the_grid), off_the_grid)
            self.assertFalse(self.maze.contains(*off_the_grid), off_the_grid)

    def test_a_negative_x_is_not_read_as_the_right_hand_edge(self):
        # The square at (3, 1) is corridor; Python would happily return it for
        # x = -2 if `square_at` indexed the row directly.
        self.assertTrue(self.maze.is_corridor(3, 1))
        self.assertTrue(self.maze.is_wall(-2, 1))

    def test_corridor_squares_come_back_in_reading_order(self):
        self.assertEqual(
            [(1, 1), (2, 1), (3, 1),
             (1, 2), (3, 2),
             (1, 3), (2, 3), (3, 3)],
            self.maze.corridor_squares())


class FourSidesTest(unittest.TestCase):

    def test_the_four_directions_are_north_south_east_and_west(self):
        # MAZE-2: corridors run only north-south and east-west, so four is
        # the whole of it.
        self.assertEqual(4, len(DIRECTIONS))
        self.assertEqual(["north", "south", "east", "west"],
                         [d.name for d in DIRECTIONS])

    def test_north_is_up_and_south_is_down(self):
        # y counts down from the top, so this is the one that is easy to get
        # backwards and impossible to notice later.
        self.assertEqual((5, 4), NORTH.from_square(5, 5))
        self.assertEqual((5, 6), SOUTH.from_square(5, 5))
        self.assertEqual((6, 5), EAST.from_square(5, 5))
        self.assertEqual((4, 5), WEST.from_square(5, 5))

    def test_each_direction_has_an_opposite_that_undoes_it(self):
        for direction in DIRECTIONS:
            there = direction.from_square(4, 4)
            back = direction.opposite().from_square(*there)
            self.assertEqual((4, 4), back, direction.name)

    def test_neighbours_gives_all_four_sides_whether_or_not_they_exist(self):
        maze = Maze.from_text(RING)
        self.assertEqual(
            [("north", 1, 0), ("south", 1, 2), ("east", 2, 1), ("west", 0, 1)],
            [(d.name, x, y) for d, x, y in maze.neighbours(1, 1)])

    def test_neighbours_of_a_corner_square_include_squares_off_the_grid(self):
        maze = Maze.from_text(RING)
        self.assertEqual(
            [("north", 0, -1), ("south", 0, 1), ("east", 1, 0), ("west", -1, 0)],
            [(d.name, x, y) for d, x, y in maze.neighbours(0, 0)])

    def test_open_neighbours_gives_only_the_ways_on(self):
        maze = Maze.from_text(RING)
        # (1, 1) is the top-left of the ring: corridor east and corridor
        # south, wall north and wall west.
        self.assertEqual([("south", 1, 2), ("east", 2, 1)],
                         [(d.name, x, y) for d, x, y in maze.open_neighbours(1, 1)])

    def test_ways_on_counts_the_open_neighbours(self):
        maze = Maze.from_text(RING)
        for square in maze.corridor_squares():
            self.assertEqual(2, maze.ways_on(*square), square)

    def test_a_square_walled_in_on_all_four_sides_has_no_ways_on(self):
        maze = Maze.from_text("""
#####
## ##
#####
""")
        self.assertEqual(0, maze.ways_on(2, 1))
        self.assertEqual([], maze.open_neighbours(2, 1))


class ReachabilityTest(unittest.TestCase):

    def test_every_square_of_a_ring_is_reachable_from_any_of_them(self):
        maze = Maze.from_text(RING)
        everything = set(maze.corridor_squares())
        for square in everything:
            self.assertEqual(everything, maze.reachable_from(*square), square)

    def test_a_maze_in_two_halves_reaches_only_its_own_half(self):
        # This is the state MAZE-6 forbids, and the reason `reachable_from`
        # is worth having: if the check could not tell these apart it would
        # not be checking anything.
        maze = Maze.from_text(TWO_ROOMS)
        left = maze.reachable_from(1, 1)
        right = maze.reachable_from(3, 1)
        self.assertEqual({(1, 1), (1, 2), (1, 3)}, left)
        self.assertEqual({(3, 1), (3, 2), (3, 3)}, right)
        self.assertEqual(set(), left & right)

    def test_reachability_does_not_cut_diagonally(self):
        # Two corridor squares touching only at a corner are not connected:
        # MAZE-2 allows movement north-south and east-west only.
        maze = Maze.from_text("""
####
# ##
## #
####
""")
        self.assertEqual({(1, 1)}, maze.reachable_from(1, 1))
        self.assertEqual({(2, 2)}, maze.reachable_from(2, 2))

    def test_nothing_is_reachable_from_a_wall(self):
        maze = Maze.from_text(RING)
        self.assertEqual(set(), maze.reachable_from(2, 2))
        self.assertEqual(set(), maze.reachable_from(0, 0))


class ComparingTest(unittest.TestCase):

    def test_two_mazes_with_the_same_squares_are_equal(self):
        self.assertEqual(Maze.from_text(RING), Maze.from_text(RING))
        self.assertEqual(hash(Maze.from_text(RING)), hash(Maze.from_text(RING)))

    def test_mazes_that_differ_by_one_square_are_not_equal(self):
        self.assertNotEqual(Maze.from_text(RING), Maze.from_text(TWO_ROOMS))

    def test_a_maze_is_not_equal_to_something_that_is_not_a_maze(self):
        self.assertNotEqual(Maze.from_text(RING), RING)

    def test_the_grid_cannot_be_changed_through_rows(self):
        maze = Maze.from_text(RING)
        with self.assertRaises(TypeError):
            maze.rows()[0][0] = CORRIDOR
        self.assertTrue(maze.is_wall(0, 0))

    def test_changing_the_rows_it_was_built_from_does_not_change_the_maze(self):
        rows = solid(3, 3)
        maze = Maze(rows)
        rows[1][1] = CORRIDOR
        self.assertTrue(maze.is_wall(1, 1))


if __name__ == "__main__":
    unittest.main()
