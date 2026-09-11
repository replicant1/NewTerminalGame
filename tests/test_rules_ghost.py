"""The ghost's movement policy — GHOST-2, GHOST-3, GHOST-4, SCORE-4,
END-1 (the ghost walks into the player) and END-5 (the ghost half).

**Every board here is hand-written and small enough to check by eye**, and
each one is drawn again in the docstring of the test that uses it with the
squares of interest named. Nothing below recomputes an expected answer with
the expression the module uses: the expected squares are written out as
literal ``(row, col)`` pairs, counted off the picture.

Four boards do all the work:

``STRAIGHT``    a single corridor with a blind end at each end — GHOST-2, and
                the reversal at the end of it.
``CROSS``       a lattice of junctions of degree 2, 3 and 4, **plus a second
                corridor that is walled off from the first**. The ghost can
                never reach the walled-off strip, which is what lets GHOST-4
                park the player on it and run the ghost for as long as it
                likes without an END-1 collision confounding the comparison.
``TEE``         one T-junction, entered along the stem — GHOST-3.
``CIRCUIT``     the board GHOST-4 is actually run on, and the reason it is
                not ``CROSS``. See the note below. It too carries a
                walled-off strip for the player.
``CULDESAC``    a stub with a degree-one square at the bottom. **A generated
                maze never contains one** (MAZE-5 keeps every corridor square
                at degree two or more), which is exactly why this board has
                to be hand-built: GHOST-3's last clause is unreachable
                without it.

**Why GHOST-4 is not run on the obvious lattice.** A ghost only makes a
*genuine* random choice where the square straight ahead is a wall **and** at
least two other ways on remain — which, working it through, means a square
of degree three or more entered along its one blocked direction. On a
regular lattice like ``CROSS`` that almost never recurs: measured over every
starting square and heading on ``CROSS``, a 200-tick run makes **at most one
genuine choice** and then settles into a cycle that makes none. A GHOST-4
comparison on such a run is close to vacuous — a ghost that hunted would
have no junction at which to do it, and the three paths would match anyway.
``CIRCUIT`` is shaped so that every circuit passes through a decision (20 in
200 ticks, measured), and the generated-maze run makes 13 to 15 in 300. The
"not vacuous" guard in :class:`TestGhost4TheGhostDoesNotHunt` pins that
without re-implementing the policy: the same run under **two different
seeds** must differ. A path that moves when the seed moves and stands still
when the player moves is reading the seed and not the player.

A note on what "the ghost does not hunt" can and cannot be tested. There is
no assertion that proves a function ignores an argument; what there *is* is
the observation that moving the player around changes nothing. That is
:class:`TestGhost4TheGhostDoesNotHunt`, and it is the test this work item is
for.
"""

import copy
import random
import unittest

from termgame import maze as mazelib
from termgame import rules
from termgame.model import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    GameState,
    Outcome,
    Position,
)


# --------------------------------------------------------------------------
# The boards
# --------------------------------------------------------------------------

#: A blind corridor, 3 x 9. The corridor squares are (1, 1) to (1, 7), and
#: both ends are walled: (1, 0) and (1, 8) are wall.
#:
#:      col 012345678
#:      row 0 #########
#:      row 1 #.......#
#:      row 2 #########
STRAIGHT = """\
#########
#.......#
#########"""

#: 9 x 9. Rows 1 to 5 are one connected lattice; **row 7 is a separate
#: corridor strip walled off from it** by the solid rows 6 and 8.
#:
#:      col 012345678
#:      row 0 #########
#:      row 1 #...#...#
#:      row 2 #.#.#.#.#
#:      row 3 #.......#
#:      row 4 #.#.#.#.#
#:      row 5 #...#...#
#:      row 6 #########
#:      row 7 #.......#     <- unreachable from the lattice above
#:      row 8 #########
#:
#: Degrees worth knowing, counted off the picture: (3, 3) and (3, 5) are
#: four-way; (3, 1) and (3, 7) are three-way; (3, 2), (3, 4) and (3, 6) are
#: straight-through; (1, 1) is a corner.
CROSS = """\
#########
#...#...#
#.#.#.#.#
#.......#
#.#.#.#.#
#...#...#
#########
#.......#
#########"""

#: 9 x 9, and the board GHOST-4 is run on. Like CROSS it keeps a walled-off
#: strip at row 7 for the player, and like CROSS every square of it can be
#: read off the picture — but unlike CROSS it keeps handing the ghost real
#: decisions instead of settling into a decision-free loop.
#:
#:      col 012345678
#:      row 0 #########
#:      row 1 #.......#
#:      row 2 #.##.##.#
#:      row 3 #.##.##.#
#:      row 4 #....##.#
#:      row 5 ####....#
#:      row 6 #########
#:      row 7 #.......#     <- unreachable from the circuit above
#:      row 8 #########
#:
#: Two squares do the work, and both are three-way with exactly one wall:
#:
#: * **(1, 4)** — wall above, arms left and right, stem below. A ghost
#:   arriving *up* the stem finds the wall ahead and must choose between the
#:   two arms.
#: * **(4, 4)** — wall to the right, ways up, left and down. A ghost
#:   arriving *rightwards* along row 4 finds the wall ahead and must choose
#:   between up and down.
#:
#: and the rest of the board is corners and straights that feed the ghost
#: back into one or the other. Going up from (4, 4) leads up the stem to
#: (1, 4); going down leads round by row 5, column 7 and row 1 and back to
#: (4, 4) along row 4. Either way the next decision is a few squares off.
CIRCUIT = """\
#########
#.......#
#.##.##.#
#.##.##.#
#....##.#
####....#
#########
#.......#
#########"""

