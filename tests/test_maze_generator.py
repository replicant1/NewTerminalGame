"""The generator, swept over several hundred seeds.

MAZE-2 to MAZE-6 are properties of *every* maze the generator can produce, not
of one, so the way to check them is to produce a lot of mazes and check every
one. That is what `GeneratedMazePropertiesTest` does: it lays out
`SWEEP_SEEDS` mazes once, in `setUpClass`, and each test method then walks all
of them looking for one counter-example and naming the seed that produced it.

The sweep is 400 seeds by default, which costs about a second. Set
`MAZE_SWEEP_SEEDS` to run a longer one:

    MAZE_SWEEP_SEEDS=20000 python3 -m unittest tests.test_maze_generator

The result of one long sweep is written up in
`docs/findings/WI-4-maze-invariants-over-seeds.md`.
"""

from __future__ import annotations

import os
import random
import unittest

from terminalgame.domain.maze import HEIGHT, WALL, WIDTH, Maze, solid
from terminalgame.domain.maze_generator import (
    MazeTooSmall,
    _braid,
    _carve,
    _cells_of,
    generate_maze,
    generate_maze_with,
)

#: How many seeds the ordinary run sweeps. Several hundred, per the
#: implementation plan's "tests must establish" row for WI-4.
DEFAULT_SWEEP_SEEDS = 400

SWEEP_SEEDS = int(os.environ.get("MAZE_SWEEP_SEEDS", DEFAULT_SWEEP_SEEDS))


def open_two_by_two_blocks(maze):
    """Every top-left corner of a 2 x 2 block that is corridor all through.

    A corridor two squares wide shows up as one of these, so this is MAZE-2
    stated as something that can be counted.
    """
    found = []
    for y in range(maze.height - 1):
        for x in range(maze.width - 1):
            if (maze.is_corridor(x, y) and maze.is_corridor(x + 1, y)
                    and maze.is_corridor(x, y + 1)
                    and maze.is_corridor(x + 1, y + 1)):
                found.append((x, y))
    return found


def border_breaches(maze):
    """Every square of the border ring that is corridor. MAZE-3 wants none."""
    breaches = []
    last_x = maze.width - 1
    last_y = maze.height - 1
    for x in range(maze.width):
        for y in (0, last_y):
            if maze.is_corridor(x, y):
                breaches.append((x, y))
    for y in range(maze.height):
        for x in (0, last_x):
            if maze.is_corridor(x, y):
                breaches.append((x, y))
    return sorted(set(breaches))


def dead_ends(maze):
    """Every corridor square with fewer than two ways on. MAZE-5 wants none."""
    return [(x, y) for (x, y) in maze.corridor_squares()
            if maze.ways_on(x, y) < 2]


def unreachable_squares(maze):
    """Corridor squares that cannot be walked to from the first one.

    MAZE-6 wants none. Walking from one square is enough for all of them:
    corridors are two-way, so "reachable from" is symmetric, and if every
    square is reachable from one then every square is reachable from every
    other through it.
    """
    corridors = maze.corridor_squares()
    if not corridors:
        return []
    reached = maze.reachable_from(*corridors[0])
    return [square for square in corridors if square not in reached]


def squares_off_the_lattice(maze):
    """Corridor squares with both coordinates even.

    The mechanism behind MAZE-2, and behind architecture caution C8: every
    2 x 2 block of squares contains exactly one square with both coordinates
    even, so as long as this list is empty, `open_two_by_two_blocks` cannot
    help but be empty too. Checking it separately says *why* a failure
    happened, not only that one did.
    """
    return [(x, y) for (x, y) in maze.corridor_squares()
            if x % 2 == 0 and y % 2 == 0]


def problems_with(maze):
    """Every way a maze breaks MAZE-2, MAZE-3, MAZE-5 or MAZE-6, as text."""
    problems = []
    if (maze.width, maze.height) != (WIDTH, HEIGHT):
        problems.append("size is {0} x {1}".format(maze.width, maze.height))
    for square in border_breaches(maze):
        problems.append("border breached at {0}".format(square))
    for square in open_two_by_two_blocks(maze):
        problems.append("2 x 2 open block at {0}".format(square))
    for square in dead_ends(maze):
        problems.append("dead end at {0}".format(square))
    for square in unreachable_squares(maze):
        problems.append("unreachable square {0}".format(square))
    return problems


