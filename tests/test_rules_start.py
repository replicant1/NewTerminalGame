"""Starting a game — START-1..5, the work of ``termgame.rules``.

**How the placement assertions are written, and why it matters.**

The implementation plan is explicit that the player's and the ghost's
placement must be asserted *by exhaustive recount over the board*, not by
recomputing with the same expression the code uses. A test that re-derives
``min(corridors, key=...)`` proves only that the formula equals itself, and
would pass just as happily against a formula that was wrong.

So every placement test below:

* walks the whole grid **by index**, asking ``maze.is_corridor((r, c))`` cell
  by cell. It never iterates ``maze.corridors()``, and it never calls
  ``rules.starting_player``, ``rules.starting_ghost``, ``rules.centre_of`` or
  ``rules.squared_distance``;
* writes the distance out **longhand with literal numbers** — the centre
  ``(14, 9)`` appears in the test as the digits 14 and 9, pinned here rather
  than borrowed from the module;
* asserts a **property of every cell** rather than an equality against a
  recomputation: no corridor square is strictly nearer the centre than the
  player's, and any square that ties sits at a higher ``(row, col)``.

Two hand-written boards force the tie-breaks, and both are checked by hand in
their own docstrings.
"""

import inspect
import random
import unittest

from termgame import maze as mazelib
from termgame import rules
from termgame.model import (
    DIRECTIONS,
    MAZE_COLS,
    MAZE_ROWS,
    GAME_STATE_FIELDS,
    Outcome,
    Position,
)

#: How many seeds the "over many seeds" tests sweep. Each one generates a
#: maze and recounts 551 cells, so this is a couple of seconds all told.
SEEDS = range(200)

#: The middle of the real 29 x 19 board, written out here as literal numbers
#: so that these tests pin it rather than take the module's word for it.
CENTRE_ROW = 14
CENTRE_COL = 9


# --------------------------------------------------------------------------
# The recount
# --------------------------------------------------------------------------


class _Recount(object):
    """Everything these tests need, counted off the grid one cell at a time.

    Deliberately dumb. It walks every ``(row, col)`` in range and asks the
    maze about that one cell, so nothing here inherits a set, a count or a
    comparator from the code under test.
    """

    def __init__(self, state):
        maze = state.maze
        self.height = maze.height
        self.width = maze.width
        self.corridor_cells = []
        self.wall_cells = []
        for row in range(self.height):
            for col in range(self.width):
                if maze.is_corridor((row, col)):
                    self.corridor_cells.append((row, col))
                else:
                    self.wall_cells.append((row, col))
        self.corridor_count = len(self.corridor_cells)

    def centre_distances(self, centre_row, centre_col):
        """``{cell: squared distance to the centre}`` for every corridor cell."""
        return dict(
            ((row, col), (row - centre_row) ** 2 + (col - centre_col) ** 2)
            for row, col in self.corridor_cells
        )

    def distances_from(self, origin):
        """``{cell: squared distance from origin}`` for every corridor cell."""
        origin_row, origin_col = origin
        return dict(
            ((row, col), (row - origin_row) ** 2 + (col - origin_col) ** 2)
            for row, col in self.corridor_cells
        )


def _states(seeds=SEEDS):
    """``(seed, state)`` for each seed, one fresh game apiece."""
    for seed in seeds:
        yield seed, rules.new_game(random.Random(seed))


# --------------------------------------------------------------------------
# START-1 — the player is nearest the middle
# --------------------------------------------------------------------------