#: A T, 4 x 5. The cross-bar is (1, 1), (1, 2), (1, 3); the stem is (2, 2).
#: Standing on (1, 2) facing UP, the wall is ahead, the stem is behind, and
#: the two arms are (1, 1) to the left and (1, 3) to the right.
#:
#:      col 01234
#:      row 0 #####
#:      row 1 #...#
#:      row 2 ##.##
#:      row 3 #####
TEE = """\
#####
#...#
##.##
#####"""

#: A stub, 5 x 5. (1, 1), (1, 2), (1, 3), (2, 3), (3, 3) are corridor.
#: (3, 3) has exactly one way on — UP — so a ghost that arrives there facing
#: DOWN has no choice but to turn round. **MAZE-5 forbids this shape in a
#: generated maze**, so it only exists here.
#:
#:      col 01234
#:      row 0 #####
#:      row 1 #...#
#:      row 2 ###.#
#:      row 3 ###.#
#:      row 4 #####
CULDESAC = """\
#####
#...#
###.#
###.#
#####"""


def board(text):
    """The hand-written board as a maze value."""
    return mazelib.from_text(text)


def state_on(
    text,
    ghost,
    ghost_dir,
    player=(0, 0),
    dots=(),
    score=0,
    outcome=Outcome.PLAYING,
):
    """A game state on a hand-written board.

    The player defaults to ``(0, 0)`` — the top-left **corner, which is wall
    on every board here**, so the ghost can never land on it and no test
    trips over an END-1 collision it did not ask for.
    """
    return GameState(
        maze=board(text),
        player=Position(*player),
        ghost=Position(*ghost),
        ghost_dir=ghost_dir,
        dots=frozenset(Position(*d) for d in dots),
        score=score,
        outcome=outcome,
    )


def walk(state, rng, ticks):
    """Run the ghost for ``ticks`` ticks; return the squares it stood on.

    The starting square is **not** included: the list is where the ghost went,
    one entry per tick.
    """
    path = []
    for _ in range(ticks):
        state = rules.move_ghost(state, rng)
        path.append(state.ghost)
    return path


class Forbidden(object):
    """A random source that fails the test if it is drawn from at all.

    Handed to a ghost that ought to be carrying straight on, it turns "the
    ghost happened to pick the same direction" into a hard failure.
    """

    def __init__(self, case):
        self.case = case

    def choice(self, options):
        self.case.fail(
            "the ghost drew from the random source when the way straight "
            "ahead was open; it should have carried on without choosing "
            "(GHOST-2). It was offered %r"
            % (tuple(d.name for d in options),)
        )


# --------------------------------------------------------------------------
# GHOST-2 — straight on for as long as the corridor lets it
# --------------------------------------------------------------------------


class TestGhost2StraightOn(unittest.TestCase):
    """``#.......#`` — from (1, 1) facing RIGHT, six ticks reach (1, 7)."""

    def test_a_straight_corridor_keeps_the_heading_for_the_whole_run(self):
        state = state_on(STRAIGHT, ghost=(1, 1), ghost_dir=RIGHT)
        # Counted off the picture: (1, 1) -> (1, 2) -> ... -> (1, 7).
        expected = [
            Position(1, 2),
            Position(1, 3),
            Position(1, 4),
            Position(1, 5),
            Position(1, 6),
            Position(1, 7),
        ]
        seen = []
        headings = []
        for _ in range(6):
            state = rules.move_ghost(state, Forbidden(self))
            seen.append(state.ghost)
            headings.append(state.ghost_dir)
        self.assertEqual(seen, expected)
        self.assertEqual(headings, [RIGHT] * 6)

    def test_the_same_run_backwards(self):
        state = state_on(STRAIGHT, ghost=(1, 7), ghost_dir=LEFT)
        seen = walk(state, Forbidden(self), 6)
        self.assertEqual(
            seen,
            [
                Position(1, 6),
                Position(1, 5),
                Position(1, 4),
                Position(1, 3),
                Position(1, 2),
                Position(1, 1),
            ],
        )

    def test_a_straight_run_draws_no_randomness_at_all(self):
        # Forbidden.choice failing is one half of this; the other half is
        # that a real random source comes out of the run untouched, which is
        # what makes a seeded ghost's arithmetic predictable.
        rng = random.Random(4)
        before = rng.getstate()
        walk(state_on(STRAIGHT, ghost=(1, 1), ghost_dir=RIGHT), rng, 6)
        self.assertEqual(rng.getstate(), before)

    def test_straight_on_wins_over_a_junction_with_arms(self):
        """(3, 3) on CROSS is four-way, but facing RIGHT the ghost carries on.

        This is the clause-ordering test: GHOST-2 is tried before GHOST-3, so
        a junction whose forward square is open is not a decision at all.
        """
        state = state_on(CROSS, ghost=(3, 3), ghost_dir=RIGHT)
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.ghost, Position(3, 4))
        self.assertEqual(moved.ghost_dir, RIGHT)

    def test_straight_on_through_a_three_way_junction(self):
        """(3, 1) on CROSS is three-way; facing DOWN the ghost keeps going."""
        state = state_on(CROSS, ghost=(3, 1), ghost_dir=DOWN)
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.ghost, Position(4, 1))
        self.assertEqual(moved.ghost_dir, DOWN)


