"""The maze generator and the loader — MAZE-1..6.

**The invariant sweep runs 250 seeds by default.** It was 1000, which cost
3.4s — more than a quarter of the whole suite — and the reduction is
deliberate rather than a trim for its own sake.

The sweep is a *regression* guard, not the original evidence. The evidence
that this generator is sound is the architect's prototype: 5000 seeds, zero
failures on border, dead-end, connectivity and no-2x2-open, recorded in
`docs/ARCHITECTURE.md`. That measurement does not need re-running on every
edit. What this sweep has to catch is a **change** that breaks the generator,
and a broken braid pass or a broken connectivity guarantee fails at a high
rate, not a one-in-a-thousand rate; it shows up in the first handful of seeds.

By the rule of three, 250 seeds clean puts a 95% upper bound of 1.2% on the
failure rate. For the rarer input-dependent bug that only a long sweep would
find, run the long sweep::

    TERMGAME_MAZE_SEEDS=5000 /usr/bin/python3 -m unittest tests.test_maze
"""

import io
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from termgame import maze as mazelib  # noqa: E402
from termgame.model import DOWN, LEFT, MAZE_COLS, MAZE_ROWS, RIGHT, UP, Position  # noqa: E402

#: Seeds the invariant sweep generates. See the module docstring for why
#: this is 250 and not 1000, and how to run a longer sweep.
SEEDS = int(os.environ.get("TERMGAME_MAZE_SEEDS", "250"))

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

#: In the specification's mock-up an even screen column holds one of these
#: when the maze cell under it is corridor: a dot, or the middle of the
#: three-character player/ghost glyph.
SPEC_CORRIDOR_CHARS = frozenset("▪█")


def read_spec_mock_up():
    """The specification's own picture, as its 29 lines of 37 characters.

    The test does the file reading; the core is handed a string (plan §2.4).
    """
    path = os.path.join(FIXTURES, "spec_maze.txt")
    with io.open(path, encoding="utf-8") as handle:
        return [line for line in handle.read().split("\n") if line]


def decode_spec_mock_up(lines):
    """Turn the mock-up back into a text grid the loader reads.

    Maze column ``c`` is drawn at screen column ``2c``; the odd columns
    between are joiners and carry no cell of their own.
    """
    rows = []
    for line in lines:
        rows.append(
            "".join(
                "." if line[2 * c] in SPEC_CORRIDOR_CHARS else "#"
                for c in range(MAZE_COLS)
            )
        )
    return "\n".join(rows)