class PlayerPlacementTests(unittest.TestCase):
    """START-1, asserted by recount over every square of the board."""

    def test_player_stands_on_a_corridor_square(self):
        for seed, state in _states():
            row, col = state.player
            self.assertTrue(
                state.maze.is_corridor((row, col)),
                "seed %d: the player is on a wall at (%d, %d)" % (seed, row, col),
            )

    def test_player_is_inside_the_grid(self):
        for seed, state in _states():
            row, col = state.player
            self.assertTrue(
                0 <= row < MAZE_ROWS and 0 <= col < MAZE_COLS,
                "seed %d: the player is off the board at (%d, %d)" % (seed, row, col),
            )

    def test_no_corridor_square_is_nearer_the_middle_than_the_players(self):
        """START-1 by exhaustive recount, ties included.

        For every one of the 551 squares: if it is corridor, then either it
        is strictly further from ``(14, 9)`` than the player's square, or it
        is exactly as far and sits at a higher ``(row, col)``.
        """
        for seed, state in _states():
            recount = _Recount(state)
            distances = recount.centre_distances(CENTRE_ROW, CENTRE_COL)
            player = (state.player.row, state.player.col)
            self.assertIn(
                player, distances, "seed %d: the player is not on a corridor" % seed
            )
            chosen = distances[player]
            for cell, distance in distances.items():
                if cell == player:
                    continue
                if distance < chosen:
                    self.fail(
                        "seed %d: %r is %d from the middle but the player took %r "
                        "at %d — a nearer corridor square was passed over"
                        % (seed, cell, distance, player, chosen)
                    )
                if distance == chosen and cell < player:
                    self.fail(
                        "seed %d: %r ties with the player's %r at distance %d but "
                        "is the lower (row, col) — the tie was broken the wrong way"
                        % (seed, cell, player, chosen)
                    )

    def test_player_ties_really_do_occur_on_the_generated_board(self):
        """The low-(row, col) branch is not dead code on the real board.

        The exact middle ``(14, 9)`` is a link cell of the lattice, so on many
        seeds it is a wall and the two node squares above and below it tie at
        distance 1. If this ever found no tie at all, the tie-break above
        would be untested on generated mazes and the hand-written boards would
        be carrying it alone.
        """
        seeds_with_a_tie = 0
        for _seed, state in _states():
            recount = _Recount(state)
            distances = recount.centre_distances(CENTRE_ROW, CENTRE_COL)
            chosen = distances[(state.player.row, state.player.col)]
            if sum(1 for d in distances.values() if d == chosen) > 1:
                seeds_with_a_tie += 1
        self.assertGreater(
            seeds_with_a_tie,
            0,
            "no seed in %d produced a tie for nearest the middle" % len(SEEDS),
        )


# --------------------------------------------------------------------------
# START-2 — the ghost is furthest from the player, across the grid
# --------------------------------------------------------------------------


