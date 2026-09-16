"""The generated maze's structural properties, over many seeds (WI-5).

Caution C4 of `docs/ARCHITECTURE.md` names this the single algorithm most
likely to ship subtly wrong, because MAZE-4, MAZE-5 and MAZE-6 are three
constraints on one grid. So every property here is asserted over 200 seeds
rather than one, and asserted **directly against the maze's query surface**
rather than through `maze_invariants` — which the generator itself uses, and
which has its own tests in `test_maze_invariants.py`. Two independent
statements of the same property is the point.

The mazes are laid out once in `setUpClass` and shared, so the sweep costs one
generation per seed however many properties are checked.
"""

import random
import unittest
from typing import Set, Tuple

from terminal_game.domain.maze import Maze, Square, SquareKind
from terminal_game.domain.maze_generator import (
    CELL_COLUMNS,
    CELL_ROWS,
    MAZE_HEIGHT,
    MAZE_WIDTH,
    generate_maze,
)

#: Many seeds, not one.
SEEDS: Tuple[int, ...] = tuple(range(200))

#: Floods from every corridor square are quadratic, so only a few seeds get
#: the exhaustive treatment; the rest are flooded from one square, which is
#: equivalent given that reachability across corridor squares is symmetric.
SEEDS_FLOODED_FROM_EVERY_SQUARE: Tuple[int, ...] = SEEDS[:3]


_LAID_OUT = {}


def mazes_for_every_seed():
    """The 200 mazes, laid out once and shared by every test that wants them."""
    if not _LAID_OUT:
        _LAID_OUT.update(
            (seed, generate_maze(random.Random(seed))) for seed in SEEDS
        )
    return _LAID_OUT


def reachable_from(maze: Maze, start: Square) -> Set[Square]:
    """Every corridor square a walker starting here could get to."""
    reached = {start}
    frontier = [start]
    while frontier:
        square = frontier.pop()
        for neighbour in maze.corridor_neighbours(square):
            if neighbour not in reached:
                reached.add(neighbour)
                frontier.append(neighbour)
    return reached


class GeneratedMazeTests(unittest.TestCase):
    """Properties every generated maze must have, checked over every seed."""

    mazes = {}

    @classmethod
    def setUpClass(cls):
        cls.mazes = mazes_for_every_seed()

    def test_the_grid_is_nineteen_across_and_twenty_nine_deep(self):
        self.assertEqual(19, MAZE_WIDTH)
        self.assertEqual(29, MAZE_HEIGHT)
        for seed, maze in self.mazes.items():
            self.assertEqual(MAZE_WIDTH, maze.width, "seed %d" % seed)
            self.assertEqual(MAZE_HEIGHT, maze.height, "seed %d" % seed)

    def test_every_square_is_one_of_exactly_two_kinds(self):
        for seed, maze in self.mazes.items():
            kinds = {maze.kind_at(square) for square in maze.squares()}
            self.assertEqual({SquareKind.WALL, SquareKind.CORRIDOR}, kinds, "seed %d" % seed)

    def test_the_border_ring_is_solid_on_all_four_sides(self):
        for seed, maze in self.mazes.items():
            top = 0
            bottom = maze.height - 1
            left = 0
            right = maze.width - 1
            for column in range(maze.width):
                self.assertTrue(maze.is_wall(Square(column, top)), "seed %d top" % seed)
                self.assertTrue(
                    maze.is_wall(Square(column, bottom)), "seed %d bottom" % seed
                )
            for row in range(maze.height):
                self.assertTrue(maze.is_wall(Square(left, row)), "seed %d left" % seed)
                self.assertTrue(maze.is_wall(Square(right, row)), "seed %d right" % seed)

    def test_no_corridor_square_has_fewer_than_two_corridor_neighbours(self):
        for seed, maze in self.mazes.items():
            for square in maze.corridor_squares():
                self.assertGreaterEqual(
                    len(maze.corridor_neighbours(square)),
                    2,
                    "seed %d: %r is a dead end" % (seed, square),
                )

    def test_a_flood_fill_reaches_every_corridor_square(self):
        for seed, maze in self.mazes.items():
            corridors = maze.corridor_squares()
            self.assertEqual(
                set(corridors), reachable_from(maze, corridors[0]), "seed %d" % seed
            )

    def test_a_flood_fill_from_any_corridor_square_reaches_every_other(self):
        for seed in SEEDS_FLOODED_FROM_EVERY_SQUARE:
            maze = self.mazes[seed]
            everywhere = set(maze.corridor_squares())
            for start in maze.corridor_squares():
                self.assertEqual(
                    everywhere, reachable_from(maze, start), "seed %d from %r" % (seed, start)
                )

    def test_no_corridor_is_two_squares_wide(self):
        for seed, maze in self.mazes.items():
            for row in range(maze.height - 1):
                for column in range(maze.width - 1):
                    block = (
                        Square(column, row),
                        Square(column + 1, row),
                        Square(column, row + 1),
                        Square(column + 1, row + 1),
                    )
                    self.assertFalse(
                        all(maze.is_corridor(square) for square in block),
                        "seed %d: corridor is two wide at %r" % (seed, block[0]),
                    )

    def test_no_corridor_runs_diagonally(self):
        for seed, maze in self.mazes.items():
            for row in range(maze.height - 1):
                for column in range(maze.width - 1):
                    top_left = Square(column, row)
                    top_right = Square(column + 1, row)
                    bottom_left = Square(column, row + 1)
                    bottom_right = Square(column + 1, row + 1)
                    self.assertFalse(
                        maze.is_corridor(top_left)
                        and maze.is_corridor(bottom_right)
                        and maze.is_wall(top_right)
                        and maze.is_wall(bottom_left),
                        "seed %d: diagonal at %r" % (seed, top_left),
                    )
                    self.assertFalse(
                        maze.is_corridor(top_right)
                        and maze.is_corridor(bottom_left)
                        and maze.is_wall(top_left)
                        and maze.is_wall(bottom_right),
                        "seed %d: diagonal at %r" % (seed, top_right),
                    )

    def test_corridors_run_only_north_south_and_east_west(self):
        # Every way on from a corridor square is an orthogonal step of one.
        for seed, maze in self.mazes.items():
            for square in maze.corridor_squares():
                for direction, destination in maze.ways_on(square).items():
                    steps = abs(destination.column - square.column) + abs(
                        destination.row - square.row
                    )
                    self.assertEqual(1, steps, "seed %d %r %r" % (seed, square, direction))

    def test_the_grid_has_the_same_signature_as_the_specimen_picture(self):
        # Measured in docs/findings/WI-5-specimen-grid-structure.md: in the
        # specimen picture of FUNCTIONAL_REQUIREMENTS.md all 126 squares at an
        # odd column and an odd row are corridor and all 190 at an even column
        # and an even row are wall, without exception. Our mazes are the same
        # kind of maze, which is what lets WI-8 and WI-12 rely on the picture.
        for seed, maze in self.mazes.items():
            for row in range(1, maze.height, 2):
                for column in range(1, maze.width, 2):
                    self.assertTrue(
                        maze.is_corridor(Square(column, row)),
                        "seed %d: (%d, %d) is not corridor" % (seed, column, row),
                    )
            for row in range(0, maze.height, 2):
                for column in range(0, maze.width, 2):
                    self.assertTrue(
                        maze.is_wall(Square(column, row)),
                        "seed %d: (%d, %d) is not wall" % (seed, column, row),
                    )

    def test_the_maze_is_carved_right_through_and_not_a_pocket_in_one_corner(self):
        # Without a floor on how much corridor there is, a generator that
        # degenerated into one small ring in a corner would satisfy every
        # property above. A maze that reaches all 126 cells costs at least one
        # corridor square per cell plus one per joining wall opened, and a
        # spanning tree over N cells opens N - 1 walls.
        cells = CELL_COLUMNS * CELL_ROWS
        for seed, maze in self.mazes.items():
            self.assertGreaterEqual(
                len(maze.corridor_squares()), 2 * cells - 1, "seed %d" % seed
            )


