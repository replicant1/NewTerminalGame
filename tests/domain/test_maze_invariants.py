"""The structural requirements, checked against mazes with known faults (WI-5).

Each check is exercised on a maze that satisfies it and on a hand-built maze
that breaks it in one named way, so that the generator's verify step is
trustworthy before it is relied on.
"""

import unittest

from terminalgame.domain.maze import Maze, Square
from terminalgame.domain.maze_invariants import (
    dead_end_squares,
    diagonal_only_corridor_pairs,
    holes_in_border,
    structural_faults,
    two_wide_corridor_squares,
    unreachable_corridor_squares,
)

# A maze that satisfies every structural requirement: a solid border, a ring of
# single-width corridor with no dead end, and one lone wall square inside it.
SOUND = Maze.from_text(
    """
#####
#...#
#.#.#
#...#
#####
"""
)


class BorderTests(unittest.TestCase):
    def test_a_solid_border_has_no_holes(self):
        self.assertEqual((), holes_in_border(SOUND))

    def test_a_corridor_reaching_the_top_edge_is_a_hole(self):
        maze = Maze.from_text(
            """
##.##
#...#
#.#.#
#...#
#####
"""
        )
        self.assertEqual((Square(2, 0),), holes_in_border(maze))

    def test_holes_are_found_on_all_four_sides(self):
        maze = Maze.from_text(
            """
##.##
....#
#.#.#
#....
##.##
"""
        )
        self.assertEqual(
            (Square(2, 0), Square(0, 1), Square(4, 3), Square(2, 4)),
            holes_in_border(maze),
        )


class DeadEndTests(unittest.TestCase):
    def test_a_ring_of_corridor_has_no_dead_ends(self):
        self.assertEqual((), dead_end_squares(SOUND))

    def test_a_corridor_stub_is_a_dead_end(self):
        # A ring of corridor with a two-square stub hanging into the middle
        # of it. The tip of the stub has one way on, so the player could be
        # walked into a pocket; MAZE-5 forbids it.
        maze = Maze.from_text(
            """
#######
#.....#
#.###.#
#.#.#.#
#.#.#.#
#.....#
#######
"""
        )
        self.assertEqual((Square(3, 3),), dead_end_squares(maze))

    def test_a_corridor_square_walled_in_on_all_sides_is_a_dead_end(self):
        island = Maze.from_text(
            """
#####
#####
##.##
#####
#####
"""
        )
        self.assertEqual((Square(2, 2),), dead_end_squares(island))


class ConnectivityTests(unittest.TestCase):
    def test_a_single_ring_is_all_reachable_from_itself(self):
        self.assertEqual((), unreachable_corridor_squares(SOUND))

    def test_a_second_pocket_walled_off_from_the_first_is_unreachable(self):
        maze = Maze.from_text(
            """
#########
#...#...#
#.#.#.#.#
#...#...#
#########
"""
        )
        self.assertEqual(
            (
                Square(5, 1),
                Square(6, 1),
                Square(7, 1),
                Square(5, 2),
                Square(7, 2),
                Square(5, 3),
                Square(6, 3),
                Square(7, 3),
            ),
            unreachable_corridor_squares(maze),
        )

    def test_a_maze_with_no_corridor_at_all_is_vacuously_connected(self):
        self.assertEqual(
            (), unreachable_corridor_squares(Maze.from_text("###\n###\n###"))
        )


class CorridorWidthTests(unittest.TestCase):
    def test_single_width_corridors_are_not_reported(self):
        self.assertEqual((), two_wide_corridor_squares(SOUND))

    def test_a_two_by_two_opening_is_a_corridor_two_squares_wide(self):
        maze = Maze.from_text(
            """
#####
#...#
#...#
#...#
#####
"""
        )
        self.assertEqual(
            (
                Square(1, 1),
                Square(2, 1),
                Square(1, 2),
                Square(2, 2),
            ),
            two_wide_corridor_squares(maze),
        )


class DiagonalTests(unittest.TestCase):
    def test_a_maze_whose_corridors_all_join_orthogonally_has_no_diagonals(self):
        self.assertEqual((), diagonal_only_corridor_pairs(SOUND))

    def test_two_corridors_touching_only_at_a_corner_are_a_diagonal(self):
        maze = Maze.from_text(
            """
#####
#.###
##.##
###.#
#####
"""
        )
        self.assertEqual(
            (
                (Square(1, 1), Square(2, 2)),
                (Square(2, 2), Square(3, 3)),
            ),
            diagonal_only_corridor_pairs(maze),
        )

    def test_the_other_diagonal_is_found_too(self):
        maze = Maze.from_text(
            """
#####
###.#
##.##
#.###
#####
"""
        )
        self.assertEqual(
            (
                (Square(3, 1), Square(2, 2)),
                (Square(2, 2), Square(1, 3)),
            ),
            diagonal_only_corridor_pairs(maze),
        )


class StructuralFaultTests(unittest.TestCase):
    def test_a_sound_maze_reports_no_faults(self):
        self.assertEqual((), structural_faults(SOUND))

    def test_every_broken_requirement_is_reported_and_named(self):
        # A border hole at the top, a two-wide corridor, and — because the
        # right-hand pocket is sealed off — both a dead end and something
        # unreachable.
        maze = Maze.from_text(
            """
##.######
#...#.#.#
#...###.#
#...#...#
#########
"""
        )
        faults = structural_faults(maze)
        codes = " ".join(faults)
        self.assertIn("MAZE-3", codes)
        self.assertIn("MAZE-5", codes)
        self.assertIn("MAZE-6", codes)
        self.assertIn("MAZE-2", codes)

    def test_a_fault_says_where_the_problem_is(self):
        maze = Maze.from_text(
            """
#####
#####
##.##
#####
#####
"""
        )
        self.assertIn("(column 2, row 2)", " ".join(structural_faults(maze)))


if __name__ == "__main__":
    unittest.main()