class AlwaysFirst:
    """A random source that never chooses anything but the first option.

    Not a stub standing in for a call that is then asserted on — the tests
    using it assert on the maze that comes out. Its point is that the maze
    invariants must hold for *any* sequence of choices, including the least
    random one available, so a sweep passing cannot be luck.
    """

    def randrange(self, upper):
        return 0


class GeneratedMazePropertiesTest(unittest.TestCase):
    """MAZE-1 to MAZE-6, over several hundred generated mazes."""

    @classmethod
    def setUpClass(cls):
        cls.seeds = list(range(SWEEP_SEEDS))
        cls.mazes = [generate_maze(seed) for seed in cls.seeds]

    def each_maze(self):
        return zip(self.seeds, self.mazes)

    def test_every_maze_is_nineteen_across_and_twenty_nine_deep(self):
        # MAZE-1.
        wrong = [(seed, maze.width, maze.height)
                 for seed, maze in self.each_maze()
                 if (maze.width, maze.height) != (WIDTH, HEIGHT)]
        self.assertEqual([], wrong)

    def test_no_maze_has_a_two_by_two_block_of_open_corridor(self):
        # MAZE-2: a corridor is one square wide, so no 2 x 2 block of squares
        # is corridor all through.
        for seed, maze in self.each_maze():
            blocks = open_two_by_two_blocks(maze)
            self.assertEqual([], blocks,
                             "seed {0} has a corridor two squares wide, with "
                             "2 x 2 open blocks at {1}\n{2}"
                             .format(seed, blocks, maze.as_text()))

    def test_no_maze_opens_a_square_off_the_odd_lattice(self):
        # Caution C8's mechanism, checked directly so that a failure of
        # MAZE-2 says where the restriction was lost.
        for seed, maze in self.each_maze():
            off = squares_off_the_lattice(maze)
            self.assertEqual([], off,
                             "seed {0} opened squares with both coordinates "
                             "even at {1}; the carve and the braid must both "
                             "stay on the odd lattice (caution C8)"
                             .format(seed, off))

    def test_every_maze_has_a_solid_wall_right_around_the_outside(self):
        # MAZE-3: nothing can leave the maze, and there are no tunnels
        # through the sides.
        for seed, maze in self.each_maze():
            breaches = border_breaches(maze)
            self.assertEqual([], breaches,
                             "seed {0} breaches the border ring at {1}\n{2}"
                             .format(seed, breaches, maze.as_text()))

    def test_every_maze_has_all_four_sides_of_the_border_intact(self):
        # The check above would also pass if a side were missing entirely
        # from the walk. This pins each side separately.
        for seed, maze in self.each_maze():
            top = [maze.square_at(x, 0) for x in range(maze.width)]
            bottom = [maze.square_at(x, maze.height - 1)
                      for x in range(maze.width)]
            left = [maze.square_at(0, y) for y in range(maze.height)]
            right = [maze.square_at(maze.width - 1, y)
                     for y in range(maze.height)]
            self.assertEqual([WALL] * maze.width, top, "seed {0} top".format(seed))
            self.assertEqual([WALL] * maze.width, bottom,
                             "seed {0} bottom".format(seed))
            self.assertEqual([WALL] * maze.height, left,
                             "seed {0} left".format(seed))
            self.assertEqual([WALL] * maze.height, right,
                             "seed {0} right".format(seed))

    def test_no_maze_has_a_dead_end(self):
        # MAZE-5: from any corridor square there are always at least two ways
        # on, so the player is never trapped in a pocket.
        for seed, maze in self.each_maze():
            ends = dead_ends(maze)
            self.assertEqual([], ends,
                             "seed {0} has dead ends at {1}\n{2}"
                             .format(seed, ends, maze.as_text()))

    def test_every_corridor_square_is_reachable_from_every_other(self):
        # MAZE-6: no dot is unreachable.
        for seed, maze in self.each_maze():
            stranded = unreachable_squares(maze)
            self.assertEqual([], stranded,
                             "seed {0} strands {1} corridor squares: {2}\n{3}"
                             .format(seed, len(stranded), stranded[:5],
                                     maze.as_text()))

    def test_reachability_holds_starting_from_any_square_not_just_the_first(self):
        # The sweep above walks from one square per maze. This confirms on a
        # handful of mazes that the choice of starting square makes no
        # difference, which is what "from every other" actually asks.
        for seed, maze in list(self.each_maze())[:5]:
            everything = set(maze.corridor_squares())
            for square in sorted(everything)[::17]:
                self.assertEqual(everything, maze.reachable_from(*square),
                                 "seed {0}, from {1}".format(seed, square))

    def test_every_maze_has_plenty_of_corridor_in_it(self):
        # A grid of all wall satisfies MAZE-2, MAZE-3, MAZE-5 and MAZE-6
        # vacuously — no square, no dead end, nothing unreachable. This is
        # what stops the sweep above being satisfied by nothing at all.
        for seed, maze in self.each_maze():
            corridors = len(maze.corridor_squares())
            self.assertGreater(corridors, 200,
                               "seed {0} has only {1} corridor squares"
                               .format(seed, corridors))
            self.assertLess(corridors, WIDTH * HEIGHT)

    def test_different_seeds_give_different_mazes(self):
        # MAZE-4: no two games are the same.
        layouts = set(maze.as_text() for maze in self.mazes)
        self.assertEqual(len(self.mazes), len(layouts),
                         "{0} seeds produced only {1} distinct layouts"
                         .format(len(self.mazes), len(layouts)))