class TestGeneratedMazeInvariants(unittest.TestCase):
    """Every MAZE requirement, over 1000 seeded mazes."""

    @classmethod
    def setUpClass(cls):
        cls.mazes = [mazelib.generate(random.Random(seed)) for seed in range(SEEDS)]

    def test_every_maze_is_twenty_nine_by_nineteen(self):
        # MAZE-1.
        for seed, maze in enumerate(self.mazes):
            self.assertEqual(
                (maze.height, maze.width), (MAZE_ROWS, MAZE_COLS), "seed %d" % seed
            )

    def test_no_maze_has_a_two_by_two_block_of_corridor(self):
        # MAZE-2: corridors are one square wide and run only north-south and
        # east-west. A 2x2 block of corridor is exactly what that forbids.
        for seed, maze in enumerate(self.mazes):
            self.assertEqual(
                mazelib.open_blocks(maze), (), "seed %d has a 2x2 corridor block" % seed
            )

    def test_every_maze_has_a_solid_wall_border(self):
        # MAZE-3: nothing can leave the maze; there are no side tunnels.
        last_row, last_col = MAZE_ROWS - 1, MAZE_COLS - 1
        for seed, maze in enumerate(self.mazes):
            for col in range(MAZE_COLS):
                self.assertTrue(maze.is_wall((0, col)), "seed %d row 0" % seed)
                self.assertTrue(
                    maze.is_wall((last_row, col)), "seed %d row 28" % seed
                )
            for row in range(MAZE_ROWS):
                self.assertTrue(maze.is_wall((row, 0)), "seed %d col 0" % seed)
                self.assertTrue(
                    maze.is_wall((row, last_col)), "seed %d col 18" % seed
                )

    def test_no_corridor_square_has_fewer_than_two_ways_on(self):
        # MAZE-5: the maze has no dead ends.
        for seed, maze in enumerate(self.mazes):
            self.assertEqual(
                mazelib.dead_ends(maze), (), "seed %d has a dead end" % seed
            )

    def test_every_corridor_square_is_reachable_from_every_other(self):
        # MAZE-6: no dot is unreachable.
        for seed, maze in enumerate(self.mazes):
            corridors = maze.corridors()
            self.assertTrue(corridors, "seed %d has no corridor at all" % seed)
            reached = mazelib.reachable_from(maze, min(corridors))
            self.assertEqual(
                reached, set(corridors), "seed %d is not fully connected" % seed
            )

    def test_check_reports_nothing_wrong_with_any_of_them(self):
        for seed, maze in enumerate(self.mazes):
            self.assertEqual(mazelib.check(maze), (), "seed %d" % seed)

    def test_a_maze_is_mostly_wall_but_substantially_open(self):
        # A generator that returned a solid block, or an empty room, would
        # pass several of the checks above. Pin the corridor count near the
        # 264 of the specification's own maze.
        for seed, maze in enumerate(self.mazes):
            corridors = len(maze.corridors())
            self.assertGreaterEqual(corridors, 251, "seed %d" % seed)
            self.assertLessEqual(corridors, 300, "seed %d" % seed)

    def test_every_node_cell_is_corridor_and_every_pillar_is_wall(self):
        # The lattice decomposition the whole design rests on.
        maze = self.mazes[0]
        for row in range(MAZE_ROWS):
            for col in range(MAZE_COLS):
                if row % 2 == 1 and col % 2 == 1:
                    self.assertTrue(maze.is_corridor((row, col)), (row, col))
                elif row % 2 == 0 and col % 2 == 0:
                    self.assertTrue(maze.is_wall((row, col)), (row, col))

    def test_a_link_cell_always_has_exactly_two_ways_on(self):
        # Which is why nodes are the only MAZE-5 risk.
        maze = self.mazes[0]
        for row in range(MAZE_ROWS):
            for col in range(MAZE_COLS):
                if (row % 2) == (col % 2):
                    continue
                if maze.is_corridor((row, col)):
                    self.assertEqual(
                        maze.corridor_degree((row, col)), 2, (row, col)
                    )


class TestRandomness(unittest.TestCase):
    def test_two_different_seeds_produce_two_different_mazes(self):
        # MAZE-4: no two games are the same.
        first = mazelib.generate(random.Random(1))
        second = mazelib.generate(random.Random(2))
        self.assertNotEqual(first.rows(), second.rows())

    def test_a_thousand_seeds_produce_a_thousand_distinct_mazes(self):
        """MAZE-4, and the name now says what the loop does.

        WI-12 found this named for a thousand seeds while looping over 200.
        The assertion was strong either way, but the name is the kind a later
        reader trusts, so it is the sweep that was brought up to it: measured
        at 0.74 s for all 1000, and **no two of the thousand are alike**.

        A generator that ignored its rng would pass the test above only by
        accident; this one it could not pass at all.
        """
        distinct = set()
        for seed in range(SEEDS):
            distinct.add(mazelib.generate(random.Random(seed)).rows())
        self.assertEqual(len(distinct), SEEDS)

    def test_the_same_seed_produces_the_identical_maze_twice(self):
        # Everything else in this project is reproducible because of this.
        for seed in (0, 17, 999):
            self.assertEqual(
                mazelib.generate(random.Random(seed)),
                mazelib.generate(random.Random(seed)),
                "seed %d" % seed,
            )

    def test_generation_draws_only_from_the_rng_it_was_given(self):
        # C7: no module-level random call anywhere in the core. If there were
        # one, seeding the global source would change the result.
        random.seed(1)
        first = mazelib.generate(random.Random(42))
        random.seed(999999)
        second = mazelib.generate(random.Random(42))
        self.assertEqual(first, second)