class GhostPlacementTests(unittest.TestCase):
    """START-2, asserted by recount. **Assumption A2, not a ruling.**

    §9's A2 is open: START-2's "measured across the grid" rules out path
    distance but does not say which straight-line metric. These tests are
    written against the plan's recorded assumption — **squared Euclidean on
    ``(row, col)``** — with the arithmetic written out longhand below. If the
    user answers Manhattan or Chebyshev, this class and one expression in
    ``rules`` are the whole of the change.
    """

    def test_ghost_stands_on_a_corridor_square(self):
        for seed, state in _states():
            row, col = state.ghost
            self.assertTrue(
                state.maze.is_corridor((row, col)),
                "seed %d: the ghost is on a wall at (%d, %d)" % (seed, row, col),
            )

    def test_ghost_does_not_start_on_top_of_the_player(self):
        for seed, state in _states():
            self.assertNotEqual(
                state.ghost,
                state.player,
                "seed %d: the ghost started on the player's square" % seed,
            )

    def test_no_corridor_square_is_further_from_the_player_than_the_ghosts(self):
        """START-2 by exhaustive recount, ties included.

        For every square of the board: if it is corridor, then either it is
        strictly nearer the player than the ghost's square, or it is exactly
        as far and sits at a higher ``(row, col)``. The distance is written
        out here as ``(r - pr) ** 2 + (c - pc) ** 2`` rather than taken from
        the module.
        """
        for seed, state in _states():
            recount = _Recount(state)
            player = (state.player.row, state.player.col)
            distances = recount.distances_from(player)
            ghost = (state.ghost.row, state.ghost.col)
            self.assertIn(
                ghost, distances, "seed %d: the ghost is not on a corridor" % seed
            )
            chosen = distances[ghost]
            for cell, distance in distances.items():
                if cell == ghost:
                    continue
                if distance > chosen:
                    self.fail(
                        "seed %d: %r is %d from the player but the ghost took %r "
                        "at %d — a further corridor square was passed over"
                        % (seed, cell, distance, ghost, chosen)
                    )
                if distance == chosen and cell < ghost:
                    self.fail(
                        "seed %d: %r ties with the ghost's %r at distance %d but "
                        "is the lower (row, col) — the tie was broken the wrong way"
                        % (seed, cell, ghost, chosen)
                    )

    def test_ghost_ties_really_do_occur_on_the_generated_board(self):
        """The low-(row, col) branch is not dead code for the ghost either.

        Measured: a tie for furthest occurs on **every one** of the seeds
        swept here, because squared Euclidean distance collides freely —
        ``(a, b)`` and ``(b, a)`` offsets from the player are the same
        distance. So the tie rule asserted above is doing real work on every
        generated board rather than on a rare one.
        """
        seeds_with_a_tie = 0
        for _seed, state in _states():
            recount = _Recount(state)
            distances = recount.distances_from((state.player.row, state.player.col))
            chosen = distances[(state.ghost.row, state.ghost.col)]
            if sum(1 for d in distances.values() if d == chosen) > 1:
                seeds_with_a_tie += 1
        self.assertEqual(
            seeds_with_a_tie,
            len(SEEDS),
            "a tie for furthest was expected on every seed, found %d of %d"
            % (seeds_with_a_tie, len(SEEDS)),
        )

    def test_the_ghost_is_measured_across_the_grid_and_not_along_the_corridors(self):
        """START-2's "rather than along the corridors" has teeth.

        A path-distance ghost and a straight-line ghost are not the same
        square on a generated maze. This finds at least one seed where the
        corridor square that is furthest by *flood fill from the player*
        differs from the square the code chose, which is what would break if
        somebody quietly swapped the metric for a breadth-first search.
        """
        disagreements = 0
        for _seed, state in _states(range(40)):
            furthest_along_corridors = self._furthest_by_flood_fill(state)
            if state.ghost not in furthest_along_corridors:
                disagreements += 1
        self.assertGreater(
            disagreements,
            0,
            "on every seed the straight-line ghost coincided with the "
            "furthest-along-the-corridors ghost, so this test proves nothing",
        )

    @staticmethod
    def _furthest_by_flood_fill(state):
        """Every corridor square at the greatest number of steps from the player.

        A plain breadth-first search written here in the test. It exists only
        to show that the two metrics genuinely differ.
        """
        maze = state.maze
        start = (state.player.row, state.player.col)
        steps = {start: 0}
        frontier = [start]
        while frontier:
            nxt = []
            for row, col in frontier:
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    cell = (row + dr, col + dc)
                    if cell in steps or not maze.is_corridor(cell):
                        continue
                    steps[cell] = steps[(row, col)] + 1
                    nxt.append(cell)
            frontier = nxt
        deepest = max(steps.values())
        return set(
            Position(row, col) for (row, col), n in steps.items() if n == deepest
        )


# --------------------------------------------------------------------------
# START-3 — a dot on every corridor square but the player's
# --------------------------------------------------------------------------


class DotTests(unittest.TestCase):
    """START-3, asserted by recount over every square of the board."""

    def test_a_square_holds_a_dot_exactly_when_it_is_corridor_and_not_the_player(self):
        for seed, state in _states():
            recount = _Recount(state)
            player = (state.player.row, state.player.col)
            for row in range(recount.height):
                for col in range(recount.width):
                    cell = (row, col)
                    should_hold = state.maze.is_corridor(cell) and cell != player
                    self.assertEqual(
                        Position(row, col) in state.dots,
                        should_hold,
                        "seed %d: (%d, %d) is %s, %s the player's square, and %s "
                        "a dot"
                        % (
                            seed,
                            row,
                            col,
                            "corridor" if state.maze.is_corridor(cell) else "wall",
                            "is" if cell == player else "is not",
                            "holds" if Position(row, col) in state.dots else "has no",
                        ),
                    )

    def test_dot_count_is_the_recounted_corridor_count_less_one(self):
        for seed, state in _states():
            recount = _Recount(state)
            self.assertEqual(
                len(state.dots),
                recount.corridor_count - 1,
                "seed %d: %d dots for %d corridor squares"
                % (seed, len(state.dots), recount.corridor_count),
            )

    def test_the_players_square_is_empty(self):
        for seed, state in _states():
            self.assertNotIn(
                state.player,
                state.dots,
                "seed %d: the player started on a dot" % seed,
            )

    def test_the_ghosts_square_does_hold_a_dot(self):
        """The ghost's square is not excused — only the player's is (START-3)."""
        for seed, state in _states():
            self.assertIn(
                state.ghost,
                state.dots,
                "seed %d: the ghost's square lost its dot" % seed,
            )

    def test_no_dot_sits_on_a_wall_or_off_the_board(self):
        for seed, state in _states():
            recount = _Recount(state)
            walls = set(recount.wall_cells)
            for dot in state.dots:
                self.assertNotIn(
                    (dot.row, dot.col),
                    walls,
                    "seed %d: a dot is inside a wall at %r" % (seed, dot),
                )
                self.assertTrue(
                    0 <= dot.row < MAZE_ROWS and 0 <= dot.col < MAZE_COLS,
                    "seed %d: a dot is off the board at %r" % (seed, dot),
                )