# --------------------------------------------------------------------------
# GHOST-3 — a random turn, and the reverse only as a last resort
# --------------------------------------------------------------------------

#: How many seeds the T-junction sweep uses. Two arms, uniform, so the
#: chance of one arm never coming up in 200 draws is 2 ** -199.
SEEDS = range(200)


class TestGhost3TheTurnAtAJunction(unittest.TestCase):
    """The T: standing on (1, 2) facing UP, into the wall at (0, 2)."""

    def _turn(self, seed):
        state = state_on(TEE, ghost=(1, 2), ghost_dir=UP)
        return rules.move_ghost(state, random.Random(seed))

    def test_the_reverse_is_never_chosen_over_many_seeds(self):
        # The ghost came up the stem, so DOWN, back to (2, 2), is the one
        # direction GHOST-3 forbids while anything else is available.
        for seed in SEEDS:
            moved = self._turn(seed)
            self.assertNotEqual(
                moved.ghost_dir,
                DOWN,
                "seed %d turned the ghost back down the stem it came up"
                % seed,
            )
            self.assertNotEqual(moved.ghost, Position(2, 2))

    def test_both_arms_are_chosen_at_least_once_over_many_seeds(self):
        # A policy that always took the first open direction would pass the
        # test above and fail this one: open_directions returns in the fixed
        # DIRECTIONS order, so "always the first" is always LEFT here.
        landed = set(self._turn(seed).ghost for seed in SEEDS)
        self.assertEqual(landed, {Position(1, 1), Position(1, 3)})

    def test_every_turn_is_onto_a_corridor_square_it_could_reach(self):
        maze = board(TEE)
        for seed in SEEDS:
            moved = self._turn(seed)
            self.assertTrue(maze.is_corridor(moved.ghost))
            self.assertIn(moved.ghost, maze.open_neighbours((1, 2)))

    def test_the_heading_and_the_square_always_agree(self):
        for seed in SEEDS:
            moved = self._turn(seed)
            self.assertEqual(
                moved.ghost, Position(1, 2).shifted(moved.ghost_dir)
            )

    def test_the_turn_is_reproducible_from_the_same_seed(self):
        for seed in (0, 1, 2, 17):
            first = self._turn(seed).ghost
            second = self._turn(seed).ghost
            self.assertEqual(first, second)


class TestGhost3ReversesOnlyWhenThereIsNoChoice(unittest.TestCase):
    """The cul-de-sac, which MAZE-5 keeps out of every generated maze."""

    def test_the_bottom_of_a_cul_de_sac_turns_the_ghost_round(self):
        # (3, 3) has exactly one way on, UP, and the ghost is facing DOWN
        # into the wall at (4, 3). There is nothing to choose, so it goes
        # back to (2, 3).
        state = state_on(CULDESAC, ghost=(3, 3), ghost_dir=DOWN)
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.ghost, Position(2, 3))
        self.assertEqual(moved.ghost_dir, UP)

    def test_the_blind_end_of_the_straight_corridor_turns_it_round(self):
        # (1, 7) on STRAIGHT: LEFT is the only way on and the ghost arrived
        # facing RIGHT, so LEFT is also the reverse. It takes it.
        state = state_on(STRAIGHT, ghost=(1, 7), ghost_dir=RIGHT)
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.ghost, Position(1, 6))
        self.assertEqual(moved.ghost_dir, LEFT)

    def test_a_forced_reversal_draws_no_randomness(self):
        rng = random.Random(11)
        before = rng.getstate()
        rules.move_ghost(
            state_on(CULDESAC, ghost=(3, 3), ghost_dir=DOWN), rng
        )
        self.assertEqual(rng.getstate(), before)

    def test_the_ghost_bounces_forever_in_a_blind_corridor(self):
        # Eight ticks from (1, 6) facing RIGHT: up to the blind end, back
        # down to the other one, counted off the picture.
        state = state_on(STRAIGHT, ghost=(1, 6), ghost_dir=RIGHT)
        self.assertEqual(
            walk(state, Forbidden(self), 8),
            [
                Position(1, 7),
                Position(1, 6),
                Position(1, 5),
                Position(1, 4),
                Position(1, 3),
                Position(1, 2),
                Position(1, 1),
                Position(1, 2),
            ],
        )

    def test_a_walled_in_ghost_is_refused_rather_than_walked_into_a_wall(self):
        # Not reachable from a generated maze; the guard exists so that a
        # bad hand-written board fails loudly instead of putting the ghost
        # inside a wall.
        state = state_on("###\n#.#\n###", ghost=(1, 1), ghost_dir=UP)
        with self.assertRaises(ValueError) as caught:
            rules.move_ghost(state, random.Random(0))
        self.assertIn("no way on", str(caught.exception))


