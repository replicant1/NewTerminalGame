"""Where everything stands when the window opens (WI-6): START-1 to START-4.

The start squares are checked both on hand-built mazes, where the right
answer can be worked out by hand and written into the test, and over the 200
generated mazes, where the property is asserted against every other corridor
square rather than against a number somebody typed.
"""

import unittest
from typing import Dict

from terminal_game.domain.game_state import Outcome, Score
from terminal_game.domain.maze import Maze, Square
from terminal_game.domain.opening_position import (
    ghost_start_square,
    opening_position,
    player_start_square,
    straight_line_distance_squared,
)

from .generated_mazes import SEEDS, maze_for, mazes_for_every_seed

# Eight corridor squares in a ring around one lone wall. The middle of the
# grid, (2, 2), is that wall, so the nearest corridor squares to the middle
# are the four beside it and the tie has to be broken.
RING = Maze.from_text(
    """
#####
#...#
#.#.#
#...#
#####
"""
)

# A corridor that doubles back on itself. From (1, 3), the square furthest
# **along the corridors** is (1, 1) — eighteen steps away round the bend —
# but it is only two squares away **across the grid**. START-2 says across
# the grid, so the ghost belongs at (9, 1), not (1, 1).
DOUBLED_BACK = Maze.from_text(
    """
###########
#.........#
#########.#
#.........#
###########
"""
)


def corridor_distances_from(maze: Maze, start: Square) -> Dict[Square, int]:
    """How many steps along the corridors each corridor square is."""
    distances = {start: 0}
    frontier = [start]
    while frontier:
        square = frontier.pop(0)
        for neighbour in maze.corridor_neighbours(square):
            if neighbour not in distances:
                distances[neighbour] = distances[square] + 1
                frontier.append(neighbour)
    return distances


class StraightLineDistanceTests(unittest.TestCase):
    def test_a_square_is_no_distance_from_itself(self):
        self.assertEqual(0, straight_line_distance_squared(Square(3, 7), Square(3, 7)))

    def test_it_is_the_same_measured_either_way_round(self):
        one, other = Square(1, 2), Square(9, 14)
        self.assertEqual(
            straight_line_distance_squared(one, other),
            straight_line_distance_squared(other, one),
        )

    def test_it_is_the_squared_distance_across_the_grid(self):
        self.assertEqual(25, straight_line_distance_squared(Square(0, 0), Square(3, 4)))
        self.assertEqual(4, straight_line_distance_squared(Square(1, 1), Square(1, 3)))


class PlayerStartTests(unittest.TestCase):
    def test_the_player_starts_beside_the_middle_when_the_middle_is_wall(self):
        # The middle of the 5 x 5 ring is (2, 2) and it is the lone wall.
        # Four corridor squares are equally near; the first in row-major
        # order is (2, 1).
        self.assertEqual(Square(2, 1), player_start_square(RING))

    def test_the_player_starts_on_a_corridor_square_in_every_generated_maze(self):
        for seed, maze in mazes_for_every_seed().items():
            self.assertTrue(
                maze.is_corridor(player_start_square(maze)), "seed %d" % seed
            )

    def test_no_corridor_square_is_nearer_the_middle_than_the_players(self):
        for seed, maze in mazes_for_every_seed().items():
            start = player_start_square(maze)
            doubled_centre = Square(maze.width - 1, maze.height - 1)

            def from_centre(square):
                return (2 * square.column - doubled_centre.column) ** 2 + (
                    2 * square.row - doubled_centre.row
                ) ** 2

            nearest = from_centre(start)
            for square in maze.corridor_squares():
                self.assertGreaterEqual(
                    from_centre(square),
                    nearest,
                    "seed %d: %r is nearer the middle than %r" % (seed, square, start),
                )

    def test_a_maze_with_no_corridor_has_nowhere_to_start(self):
        with self.assertRaises(ValueError):
            player_start_square(Maze.from_text("###\n###\n###"))