# --------------------------------------------------------------------------
# START-4 and START-5 — the score, the outcome, and being under way
# --------------------------------------------------------------------------


class ScoreAndOutcomeTests(unittest.TestCase):
    def test_the_score_starts_at_zero(self):
        for seed, state in _states():
            self.assertEqual(state.score, 0, "seed %d: score is not zero" % seed)

    def test_the_outcome_starts_as_playing(self):
        for seed, state in _states():
            self.assertIs(
                state.outcome,
                Outcome.PLAYING,
                "seed %d: a fresh game is already over" % seed,
            )

    def test_new_game_takes_a_random_source_and_nothing_else(self):
        """START-5, the state half: there is nothing to press.

        Not a shape assertion for its own sake. If a later item wants a title
        screen or a "press any key", the cheapest way in is a second parameter
        here — a screen, a key, a flag. This says there is no such parameter,
        so that route is closed.
        """
        parameters = list(inspect.signature(rules.new_game).parameters)
        self.assertEqual(
            parameters,
            ["rng"],
            "new_game should take a random source and nothing else, got %r"
            % (parameters,),
        )

    def test_a_fresh_state_carries_exactly_the_seven_fields_and_no_eighth(self):
        """GAME-3 still holds for a state built by this item."""
        state = rules.new_game(random.Random(0))
        self.assertEqual(
            GAME_STATE_FIELDS,
            ("maze", "player", "ghost", "ghost_dir", "dots", "score", "outcome"),
        )
        for banned in ("lives", "level", "timer", "power_up", "paused", "restart"):
            self.assertFalse(
                hasattr(state, banned),
                "a fresh game state has grown a %r field" % (banned,),
            )


# --------------------------------------------------------------------------
# The ghost's heading
# --------------------------------------------------------------------------


class GhostHeadingTests(unittest.TestCase):
    def test_the_heading_is_one_of_the_four_directions(self):
        for seed, state in _states():
            self.assertIn(
                state.ghost_dir,
                DIRECTIONS,
                "seed %d: %r is not a direction" % (seed, state.ghost_dir),
            )

    def test_the_heading_is_open_from_the_ghosts_own_square(self):
        """Recounted from the grid, not from ``maze.open_directions``.

        The square one step along the heading is asked about directly, so this
        does not lean on the same lookup the placement code used.
        """
        for seed, state in _states():
            ahead = (
                state.ghost.row + state.ghost_dir.dr,
                state.ghost.col + state.ghost_dir.dc,
            )
            self.assertTrue(
                state.maze.is_corridor(ahead),
                "seed %d: the ghost at %r faces %s, into the wall at %r"
                % (seed, state.ghost, state.ghost_dir.name, ahead),
            )

    def test_the_heading_is_actually_drawn_from_the_random_source(self):
        """More than one heading is seen across seeds.

        Always returning the first open direction would satisfy every other
        test in this file. It would not satisfy this one.
        """
        headings = set(state.ghost_dir for _seed, state in _states())
        self.assertGreater(
            len(headings),
            1,
            "every seed gave the ghost the same heading %r, so it is not being "
            "chosen from the random source" % (headings,),
        )


# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------