class TestGhost3OnRealGeneratedMazes(unittest.TestCase):
    """The policy against the boards the game actually plays on.

    MAZE-5 puts every corridor square at degree two or more. A ghost that
    arrives somewhere always has the way it came open, so "degree two or
    more" means there is always at least one direction that is not the
    reverse — which makes a striking prediction: **on a generated maze the
    ghost never turns back the way it came.** These tests assert that, and
    that every step lands on a corridor square one square away.
    """

    @staticmethod
    def _running_game(seed):
        """A real game on seed ``seed``, with the player parked out of reach.

        The player goes to ``(0, 0)``, which MAZE-3 guarantees is wall, so
        these sweeps cannot be cut short by an END-1 catch. Leaving the real
        player where it starts is what makes the difference: the ghost
        catches it partway through and END-5 then freezes the state, and a
        sweep that did not notice would be asserting about a ghost that had
        stopped moving.
        """
        rng = random.Random(seed)
        state = rules.starting_state(mazelib.generate(rng), rng)
        return (
            GameState(
                maze=state.maze,
                player=Position(0, 0),
                ghost=state.ghost,
                ghost_dir=state.ghost_dir,
                dots=state.dots,
                score=state.score,
                outcome=state.outcome,
            ),
            rng,
        )

    def test_the_ghost_never_reverses_on_a_generated_maze(self):
        for seed in range(30):
            state, rng = self._running_game(seed)
            for tick in range(120):
                was = state.ghost_dir
                state = rules.move_ghost(state, rng)
                self.assertNotEqual(
                    state.ghost_dir,
                    was.opposite(),
                    "seed %d tick %d: the ghost reversed at %r, but MAZE-5 "
                    "means it always had somewhere else to go"
                    % (seed, tick, state.ghost),
                )

    def test_every_step_is_one_square_onto_corridor(self):
        for seed in range(30):
            state, rng = self._running_game(seed)
            maze = state.maze
            for tick in range(120):
                before = state.ghost
                state = rules.move_ghost(state, rng)
                self.assertIn(
                    state.ghost,
                    maze.open_neighbours(before),
                    "seed %d tick %d: %r -> %r is not a step along a corridor"
                    % (seed, tick, before, state.ghost),
                )
                self.assertEqual(
                    state.ghost, before.shifted(state.ghost_dir)
                )

    def test_it_keeps_the_heading_whenever_the_way_ahead_was_open(self):
        for seed in range(30):
            state, rng = self._running_game(seed)
            maze = state.maze
            for tick in range(120):
                here, was = state.ghost, state.ghost_dir
                state = rules.move_ghost(state, rng)
                if maze.is_open(here, was):
                    self.assertEqual(
                        state.ghost_dir,
                        was,
                        "seed %d tick %d: turned at %r although %s was open"
                        % (seed, tick, here, was.name),
                    )


# --------------------------------------------------------------------------
# GHOST-4 — the ghost does not hunt
# --------------------------------------------------------------------------