class GhostStartTests(unittest.TestCase):
    def test_the_ghost_starts_furthest_across_the_grid_not_along_the_corridors(self):
        player = Square(1, 3)
        along_the_corridors = corridor_distances_from(DOUBLED_BACK, player)

        # The premise: (1, 1) really is the furthest square to walk to, and
        # (9, 1) really is the furthest across the grid. They are different
        # squares, which is the whole point of START-2's wording.
        self.assertEqual(
            Square(1, 1), max(along_the_corridors, key=along_the_corridors.get)
        )
        self.assertEqual(18, along_the_corridors[Square(1, 1)])
        self.assertEqual(4, straight_line_distance_squared(Square(1, 1), player))
        self.assertEqual(68, straight_line_distance_squared(Square(9, 1), player))

        self.assertEqual(Square(9, 1), ghost_start_square(DOUBLED_BACK, player))

    def test_the_ghost_starts_in_the_far_corner_of_the_ring(self):
        # From (2, 1) the two bottom corners are furthest, at 5; the first in
        # row-major order is (1, 3).
        self.assertEqual(Square(1, 3), ghost_start_square(RING, Square(2, 1)))

    def test_the_ghost_starts_on_a_corridor_square_in_every_generated_maze(self):
        for seed, maze in mazes_for_every_seed().items():
            player = player_start_square(maze)
            self.assertTrue(
                maze.is_corridor(ghost_start_square(maze, player)), "seed %d" % seed
            )

    def test_no_corridor_square_is_further_from_the_player_than_the_ghosts(self):
        for seed, maze in mazes_for_every_seed().items():
            player = player_start_square(maze)
            ghost = ghost_start_square(maze, player)
            furthest = straight_line_distance_squared(ghost, player)
            for square in maze.corridor_squares():
                self.assertLessEqual(
                    straight_line_distance_squared(square, player),
                    furthest,
                    "seed %d: %r is further from the player than %r"
                    % (seed, square, ghost),
                )

    def test_the_player_must_be_somewhere_a_player_could_be(self):
        with self.assertRaises(ValueError):
            ghost_start_square(RING, Square(2, 2))

    def test_one_corridor_square_is_not_enough_for_two_to_start_apart(self):
        with self.assertRaises(ValueError):
            ghost_start_square(
                Maze.from_text("###\n#.#\n###"), Square(1, 1)
            )


class OpeningPositionTests(unittest.TestCase):
    def test_the_two_start_well_apart_in_every_generated_maze(self):
        for seed in SEEDS:
            state = opening_position(maze_for(seed))
            self.assertNotEqual(state.player, state.ghost, "seed %d" % seed)
            self.assertFalse(state.actors_share_a_square, "seed %d" % seed)

    def test_there_is_a_dot_on_every_corridor_square_but_the_players(self):
        for seed in SEEDS[:20]:
            maze = maze_for(seed)
            state = opening_position(maze)
            self.assertEqual(
                len(maze.corridor_squares()) - 1, state.dots.remaining, "seed %d" % seed
            )
            self.assertFalse(state.dots.has_dot(state.player), "seed %d" % seed)

    def test_the_ghost_starts_standing_on_a_dot_it_has_not_taken(self):
        # SCORE-4: the ghost neither eats a dot nor hides one.
        state = opening_position(maze_for(0))
        self.assertTrue(state.dots.has_dot(state.ghost))

    def test_the_score_starts_at_zero_and_no_ending_has_happened(self):
        state = opening_position(maze_for(0))
        self.assertEqual(Score.zero(), state.score)
        self.assertEqual(0, state.score.points)
        self.assertEqual(Outcome.UNDECIDED, state.outcome)
        self.assertFalse(state.is_over)

    def test_the_state_carries_the_maze_it_was_given(self):
        maze = maze_for(11)
        self.assertIs(maze, opening_position(maze).maze)

    def test_the_same_maze_always_opens_the_same_way(self):
        maze = maze_for(5)
        self.assertEqual(opening_position(maze), opening_position(maze))

    def test_the_opening_position_of_the_hand_built_ring(self):
        state = opening_position(RING)
        self.assertEqual(Square(2, 1), state.player)
        self.assertEqual(Square(1, 3), state.ghost)
        self.assertEqual(7, state.dots.remaining)
        self.assertEqual(0, state.score.points)


if __name__ == "__main__":
    unittest.main()