class RandomnessTests(unittest.TestCase):
    """MAZE-4: laid out at random, from a source the generator is handed."""

    def test_the_same_seed_twice_gives_the_identical_maze(self):
        for seed in (0, 1, 42, 1234, 99999):
            first = generate_maze(random.Random(seed))
            second = generate_maze(random.Random(seed))
            self.assertEqual(first, second, "seed %d" % seed)
            self.assertEqual(first.to_text(), second.to_text(), "seed %d" % seed)

    def test_two_hundred_different_seeds_give_two_hundred_different_mazes(self):
        laid_out = {maze.to_text() for maze in mazes_for_every_seed().values()}
        self.assertEqual(len(SEEDS), len(laid_out))

    def test_the_generator_never_reaches_for_the_global_random_source(self):
        # Whatever the module-level generator happens to be doing, a maze laid
        # out from a seeded source is the same maze.
        saved = random.getstate()
        try:
            random.seed(1)
            first = generate_maze(random.Random(7))
            random.seed(2)
            [random.random() for _ in range(100)]
            second = generate_maze(random.Random(7))
        finally:
            random.setstate(saved)
        self.assertEqual(first, second)

    def test_the_source_it_is_handed_is_the_one_it_draws_from(self):
        # Two sources at different points in the same sequence lay out
        # different mazes, so the draws really are coming from the argument.
        advanced = random.Random(7)
        [advanced.random() for _ in range(5)]
        self.assertNotEqual(generate_maze(random.Random(7)), generate_maze(advanced))


class OtherSizeTests(unittest.TestCase):
    """The algorithm is not tuned to 19 x 29; other odd grids work too."""

    def test_the_smallest_workable_grid_satisfies_every_property(self):
        maze = generate_maze(random.Random(3), width=5, height=5)
        self.assertEqual(5, maze.width)
        self.assertEqual(5, maze.height)
        for square in maze.corridor_squares():
            self.assertGreaterEqual(len(maze.corridor_neighbours(square)), 2)
        self.assertEqual(
            set(maze.corridor_squares()),
            reachable_from(maze, maze.corridor_squares()[0]),
        )

    def test_an_oblong_grid_satisfies_every_property(self):
        for seed in range(20):
            maze = generate_maze(random.Random(seed), width=11, height=7)
            self.assertEqual(11, maze.width)
            self.assertEqual(7, maze.height)
            for square in maze.corridor_squares():
                self.assertGreaterEqual(
                    len(maze.corridor_neighbours(square)), 2, "seed %d" % seed
                )
            self.assertEqual(
                set(maze.corridor_squares()),
                reachable_from(maze, maze.corridor_squares()[0]),
                "seed %d" % seed,
            )

    def test_an_even_dimension_is_refused(self):
        with self.assertRaises(ValueError):
            generate_maze(random.Random(0), width=20, height=29)
        with self.assertRaises(ValueError):
            generate_maze(random.Random(0), width=19, height=30)

    def test_a_grid_too_small_to_avoid_dead_ends_is_refused(self):
        with self.assertRaises(ValueError):
            generate_maze(random.Random(0), width=3, height=29)
        with self.assertRaises(ValueError):
            generate_maze(random.Random(0), width=19, height=3)


if __name__ == "__main__":
    unittest.main()