class TestGhost4TheGhostDoesNotHunt(unittest.TestCase):
    """The test this work item exists for.

    The same seed, the same maze, the same starting square and heading — and
    the player somewhere different each time. If the three runs come out
    identical square for square and heading for heading over a long run
    through many junctions, the ghost is not reading the player. If any one
    of them diverges, it is.

    Both boards put the player where the ghost can never reach it, so that a
    collision cannot end a run early and make two short paths agree for the
    wrong reason: on CIRCUIT the player sits on the walled-off strip at row
    7, and on a generated maze it sits on the wall corner (0, 0), which
    MAZE-3 guarantees is never corridor.

    It is run on CIRCUIT rather than CROSS for the reason set out at the top
    of this file: a run that never reaches a real fork proves nothing about
    hunting, because a hunting ghost would have had no fork to hunt at.
    ``test_that_comparison_is_not_vacuous`` is what stands behind that, and
    it does not re-implement the policy to do it — it simply changes the
    seed and requires the path to change.
    """

    TICKS = 200

    def _run_with_player_at(self, player, seed=5):
        state = state_on(CIRCUIT, ghost=(1, 4), ghost_dir=UP, player=player)
        rng = random.Random(seed)
        trail = []
        for _ in range(self.TICKS):
            state = rules.move_ghost(state, rng)
            trail.append((state.ghost, state.ghost_dir.name, state.outcome))
        return trail

    def test_three_player_positions_give_three_identical_ghost_paths(self):
        # (7, 1), (7, 4) and (7, 7) are all on the walled-off strip, so the
        # ghost never meets any of them.
        first = self._run_with_player_at((7, 1))
        second = self._run_with_player_at((7, 4))
        third = self._run_with_player_at((7, 7))
        self.assertEqual(first, second)
        self.assertEqual(second, third)

    def test_that_comparison_is_not_vacuous(self):
        # Two claims, and the pair of them is the whole argument.
        #
        # First, the run is long, wanders, and never ends: it is not one
        # square repeated 200 times, nor a path frozen by an early catch.
        trail = self._run_with_player_at((7, 1))
        self.assertEqual(len(trail), self.TICKS)
        self.assertGreater(len(set(square for square, _, _ in trail)), 8)
        self.assertGreater(len(set(name for _, name, _ in trail)), 2)
        self.assertEqual(
            set(outcome for _, _, outcome in trail), {Outcome.PLAYING}
        )
        # Second, and this is the part that matters: the path **does** move
        # when something it is entitled to read moves. Change the seed and
        # it comes out different. So the run is full of real forks, and a
        # ghost that took the player into account at those forks would have
        # shown it in the test above.
        for other in (6, 7, 8):
            self.assertNotEqual(
                self._run_with_player_at((7, 1), seed=other),
                trail,
                "seed %d gave the same path as seed 5, so this run reaches "
                "no fork and proves nothing about hunting" % other,
            )

    def test_the_player_may_even_be_moved_between_ticks(self):
        """A player that teleports every tick still changes nothing.

        Stronger than the three fixed positions: this walks the player over
        every square of the walled-off strip while the ghost runs, and the
        ghost's path is still the one it takes when the player never moves.
        """
        strip = [Position(7, c) for c in range(1, 8)]
        state = state_on(
            CIRCUIT, ghost=(1, 4), ghost_dir=UP, player=strip[0]
        )
        rng = random.Random(5)
        trail = []
        for tick in range(self.TICKS):
            state = rules.move_ghost(state, rng)
            trail.append((state.ghost, state.ghost_dir.name, state.outcome))
            state = GameState(
                maze=state.maze,
                player=strip[tick % len(strip)],
                ghost=state.ghost,
                ghost_dir=state.ghost_dir,
                dots=state.dots,
                score=state.score,
                outcome=state.outcome,
            )
        self.assertEqual(trail, self._run_with_player_at((7, 1)))

    def test_three_player_positions_on_a_real_generated_maze(self):
        # The same again on a board the game would actually deal, so that
        # nothing here depends on the hand-written lattice.
        maze = mazelib.generate(random.Random(23))
        start = rules.starting_ghost(maze, rules.starting_player(maze))
        heading = maze.open_directions(start)[0]

        def run(player, seed=99):
            state = GameState(
                maze=maze,
                player=Position(*player),
                ghost=start,
                ghost_dir=heading,
                dots=frozenset(),
                score=0,
                outcome=Outcome.PLAYING,
            )
            rng = random.Random(seed)
            out = []
            for _ in range(300):
                state = rules.move_ghost(state, rng)
                out.append((state.ghost, state.ghost_dir.name))
            return out

        # (0, 0) is wall by MAZE-3, so this run can never be interrupted.
        reference = run((0, 0))
        # As above: a run that reaches no fork proves nothing, so require
        # this one to answer to the seed before asking it to ignore the
        # player. (Measured on this maze: 15 genuine forks in 300 ticks.)
        self.assertNotEqual(run((0, 0), seed=100), reference)
        visited = set(square for square, _ in reference)
        elsewhere = sorted(p for p in maze.corridors() if p not in visited)
        self.assertGreaterEqual(
            len(elsewhere),
            3,
            "the ghost covered so much of the maze that there is nowhere "
            "left to stand the player; pick a different seed",
        )
        for player in (elsewhere[0], elsewhere[len(elsewhere) // 2],
                       elsewhere[-1]):
            self.assertEqual(
                run(player),
                reference,
                "moving the player to %r changed the ghost's path" % (player,),
            )


# --------------------------------------------------------------------------
# SCORE-4 — the ghost neither eats dots nor scores
# --------------------------------------------------------------------------


class TestScore4TheGhostLeavesTheDotsAlone(unittest.TestCase):
    """Dots on every corridor square of ``STRAIGHT``; the ghost walks over
    them and takes none."""

    ALL_DOTS = tuple(Position(1, c) for c in range(1, 8))

    def test_a_move_onto_a_dotted_square_leaves_the_dot_there(self):
        state = state_on(
            STRAIGHT, ghost=(1, 1), ghost_dir=RIGHT, dots=self.ALL_DOTS,
            score=3,
        )
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.ghost, Position(1, 2))
        self.assertIn(
            Position(1, 2),
            moved.dots,
            "the ghost stood on (1, 2) and its dot vanished",
        )
        self.assertEqual(moved.dots, state.dots)
        self.assertEqual(moved.score, 3)

    def test_leaving_a_dotted_square_leaves_the_dot_there_too(self):
        state = state_on(
            STRAIGHT, ghost=(1, 2), ghost_dir=RIGHT, dots=self.ALL_DOTS,
        )
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertIn(Position(1, 2), moved.dots)
        self.assertIn(Position(1, 3), moved.dots)

    def test_the_whole_set_survives_a_long_run_square_for_square(self):
        state = state_on(
            STRAIGHT, ghost=(1, 1), ghost_dir=RIGHT, dots=self.ALL_DOTS,
        )
        expected = frozenset(self.ALL_DOTS)
        for _ in range(20):
            state = rules.move_ghost(state, random.Random(0))
            self.assertEqual(state.dots, expected)
            self.assertEqual(state.dots - expected, frozenset())
            self.assertEqual(expected - state.dots, frozenset())
            self.assertEqual(state.score, 0)

    def test_the_score_is_carried_across_untouched_whatever_it_was(self):
        for score in (0, 1, 7, 250):
            state = state_on(
                STRAIGHT, ghost=(1, 1), ghost_dir=RIGHT,
                dots=self.ALL_DOTS, score=score,
            )
            self.assertEqual(rules.move_ghost(state, Forbidden(self)).score,
                             score)

    def test_a_move_that_loses_the_game_still_takes_no_dot(self):
        # END-1 and SCORE-4 at once: catching the player is not a scoring
        # event and does not clear the dot underneath.
        state = state_on(
            STRAIGHT, ghost=(1, 2), ghost_dir=RIGHT, player=(1, 3),
            dots=self.ALL_DOTS, score=9,
        )
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.outcome, Outcome.CAUGHT)
        self.assertEqual(moved.score, 9)
        self.assertIn(Position(1, 3), moved.dots)

    def test_dots_survive_a_long_run_on_a_generated_maze(self):
        rng = random.Random(3)
        state = rules.starting_state(mazelib.generate(rng), rng)
        state = GameState(
            maze=state.maze, player=Position(0, 0), ghost=state.ghost,
            ghost_dir=state.ghost_dir, dots=state.dots, score=state.score,
            outcome=state.outcome,
        )
        expected = state.dots
        self.assertGreater(len(expected), 100)   # there really are dots
        for _ in range(200):
            state = rules.move_ghost(state, rng)
        self.assertEqual(state.dots, expected)
        self.assertEqual(state.score, 0)