class ReproducibilityTest(unittest.TestCase):
    """A seed names a maze, so a failure can be looked at again."""

    def test_the_same_seed_gives_the_same_maze_twice(self):
        self.assertEqual(generate_maze(1234), generate_maze(1234))
        self.assertEqual(generate_maze(1234).as_text(),
                         generate_maze(1234).as_text())

    def test_the_same_seed_gives_the_same_maze_after_other_mazes(self):
        # The generator must not carry state between calls, or a maze would
        # depend on how many were made before it and a seed would stop
        # naming anything.
        first = generate_maze(99)
        for seed in range(20):
            generate_maze(seed)
        self.assertEqual(first, generate_maze(99))

    def test_a_neighbouring_seed_gives_a_different_maze(self):
        self.assertNotEqual(generate_maze(1234), generate_maze(1235))

    def test_an_injected_random_source_gives_the_same_maze_as_its_seed(self):
        # `generate_maze_with` is the door a caller that owns the whole
        # game's randomness comes through; it must be the same generator.
        self.assertEqual(generate_maze(4321),
                         generate_maze_with(random.Random(4321)))

    def test_no_seed_at_all_still_gives_a_maze_that_meets_the_requirements(self):
        # MAZE-4 in its everyday form: a game starting with no seed gets a
        # fresh layout, and it is a real maze.
        maze = generate_maze()
        self.assertEqual([], problems_with(maze))

    def test_asking_repeatedly_with_no_seed_does_not_give_the_same_maze(self):
        # The chance of ten unseeded layouts colliding is negligible: seed
        # 0..399 alone gave 400 distinct layouts.
        layouts = set(generate_maze().as_text() for _ in range(10))
        self.assertGreater(len(layouts), 1)


class ChoiceIndependenceTest(unittest.TestCase):
    """The invariants are the algorithm's, not the random source's luck."""

    def test_a_source_that_never_chooses_randomly_still_gives_a_real_maze(self):
        maze = generate_maze_with(AlwaysFirst())
        self.assertEqual([], problems_with(maze))

    def test_that_maze_is_the_same_every_time_because_nothing_is_random(self):
        self.assertEqual(generate_maze_with(AlwaysFirst()),
                         generate_maze_with(AlwaysFirst()))


class OtherGridSizesTest(unittest.TestCase):
    """19 x 29 is the specification; the algorithm is not about those numbers."""

    SIZES = [(5, 5), (7, 5), (5, 11), (9, 9), (21, 21), (19, 29), (29, 19),
             (11, 7), (13, 31)]

    def test_the_invariants_hold_at_every_odd_size_that_fits_a_maze(self):
        for width, height in self.SIZES:
            maze = generate_maze(seed=7, width=width, height=height)
            self.assertEqual((width, height), (maze.width, maze.height))
            self.assertEqual([], border_breaches(maze), (width, height))
            self.assertEqual([], open_two_by_two_blocks(maze), (width, height))
            self.assertEqual([], dead_ends(maze), (width, height))
            self.assertEqual([], unreachable_squares(maze), (width, height))
            self.assertGreater(len(maze.corridor_squares()), 0, (width, height))

    def test_an_even_dimension_is_refused_rather_than_losing_the_border(self):
        # An even width would put the last lattice cell hard against the right
        # edge and MAZE-3 could not hold.
        with self.assertRaises(MazeTooSmall):
            generate_maze(seed=1, width=20, height=29)
        with self.assertRaises(MazeTooSmall):
            generate_maze(seed=1, width=19, height=30)

    def test_a_grid_too_narrow_for_two_cells_is_refused(self):
        # A single column of cells has cells with one neighbour, and no braid
        # can give them a second way on, so MAZE-5 could not hold. Refused
        # loudly rather than returned with a dead end in it.
        with self.assertRaises(MazeTooSmall):
            generate_maze(seed=1, width=3, height=29)
        with self.assertRaises(MazeTooSmall):
            generate_maze(seed=1, width=19, height=3)

    def test_the_lattice_of_the_specified_grid_is_nine_cells_by_fourteen(self):
        cells = _cells_of(WIDTH, HEIGHT)
        self.assertEqual(9 * 14, len(cells))
        self.assertEqual((1, 1), cells[0])
        self.assertEqual((WIDTH - 2, HEIGHT - 2), cells[-1])
        self.assertTrue(all(x % 2 == 1 and y % 2 == 1 for x, y in cells))