class ReproducibilityTests(unittest.TestCase):
    def test_the_same_seed_gives_the_identical_starting_state_twice(self):
        for seed in range(30):
            first = rules.new_game(random.Random(seed))
            second = rules.new_game(random.Random(seed))
            self.assertEqual(first.maze.rows(), second.maze.rows(), "seed %d" % seed)
            self.assertEqual(first.player, second.player, "seed %d" % seed)
            self.assertEqual(first.ghost, second.ghost, "seed %d" % seed)
            self.assertEqual(first.ghost_dir, second.ghost_dir, "seed %d" % seed)
            self.assertEqual(first.dots, second.dots, "seed %d" % seed)
            self.assertEqual(first.score, second.score, "seed %d" % seed)
            self.assertIs(first.outcome, second.outcome, "seed %d" % seed)

    def test_the_whole_state_compares_equal_for_the_same_seed(self):
        self.assertEqual(rules.new_game(random.Random(7)), rules.new_game(random.Random(7)))

    def test_two_different_seeds_give_two_different_starting_positions(self):
        """Not merely two different mazes — a different placement too."""
        placements = set()
        mazes = set()
        for _seed, state in _states(range(30)):
            placements.add((state.player, state.ghost))
            mazes.add(state.maze.rows())
        self.assertGreater(len(mazes), 1, "every seed produced the same maze")
        self.assertGreater(
            len(placements),
            1,
            "every seed put the player and the ghost on the same two squares",
        )


# --------------------------------------------------------------------------
# Hand-written boards, small enough to check by eye
# --------------------------------------------------------------------------

#: The middle square ``(3, 4)`` is a **wall**, so four corridor squares tie at
#: distance 1 for nearest the middle: ``(2, 4)``, ``(3, 3)``, ``(3, 5)`` and
#: ``(4, 4)``. Lowest ``(row, col)`` of those four is ``(2, 4)``.
#:
#: From ``(2, 4)`` the furthest corridor squares are ``(5, 1)`` and ``(5, 7)``,
#: both at ``3**2 + 3**2 = 18``. Lowest of those two is ``(5, 1)``, whose only
#: ways on are up to ``(4, 1)`` and right to ``(5, 2)``.
PLAYER_TIE_BOARD = """\
#########
#.......#
#.......#
#...#...#
#.......#
#.......#
#########"""

#: The middle square ``(3, 4)`` **is** corridor, so the player takes it
#: outright at distance 0 — no tie.
#:
#: From ``(3, 4)`` the four corners, ``(1, 1)``, ``(1, 7)``, ``(5, 1)`` and
#: ``(5, 7)``, all sit at ``2**2 + 3**2 = 13``, and nothing on the board is
#: further. Lowest ``(row, col)`` of the four is ``(1, 1)``, whose only ways
#: on are right to ``(1, 2)`` and down to ``(2, 1)``.
GHOST_TIE_BOARD = """\
#########
#.......#
#.#...#.#
#.......#
#.#...#.#
#.......#
#########"""