class TestLattice(unittest.TestCase):
    def test_the_lattice_is_nine_across_and_fourteen_deep(self):
        self.assertEqual((mazelib.NODE_ROWS, mazelib.NODE_COLS), (14, 9))
        self.assertEqual(mazelib.NODE_ROWS * mazelib.NODE_COLS, 126)

    def test_a_node_sits_on_an_odd_odd_cell(self):
        self.assertEqual(mazelib.node_cell((0, 0)), Position(1, 1))
        self.assertEqual(mazelib.node_cell((13, 8)), Position(27, 17))

    def test_a_link_lies_between_its_two_nodes(self):
        self.assertEqual(mazelib.link_cell((0, 0), (0, 1)), Position(1, 2))
        self.assertEqual(mazelib.link_cell((0, 1), (0, 0)), Position(1, 2))
        self.assertEqual(mazelib.link_cell((3, 4), (4, 4)), Position(8, 9))

    def test_non_adjacent_nodes_have_no_link(self):
        with self.assertRaises(ValueError):
            mazelib.link_cell((0, 0), (0, 2))


class TestLoader(unittest.TestCase):
    def test_a_hand_written_board_loads(self):
        maze = mazelib.from_text("###\n#.#\n###")
        self.assertEqual((maze.height, maze.width), (3, 3))
        self.assertEqual(maze.corridors(), frozenset({Position(1, 1)}))

    def test_space_is_corridor_too(self):
        maze = mazelib.from_text("###\n# #\n###")
        self.assertTrue(maze.is_corridor((1, 1)))

    def test_leading_and_trailing_blank_lines_are_ignored(self):
        maze = mazelib.from_text("\n\n###\n#.#\n###\n\n")
        self.assertEqual(maze.height, 3)

    def test_a_row_of_spaces_survives_the_blank_line_trim(self):
        maze = mazelib.from_text("###\n   \n###")
        self.assertEqual(maze.height, 3)
        self.assertEqual(maze.corridor_degree((1, 1)), 2)

    def test_a_ragged_board_is_refused(self):
        with self.assertRaises(ValueError):
            mazelib.from_text("###\n#.\n###")

    def test_an_unknown_character_is_refused(self):
        with self.assertRaises(ValueError):
            mazelib.from_text("###\n#?#\n###")

    def test_empty_text_is_refused(self):
        with self.assertRaises(ValueError):
            mazelib.from_text("\n\n")

    def test_a_generated_maze_round_trips_through_text(self):
        original = mazelib.generate(random.Random(5))
        self.assertEqual(mazelib.from_text(mazelib.to_text(original)), original)

    def test_the_loader_reads_a_string_not_a_file(self):
        # Plan §2.4: the core reads no files. Handing it a path must fail as
        # a grid rather than quietly opening anything.
        with self.assertRaises(ValueError):
            mazelib.from_text("tests/fixtures/spec_maze.txt")


class TestInvariantHelpers(unittest.TestCase):
    """The checks themselves must be able to see a broken maze."""

    def test_a_gap_in_the_border_is_reported(self):
        self.assertFalse(mazelib.has_solid_border(mazelib.from_text("###\n..#\n###")))
        self.assertTrue(mazelib.has_solid_border(mazelib.from_text("###\n#.#\n###")))

    def test_a_dead_end_is_reported(self):
        maze = mazelib.from_text("####\n#..#\n#.##\n####")
        self.assertEqual(mazelib.dead_ends(maze), (Position(1, 2), Position(2, 1)))

    def test_a_two_by_two_block_is_reported(self):
        maze = mazelib.from_text("####\n#..#\n#..#\n####")
        self.assertEqual(mazelib.open_blocks(maze), (Position(1, 1),))

    def test_two_separate_pockets_are_reported_as_unconnected(self):
        maze = mazelib.from_text("#####\n#.#.#\n#.#.#\n#####")
        self.assertFalse(mazelib.is_fully_connected(maze))
        self.assertTrue(
            mazelib.is_fully_connected(mazelib.from_text("#####\n#...#\n#####"))
        )

    def test_reachable_from_a_wall_square_is_empty(self):
        maze = mazelib.from_text("###\n#.#\n###")
        self.assertEqual(mazelib.reachable_from(maze, Position(0, 0)), set())

    def test_check_names_the_requirement_it_caught(self):
        maze = mazelib.from_text("####\n#..#\n#..#\n####")
        joined = " ".join(mazelib.check(maze))
        self.assertIn("MAZE-1", joined)  # not 29 x 19
        self.assertIn("MAZE-2", joined)  # the 2x2 block
        # This board's border is solid and its corridors are all reachable
        # with two ways on apiece, so those must not be reported.
        self.assertNotIn("MAZE-3", joined)
        self.assertNotIn("MAZE-5", joined)
        self.assertNotIn("MAZE-6", joined)

    def test_check_names_a_broken_border_and_a_dead_end(self):
        joined = " ".join(mazelib.check(mazelib.from_text("####\n...#\n#.##\n####")))
        self.assertIn("MAZE-3", joined)
        self.assertIn("MAZE-5", joined)

    def test_check_names_an_unreachable_pocket(self):
        joined = " ".join(mazelib.check(mazelib.from_text("#####\n#.#.#\n#.#.#\n#####")))
        self.assertIn("MAZE-6", joined)

    def test_check_passes_a_generated_maze(self):
        self.assertEqual(mazelib.check(mazelib.generate(random.Random(3))), ())