# --------------------------------------------------------------------------
# END-1 — the ghost walks into the player
# --------------------------------------------------------------------------


class TestEnd1TheGhostWalksIntoThePlayer(unittest.TestCase):
    def test_landing_on_the_player_loses_the_game(self):
        state = state_on(STRAIGHT, ghost=(1, 2), ghost_dir=RIGHT,
                         player=(1, 3))
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.outcome, Outcome.CAUGHT)
        self.assertEqual(moved.ghost, Position(1, 3))
        self.assertEqual(moved.player, Position(1, 3))

    def test_passing_next_to_the_player_does_not(self):
        # The player one square off the ghost's line: the ghost goes by and
        # the game is still on. This is the half that a collision test which
        # compared rows only, or columns only, would get wrong.
        state = state_on(CROSS, ghost=(3, 2), ghost_dir=RIGHT, player=(2, 3))
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.ghost, Position(3, 3))
        self.assertEqual(moved.outcome, Outcome.PLAYING)

    def test_standing_beside_the_player_and_turning_away_does_not(self):
        state = state_on(CULDESAC, ghost=(3, 3), ghost_dir=DOWN,
                         player=(1, 3))
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.ghost, Position(2, 3))
        self.assertEqual(moved.outcome, Outcome.PLAYING)

    def test_the_loss_is_decided_on_the_square_the_ghost_arrives_at(self):
        # The player standing where the ghost *started* is not a catch: the
        # ghost has left. (It cannot happen in a real game — that would
        # already have been a loss — but it pins which square is tested.)
        state = state_on(STRAIGHT, ghost=(1, 2), ghost_dir=RIGHT,
                         player=(1, 2))
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.ghost, Position(1, 3))
        self.assertEqual(moved.outcome, Outcome.PLAYING)

    def test_a_ghost_reversing_onto_the_player_loses_too(self):
        state = state_on(CULDESAC, ghost=(3, 3), ghost_dir=DOWN,
                         player=(2, 3))
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertEqual(moved.outcome, Outcome.CAUGHT)

    def test_a_ghost_turning_at_a_junction_onto_the_player_loses_too(self):
        # Both arms of the T occupied, so whichever way the draw falls the
        # answer is the same.
        for seed in range(20):
            state = state_on(TEE, ghost=(1, 2), ghost_dir=UP, player=(1, 1))
            moved = rules.move_ghost(state, random.Random(seed))
            if moved.ghost == Position(1, 1):
                self.assertEqual(moved.outcome, Outcome.CAUGHT)
            else:
                self.assertEqual(moved.outcome, Outcome.PLAYING)