class TheTwoPassesTest(unittest.TestCase):
    """The carve and the braid, looked at one at a time.

    Worth doing separately because "no dead ends" over a sweep would read the
    same whether the braid were doing the work or whether the carve happened
    never to produce a dead end. It does produce them, in quantity; these
    tests say so.
    """

    def setUp(self):
        self.cells = _cells_of(WIDTH, HEIGHT)

    def carved(self, seed):
        grid = solid(WIDTH, HEIGHT)
        _carve(grid, self.cells, random.Random(seed))
        return grid

    def test_the_carve_alone_leaves_dead_ends(self):
        # A spanning tree has leaves. If this ever came back empty, the
        # sweep's zero-dead-ends result would be telling us nothing.
        for seed in range(20):
            self.assertGreater(len(dead_ends(Maze(self.carved(seed)))), 0,
                               "seed {0}".format(seed))

    def test_the_carve_alone_is_already_connected(self):
        # The carve is what delivers MAZE-6; the braid only adds to it.
        for seed in range(20):
            self.assertEqual([], unreachable_squares(Maze(self.carved(seed))),
                             "seed {0}".format(seed))

    def test_the_carve_visits_every_cell_of_the_lattice(self):
        maze = Maze(self.carved(3))
        for (x, y) in self.cells:
            self.assertTrue(maze.is_corridor(x, y), (x, y))

    def test_the_carve_opens_exactly_one_connector_per_cell_after_the_first(self):
        # That is what makes it a spanning tree rather than something with
        # loops in it, and it is why the carve has dead ends to open out.
        maze = Maze(self.carved(3))
        connectors = [(x, y) for (x, y) in maze.corridor_squares()
                      if (x % 2 == 0) != (y % 2 == 0)]
        self.assertEqual(len(self.cells) - 1, len(connectors))

    def test_the_braid_removes_every_dead_end_the_carve_left(self):
        for seed in range(20):
            grid = self.carved(seed)
            before = len(dead_ends(Maze(grid)))
            _braid(grid, self.cells, random.Random(seed))
            after = len(dead_ends(Maze(grid)))
            self.assertGreater(before, 0, "seed {0}".format(seed))
            self.assertEqual(0, after, "seed {0}".format(seed))

    def test_the_braid_only_ever_opens_squares_and_never_closes_one(self):
        # Opening is what makes the braid safe: it cannot disconnect anything
        # the carve connected, and it cannot create the dead end it is
        # removing somewhere else.
        grid = self.carved(5)
        before = set(Maze(grid).corridor_squares())
        _braid(grid, self.cells, random.Random(5))
        after = set(Maze(grid).corridor_squares())
        self.assertEqual(set(), before - after)
        self.assertGreater(len(after - before), 0)

    def test_the_braid_stays_on_the_lattice(self):
        # Caution C8 exactly: the braid is the pass that would wander off the
        # lattice and make a 2 x 2 open block if it were not held there.
        for seed in range(20):
            grid = self.carved(seed)
            _braid(grid, self.cells, random.Random(seed))
            maze = Maze(grid)
            self.assertEqual([], squares_off_the_lattice(maze),
                             "seed {0}".format(seed))
            self.assertEqual([], open_two_by_two_blocks(maze),
                             "seed {0}".format(seed))


class SweepSizeTest(unittest.TestCase):

    def test_the_ordinary_run_sweeps_several_hundred_seeds(self):
        # The plan's WI-4 row says "over several hundred seeds". If someone
        # trims the default to make the suite faster, this says so.
        self.assertGreaterEqual(DEFAULT_SWEEP_SEEDS, 300)


if __name__ == "__main__":
    unittest.main()