class HandWrittenBoardTests(unittest.TestCase):
    """Boards a reader can check by eye, forcing each tie-break in turn."""

    def test_hand_written_board_player_takes_the_lowest_of_four_tied_squares(self):
        maze = mazelib.from_text(PLAYER_TIE_BOARD)
        state = rules.starting_state(maze, random.Random(0))
        self.assertEqual(state.player, Position(2, 4))

    def test_hand_written_board_the_four_way_tie_for_the_player_is_real(self):
        """Recounted: those four squares really are all at distance 1."""
        maze = mazelib.from_text(PLAYER_TIE_BOARD)
        tied = [
            (row, col)
            for row in range(7)
            for col in range(9)
            if maze.is_corridor((row, col)) and (row - 3) ** 2 + (col - 4) ** 2 == 1
        ]
        self.assertEqual(tied, [(2, 4), (3, 3), (3, 5), (4, 4)])

    def test_hand_written_board_ghost_takes_the_lowest_of_two_tied_squares(self):
        maze = mazelib.from_text(PLAYER_TIE_BOARD)
        state = rules.starting_state(maze, random.Random(0))
        self.assertEqual(state.ghost, Position(5, 1))

    def test_hand_written_board_player_takes_the_exact_middle_when_it_is_open(self):
        maze = mazelib.from_text(GHOST_TIE_BOARD)
        state = rules.starting_state(maze, random.Random(0))
        self.assertEqual(state.player, Position(3, 4))

    def test_hand_written_board_ghost_takes_the_lowest_of_four_tied_corners(self):
        maze = mazelib.from_text(GHOST_TIE_BOARD)
        state = rules.starting_state(maze, random.Random(0))
        self.assertEqual(state.ghost, Position(1, 1))

    def test_hand_written_board_the_four_way_tie_for_the_ghost_is_real(self):
        """Recounted: nothing on that board is further from (3, 4) than 13."""
        maze = mazelib.from_text(GHOST_TIE_BOARD)
        distances = dict(
            ((row, col), (row - 3) ** 2 + (col - 4) ** 2)
            for row in range(7)
            for col in range(9)
            if maze.is_corridor((row, col))
        )
        furthest = max(distances.values())
        self.assertEqual(furthest, 13)
        self.assertEqual(
            sorted(cell for cell, d in distances.items() if d == furthest),
            [(1, 1), (1, 7), (5, 1), (5, 7)],
        )

    def test_hand_written_board_dots_are_every_corridor_but_the_players(self):
        maze = mazelib.from_text(GHOST_TIE_BOARD)
        state = rules.starting_state(maze, random.Random(0))
        expected = set(
            Position(row, col)
            for row in range(7)
            for col in range(9)
            if maze.is_corridor((row, col)) and (row, col) != (3, 4)
        )
        self.assertEqual(set(state.dots), expected)
        self.assertEqual(len(state.dots), len(expected))

    def test_hand_written_board_heading_is_one_of_the_two_open_ways_on(self):
        """From ``(1, 1)`` the only ways on are RIGHT and DOWN."""
        maze = mazelib.from_text(GHOST_TIE_BOARD)
        seen = set()
        for seed in range(40):
            state = rules.starting_state(maze, random.Random(seed))
            self.assertEqual(state.ghost, Position(1, 1))
            seen.add(state.ghost_dir.name)
        self.assertEqual(seen, set(["RIGHT", "DOWN"]))


# --------------------------------------------------------------------------
# Degenerate boards fail loudly
# --------------------------------------------------------------------------


class DegenerateBoardTests(unittest.TestCase):
    def test_a_maze_with_no_corridor_at_all_raises(self):
        maze = mazelib.from_text("###\n###\n###")
        with self.assertRaises(ValueError):
            rules.starting_state(maze, random.Random(0))

    def test_a_ghost_square_with_no_way_on_raises(self):
        """A lone walled-in square cannot be faced away from.

        Not reachable on a generated maze — MAZE-5 forbids it — but a
        hand-written board can produce it, and an explicit failure beats an
        ``IndexError`` from inside a random choice.
        """
        maze = mazelib.from_text("###\n#.#\n###")
        with self.assertRaises(ValueError):
            rules.starting_heading(maze, (1, 1), random.Random(0))


# --------------------------------------------------------------------------
# The purity contract, restated where a reader of this module will see it
# --------------------------------------------------------------------------


class PurityTests(unittest.TestCase):
    """WI-1's guard covers ``rules.py`` automatically; this pins the one rule
    it cannot see — that randomness arrives as a parameter and never from a
    module-level draw."""

    def test_every_public_function_that_needs_randomness_takes_it_as_a_parameter(self):
        for name in ("new_game", "starting_state", "starting_heading"):
            parameters = list(inspect.signature(getattr(rules, name)).parameters)
            self.assertIn(
                "rng",
                parameters,
                "%s must take its random source as a parameter, got %r"
                % (name, parameters),
            )

    def test_the_module_makes_no_module_level_random_draw(self):
        """Two different ``Random`` instances at the same seed agree, and the
        process-wide ``random`` module is untouched by a call."""
        random.seed(12345)
        before = random.random()
        random.seed(12345)
        rules.new_game(random.Random(99))
        after = random.random()
        self.assertEqual(
            before,
            after,
            "new_game consumed the process-wide random source",
        )


if __name__ == "__main__":
    unittest.main()