# --------------------------------------------------------------------------
# END-5 — once it is over, the ghost stands still
# --------------------------------------------------------------------------


class TestEnd5AFinishedGameDoesNotMove(unittest.TestCase):
    def _finished(self, outcome):
        return state_on(
            STRAIGHT, ghost=(1, 1), ghost_dir=RIGHT,
            dots=(Position(1, 4),), score=6, outcome=outcome,
        )

    def test_a_caught_game_comes_back_the_very_same_object(self):
        state = self._finished(Outcome.CAUGHT)
        self.assertIs(rules.move_ghost(state, random.Random(0)), state)

    def test_a_cleared_game_comes_back_the_very_same_object(self):
        state = self._finished(Outcome.CLEARED)
        self.assertIs(rules.move_ghost(state, random.Random(0)), state)

    def test_a_hundred_ticks_change_nothing(self):
        for outcome in (Outcome.CAUGHT, Outcome.CLEARED):
            state = self._finished(outcome)
            after = state
            for _ in range(100):
                after = rules.move_ghost(after, random.Random(0))
            self.assertIs(after, state)
            self.assertEqual(after.ghost, Position(1, 1))
            self.assertEqual(after.ghost_dir, RIGHT)
            self.assertEqual(after.score, 6)
            self.assertEqual(after.outcome, outcome)

    def test_a_finished_game_draws_no_randomness(self):
        # The END-5 guard comes before the draw, so a finished game leaves
        # the random source exactly where it found it. If the guard moved
        # below the draw this would fail even though the state still looked
        # right.
        rng = random.Random(1)
        before = rng.getstate()
        for _ in range(50):
            rules.move_ghost(self._finished(Outcome.CAUGHT), rng)
        self.assertEqual(rng.getstate(), before)

    def test_the_guard_is_the_outcome_and_not_an_empty_dot_set(self):
        # A PLAYING game with no dots left is not finished as far as the
        # ghost is concerned; it is END-2's business, and the ghost moves.
        state = state_on(STRAIGHT, ghost=(1, 1), ghost_dir=RIGHT)
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertIsNot(moved, state)
        self.assertEqual(moved.ghost, Position(1, 2))


# --------------------------------------------------------------------------
# The transition is a transition: nothing is mutated
# --------------------------------------------------------------------------


class TestTheMoveIsPure(unittest.TestCase):
    def test_the_state_handed_in_is_not_touched(self):
        state = state_on(
            CROSS, ghost=(1, 1), ghost_dir=RIGHT, player=(7, 3),
            dots=(Position(3, 3), Position(3, 5)), score=4,
        )
        snapshot = copy.deepcopy(state)
        for _ in range(50):
            rules.move_ghost(state, random.Random(2))
        self.assertEqual(state.ghost, snapshot.ghost)
        self.assertEqual(state.ghost_dir, snapshot.ghost_dir)
        self.assertEqual(state.player, snapshot.player)
        self.assertEqual(state.dots, snapshot.dots)
        self.assertEqual(state.score, snapshot.score)
        self.assertEqual(state.outcome, snapshot.outcome)
        self.assertEqual(state.maze.rows(), snapshot.maze.rows())

    def test_the_maze_comes_across_unchanged(self):
        state = state_on(CROSS, ghost=(1, 1), ghost_dir=RIGHT)
        moved = rules.move_ghost(state, Forbidden(self))
        self.assertIs(moved.maze, state.maze)

    @staticmethod
    def _circuit_run(seed):
        return walk(
            state_on(CIRCUIT, ghost=(1, 4), ghost_dir=UP),
            random.Random(seed),
            150,
        )

    def test_the_same_seed_gives_the_same_run_twice(self):
        self.assertEqual(self._circuit_run(8), self._circuit_run(8))

    def test_different_seeds_give_different_runs(self):
        # If they did not, "the same seed gives the same run" would be true
        # of a ghost that ignored the random source entirely.
        self.assertNotEqual(self._circuit_run(8), self._circuit_run(9))


# --------------------------------------------------------------------------
# The boards themselves, checked against their own docstrings
# --------------------------------------------------------------------------