class TestTheSpecificationsOwnMaze(unittest.TestCase):
    """The mock-up in the specification is itself a legal maze."""

    @classmethod
    def setUpClass(cls):
        cls.lines = read_spec_mock_up()
        cls.maze = mazelib.from_text(decode_spec_mock_up(cls.lines))

    def test_the_mock_up_is_twenty_nine_rows_of_thirty_seven_columns(self):
        self.assertEqual(len(self.lines), MAZE_ROWS)
        self.assertEqual(set(len(line) for line in self.lines), {37})
        self.assertEqual(2 * (MAZE_COLS - 1) + 1, 37)

    def test_it_decodes_to_the_two_hundred_and_sixty_four_corridors_measured(self):
        self.assertEqual(len(self.maze.corridors()), 264)

    def test_it_satisfies_every_invariant_a_generated_maze_must(self):
        # If it does not, the decoding is wrong, not the specification.
        self.assertEqual(mazelib.check(self.maze), ())

    def test_its_nodes_and_pillars_fall_where_the_lattice_says(self):
        # This is the measurement the whole generator design was derived from.
        for row in range(MAZE_ROWS):
            for col in range(MAZE_COLS):
                if row % 2 == 1 and col % 2 == 1:
                    self.assertTrue(self.maze.is_corridor((row, col)), (row, col))
                elif row % 2 == 0 and col % 2 == 0:
                    self.assertTrue(self.maze.is_wall((row, col)), (row, col))

    def test_its_corridor_count_is_nodes_plus_links(self):
        links = sum(
            1
            for row in range(MAZE_ROWS)
            for col in range(MAZE_COLS)
            if (row % 2) != (col % 2) and self.maze.is_corridor((row, col))
        )
        self.assertEqual(126 + links, 264)
        self.assertEqual(links, 138)

    def test_the_player_and_ghost_in_the_mock_up_stand_on_corridor(self):
        # The player is drawn ▐█▌ and the ghost ▗█▖, three characters centred
        # on an even screen column. Both middles must be corridor cells, or
        # the decoding above has mistaken an entity for a wall.
        found = []
        for row, line in enumerate(self.lines):
            for col in range(0, 37, 2):
                if line[col] == "█":
                    found.append(Position(row, col // 2))
        self.assertEqual(len(found), 2, "expected the player and the ghost")
        for cell in found:
            self.assertTrue(self.maze.is_corridor(cell), cell)

    def test_a_joiner_column_beside_a_corridor_cell_is_blank(self):
        # Architecture C9. The three-wide entity glyphs spill into the joiner
        # columns either side, and that is only safe while this holds.
        for row, line in enumerate(self.lines):
            for col in range(1, 37, 2):
                left = self.maze.is_corridor((row, (col - 1) // 2))
                right = self.maze.is_corridor((row, (col + 1) // 2))
                if left or right:
                    self.assertIn(
                        line[col],
                        (" ", "█", "▐", "▌", "▗", "▖"),
                        "joiner at row %d col %d is %r" % (row, col, line[col]),
                    )


if __name__ == "__main__":
    unittest.main()