class TestTheHandWrittenBoardsAreWhatTheySay(unittest.TestCase):
    """If a board is not the shape the tests above assume, those tests are
    asserting something other than what they claim. So the shapes are pinned
    here, counted off the pictures."""

    def test_straight_is_one_corridor_walled_at_both_ends(self):
        maze = board(STRAIGHT)
        self.assertEqual((maze.height, maze.width), (3, 9))
        self.assertEqual(
            sorted(maze.corridors()),
            [Position(1, c) for c in range(1, 8)],
        )
        self.assertTrue(maze.is_wall((1, 0)))
        self.assertTrue(maze.is_wall((1, 8)))

    def test_the_tee_is_a_tee(self):
        maze = board(TEE)
        self.assertEqual(
            sorted(maze.corridors()),
            [Position(1, 1), Position(1, 2), Position(1, 3), Position(2, 2)],
        )
        self.assertEqual(maze.corridor_degree((1, 2)), 3)
        self.assertTrue(maze.is_wall((0, 2)))

    def test_the_cul_de_sac_really_has_a_degree_one_square(self):
        maze = board(CULDESAC)
        self.assertEqual(maze.corridor_degree((3, 3)), 1)
        self.assertEqual(maze.open_directions((3, 3)), (UP,))

    def test_a_generated_maze_contains_no_cul_de_sac_at_all(self):
        # Which is why CULDESAC had to be hand-built: MAZE-5 forbids the
        # shape, so GHOST-3's last clause has no other way to be reached.
        for seed in range(20):
            maze = mazelib.generate(random.Random(seed))
            worst = min(maze.corridor_degree(p) for p in maze.corridors())
            self.assertGreaterEqual(worst, 2, "seed %d" % seed)

    def test_the_cross_lattice_has_the_junctions_the_tests_rely_on(self):
        maze = board(CROSS)
        self.assertEqual((maze.height, maze.width), (9, 9))
        self.assertEqual(maze.corridor_degree((3, 3)), 4)
        self.assertEqual(maze.corridor_degree((3, 5)), 4)
        self.assertEqual(maze.corridor_degree((3, 1)), 3)
        self.assertEqual(maze.corridor_degree((3, 7)), 3)
        self.assertEqual(maze.corridor_degree((3, 2)), 2)

    def test_the_circuit_has_the_two_three_way_squares_ghost_4_relies_on(self):
        maze = board(CIRCUIT)
        self.assertEqual((maze.height, maze.width), (9, 9))
        # (1, 4): wall above, and the ways on are down, left and right.
        self.assertTrue(maze.is_wall((0, 4)))
        self.assertEqual(
            maze.open_directions((1, 4)), (DOWN, LEFT, RIGHT)
        )
        # (4, 4): wall to the right, and the ways on are up, down and left.
        self.assertTrue(maze.is_wall((4, 5)))
        self.assertEqual(maze.open_directions((4, 4)), (UP, DOWN, LEFT))

    def test_the_circuit_player_strip_is_walled_off_too(self):
        maze = board(CIRCUIT)
        for col in range(1, 8):
            self.assertTrue(maze.is_corridor((7, col)))
            self.assertNotIn(Position(7, col), self._reachable_from(maze, (1, 4)))

    def test_a_regular_lattice_gives_the_ghost_almost_nothing_to_decide(self):
        """The measurement behind GHOST-4 being run on CIRCUIT, not CROSS.

        Two hundred ticks from every square and heading on CROSS, and the
        ghost's path is the same whichever seed it is handed — it settles
        into a cycle in which the way ahead is always either open or the
        only way left. CIRCUIT, by contrast, answers to the seed. This is a
        fact about the boards, asserted the same way the GHOST-4 tests
        assert it: by changing the seed and looking.
        """
        cross = board(CROSS)
        seed_sensitive = 0
        for square in sorted(cross.corridors()):
            if square.row >= 7:          # the walled-off strip
                continue
            for heading in cross.open_directions(square):
                runs = set()
                for seed in (1, 2, 3, 4):
                    runs.add(
                        tuple(
                            walk(
                                state_on(
                                    CROSS, ghost=square, ghost_dir=heading
                                ),
                                random.Random(seed),
                                200,
                            )
                        )
                    )
                if len(runs) > 1:
                    seed_sensitive += 1
        self.assertEqual(
            seed_sensitive,
            0,
            "CROSS turned out to offer the ghost a real fork after all, so "
            "the note at the top of this file is now wrong",
        )
        self.assertNotEqual(
            walk(state_on(CIRCUIT, ghost=(1, 4), ghost_dir=UP),
                 random.Random(1), 200),
            walk(state_on(CIRCUIT, ghost=(1, 4), ghost_dir=UP),
                 random.Random(2), 200),
        )

    @staticmethod
    def _reachable_from(maze, square):
        reached = set()
        frontier = [Position(*square)]
        while frontier:
            here = frontier.pop()
            if here in reached:
                continue
            reached.add(here)
            frontier.extend(maze.open_neighbours(here))
        return reached

    def test_the_cross_player_strip_is_walled_off_from_the_lattice(self):
        # The whole of the GHOST-4 comparison rests on this: if row 7 were
        # reachable, a run could end in a catch and two paths could agree
        # for the wrong reason.
        maze = board(CROSS)
        reached = set()
        frontier = [Position(1, 1)]
        while frontier:
            here = frontier.pop()
            if here in reached:
                continue
            reached.add(here)
            frontier.extend(maze.open_neighbours(here))
        for col in range(1, 8):
            self.assertTrue(maze.is_corridor((7, col)))
            self.assertNotIn(Position(7, col), reached)
        self.assertIn(Position(3, 3), reached)


if __name__ == "__main__":
    unittest.main()
