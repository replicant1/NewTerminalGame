# -*- coding: utf-8 -*-
"""The ghost's policy — GHOST-2, GHOST-3, GHOST-4 and SCORE-4.

Two of these requirements are negative — *does not hunt*, *turns back only
when there is no other choice* — and a negative requirement is where a test
goes vacuous most easily, because **an implementation that never does the
thing at all passes every test that checks it did not do the thing.**

So each negative is paired with the positive that makes it mean something:

* GHOST-3 says the ghost turns back only as a last resort. A ghost that could
  never turn back would satisfy every "it did not reverse" assertion. So there
  is a test that it **does** reverse, in a dead end built by hand — the
  generator cannot make one, since MAZE-5 forbids it.
* GHOST-4 says the ghost takes no notice of the player. A test that runs the
  ghost once and finds it did not move towards the player proves nothing. So
  GHOST-4 is checked two ways: **structurally**, that the player is not a
  parameter of the policy at all, and **by consequence**, running the same
  ghost from the same state with the player on every corridor square of the
  maze in turn and requiring the move to be identical every time.
"""

from __future__ import annotations

import inspect
import random
import unittest

from terminalgame.domain.game_state import (
    GameState,
    Outcome,
    new_game,
    open_game_on,
)
from terminalgame.domain.maze import (
    DIRECTIONS,
    EAST,
    NORTH,
    SOUTH,
    WEST,
    Maze,
)
from terminalgame.domain.maze_generator import generate_maze
from terminalgame.domain.ghost_policy import (
    choose_heading,
    ghost_move,
    move_ghost,
    ways_on,
)

# A corridor with nothing else in it. The ghost should walk the length of it.
LONG_CORRIDOR = Maze.from_text(
    "#########\n"
    "#.......#\n"
    "#########", wall="#")

# A T: the stem comes down from the north into a corridor running east-west.
# A ghost arriving southwards at (2, 2) has no ahead, and two others.
TEE = Maze.from_text(
    "#####\n"
    "##.##\n"
    "#...#\n"
    "#####", wall="#")

# A dead end at (1, 1): the only way on is east. The generator cannot produce
# this — MAZE-5 forbids it — so it has to be written out.
DEAD_END = Maze.from_text(
    "#####\n"
    "#...#\n"
    "#####", wall="#")

# A crossroads: a ghost driving through it has an ahead *and* two side
# openings, which is the case GHOST-2 has to win.
CROSSROADS = Maze.from_text(
    "#####\n"
    "##.##\n"
    "#...#\n"
    "##.##\n"
    "#####", wall="#")


def state_on(maze, ghost, heading, player=None, dots=None, score=0):
    """A game state placed by hand, for cases the generator cannot reach."""
    corridors = maze.corridor_squares()
    if player is None:
        player = corridors[0]
    if dots is None:
        dots = frozenset(corridors) - {player}
    return GameState(maze=maze, player=player, ghost=ghost,
                     ghost_heading=heading, dots=dots, score=score,
                     outcome=Outcome.PLAYING)


class CarryingStraightOnTest(unittest.TestCase):
    """GHOST-2 — a straight line for as long as the corridor lets it."""

    def test_it_walks_the_whole_length_of_a_straight_corridor(self):
        square, heading = (1, 1), EAST
        walked = [square]
        for _ in range(6):
            square, heading = ghost_move(LONG_CORRIDOR, square, heading,
                                         random.Random(0))
            walked.append(square)
            self.assertEqual(EAST, heading)
        self.assertEqual([(x, 1) for x in range(1, 8)], walked)

    def test_it_carries_on_even_where_there_are_side_openings(self):
        # The crossroads case. "For as long as the corridor lets it" means the
        # ghost does not stop to choose at a junction it can drive through --
        # and the random source is never consulted, so a source that would
        # raise if used proves it.
        class NeverAsked:
            def choice(self, options):
                raise AssertionError(
                    "the ghost consulted chance at a crossroads it could "
                    "drive straight through (GHOST-2)")

        square, heading = ghost_move(CROSSROADS, (2, 2), EAST, NeverAsked())
        self.assertEqual((3, 2), square)
        self.assertEqual(EAST, heading)

        square, heading = ghost_move(CROSSROADS, (2, 2), SOUTH, NeverAsked())
        self.assertEqual((2, 3), square)
        self.assertEqual(SOUTH, heading)

    def test_going_straight_on_is_not_an_accident_of_the_direction_order(self):
        # North comes first in DIRECTIONS, so a policy that just took the
        # first way on would look right whenever the ghost was heading north.
        # These head the other three ways through the same crossroads.
        for heading, expected in ((SOUTH, (2, 3)), (EAST, (3, 2)), (WEST, (1, 2))):
            square, new_heading = ghost_move(CROSSROADS, (2, 2), heading,
                                             random.Random(0))
            self.assertEqual(expected, square, heading.name)
            self.assertEqual(heading, new_heading, heading.name)

    def test_over_a_whole_maze_it_never_turns_where_it_could_go_straight(self):
        for seed in range(20):
            maze = generate_maze(seed)
            state = new_game(seed)
            square, heading = state.ghost, state.ghost_heading
            source = random.Random(seed)
            for _ in range(60):
                before = heading
                could_go_straight = before in ways_on(maze, square)
                square, heading = ghost_move(maze, square, heading, source)
                if could_go_straight:
                    self.assertEqual(before, heading,
                                     "seed {0} at {1}".format(seed, square))


class ChoosingAtAJunctionTest(unittest.TestCase):
    """GHOST-3 — pick at random among the others; turn back only if forced."""

    def test_at_a_tee_it_never_carries_on_because_there_is_no_ahead(self):
        square, heading = ghost_move(TEE, (2, 2), SOUTH, random.Random(0))
        self.assertNotEqual(SOUTH, heading)
        self.assertNotEqual((2, 3), square)

    def test_over_many_runs_it_visits_every_branch_of_a_tee(self):
        # "picks one of the other ways on at random" -- so over enough seeds
        # both branches come up. A policy that always took the first would
        # pass a single-run test and fail this one.
        chosen = set()
        for seed in range(60):
            _, heading = ghost_move(TEE, (2, 2), SOUTH, random.Random(seed))
            chosen.add(heading.name)
        self.assertEqual({"east", "west"}, chosen)

    def test_it_never_turns_back_at_a_tee_where_anything_else_is_open(self):
        for seed in range(60):
            _, heading = ghost_move(TEE, (2, 2), SOUTH, random.Random(seed))
            self.assertNotEqual(NORTH, heading,
                                "the ghost turned back with two other ways "
                                "open (GHOST-3), seed {0}".format(seed))

    def test_it_does_turn_back_in_a_dead_end(self):
        # The test that makes the one above mean something. Without it, a
        # ghost that could never reverse would satisfy every assertion here.
        square, heading = ghost_move(DEAD_END, (1, 1), WEST, random.Random(0))
        self.assertEqual(EAST, heading)
        self.assertEqual((2, 1), square)

    def test_it_turns_back_from_every_direction_into_a_dead_end(self):
        # Arriving at (1, 1) heading west is the natural case; heading north
        # or south into it is constructible and must behave the same way,
        # because in all three the only way on is east.
        for heading in (WEST, NORTH, SOUTH):
            square, new_heading = ghost_move(DEAD_END, (1, 1), heading,
                                             random.Random(0))
            self.assertEqual(EAST, new_heading, heading.name)
            self.assertEqual((2, 1), square, heading.name)

    def test_across_generated_mazes_it_reverses_only_when_forced(self):
        # MAZE-5 means a generated maze has no dead ends, so over these runs
        # the ghost should never reverse at all. That is only worth asserting
        # because the dead-end tests above show it can.
        reversals = 0
        for seed in range(20):
            maze = generate_maze(seed)
            state = new_game(seed)
            square, heading = state.ghost, state.ghost_heading
            source = random.Random(seed)
            for _ in range(80):
                before = heading
                square, heading = ghost_move(maze, square, heading, source)
                if heading is before.opposite():
                    reversals += 1
                    self.assertEqual(
                        [before.opposite()], ways_on(maze, square),
                        "seed {0}: reversed at {1} with other ways open"
                        .format(seed, square))
        self.assertEqual(0, reversals,
                         "a maze with no dead ends should never force a "
                         "reversal (MAZE-5)")

    def test_the_chosen_way_is_always_one_the_ghost_can_actually_travel(self):
        for seed in range(20):
            maze = generate_maze(seed)
            state = new_game(seed)
            square, heading = state.ghost, state.ghost_heading
            source = random.Random(seed)
            for _ in range(60):
                square, heading = ghost_move(maze, square, heading, source)
                self.assertTrue(maze.is_corridor(*square),
                                "the ghost left the corridors at {0}".format(square))
                self.assertIn(heading, DIRECTIONS)


class TakesNoNoticeOfThePlayerTest(unittest.TestCase):
    """GHOST-4, checked structurally and by consequence."""

    def test_the_player_is_not_a_parameter_of_the_policy(self):
        # The strongest form available: a function that cannot see the player
        # cannot take notice of them. This is a property of the code, not a
        # claim about its behaviour.
        for function in (choose_heading, ghost_move, ways_on):
            names = list(inspect.signature(function).parameters)
            self.assertNotIn("player", names, function.__name__)
            for name in names:
                self.assertNotIn("player", name.lower(), function.__name__)

    def test_the_policy_takes_only_the_maze_the_square_and_the_heading(self):
        # Stated positively too, so that a parameter added later has to be a
        # deliberate act rather than a slip.
        self.assertEqual(["maze", "square", "heading", "random_source"],
                         list(inspect.signature(choose_heading).parameters))
        self.assertEqual(["maze", "square", "heading", "random_source"],
                         list(inspect.signature(ghost_move).parameters))

    def test_the_ghost_moves_the_same_way_wherever_the_player_stands(self):
        # The consequence form, and the plan's own words: "with the player
        # standing in every possible square in turn, the ghost's chosen move
        # is identical". `move_ghost` is handed the whole state, player and
        # all, so this is where the guarantee would actually be lost.
        maze = generate_maze(4)
        opened = open_game_on(maze, random.Random(4))
        expected = None
        for player in maze.corridor_squares():
            if player == opened.ghost:
                continue
            state = opened.with_changes(player=player)
            moved = move_ghost(state, random.Random(0))
            result = (moved.ghost, moved.ghost_heading)
            if expected is None:
                expected = result
            self.assertEqual(expected, result,
                             "the ghost moved differently with the player at "
                             "{0}".format(player))
        self.assertIsNotNone(expected)

    def test_that_holds_over_a_long_run_not_just_one_move(self):
        # A ghost that hunted only when close would survive a single move.
        maze = generate_maze(8)
        opened = open_game_on(maze, random.Random(8))
        corridors = maze.corridor_squares()
        walks = []
        for player in (corridors[0], corridors[len(corridors) // 2],
                       corridors[-1]):
            state = opened.with_changes(player=player)
            source = random.Random(3)
            walk = []
            for _ in range(50):
                state = move_ghost(state, source)
                walk.append((state.ghost, state.ghost_heading.name))
            walks.append(walk)
        self.assertEqual(walks[0], walks[1])
        self.assertEqual(walks[0], walks[2])

    def test_the_ghost_will_walk_onto_the_players_square(self):
        # The other half of "takes no notice": it does not avoid the player
        # either. Put the player directly ahead of a ghost in a corridor and
        # the ghost walks onto them -- which is the collision WI-10 rules on.
        state = state_on(LONG_CORRIDOR, ghost=(1, 1), heading=EAST,
                         player=(2, 1))
        moved = move_ghost(state, random.Random(0))
        self.assertEqual((2, 1), moved.ghost)
        self.assertEqual(moved.player, moved.ghost)


class TouchesNeitherDotsNorScoreTest(unittest.TestCase):
    """SCORE-4 — a dot under the ghost is still there to be taken."""

    def test_a_ghost_move_changes_nothing_but_the_ghost_and_its_heading(self):
        # Over enough moves that both a straight-on step (ghost only) and a
        # turn (ghost and heading) are covered; what must never appear in this
        # list is anything else.
        state = new_game(12)
        source = random.Random(0)
        moved_at_all = set()
        for _ in range(60):
            after = move_ghost(state, source)
            changed = set(name for name in GameState.FIELDS
                          if getattr(state, name) != getattr(after, name))
            self.assertEqual(set(), changed - {"ghost", "ghost_heading"},
                             "a ghost move changed something it has no "
                             "business changing")
            moved_at_all |= changed
            state = after
        # And it really did move, and really did turn at some point, or the
        # assertion above would be true of a ghost that did nothing.
        self.assertEqual({"ghost", "ghost_heading"}, moved_at_all)

    def test_the_dot_the_ghost_walks_onto_is_still_there(self):
        state = new_game(13)
        for _ in range(40):
            state = move_ghost(state, random.Random(1))
            self.assertTrue(state.dot_at(state.ghost),
                            "the ghost is standing on {0} and the dot has "
                            "gone".format(state.ghost))

    def test_a_long_ghost_run_eats_nothing_and_scores_nothing(self):
        state = new_game(14)
        dots_before, score_before = state.dots, state.score
        source = random.Random(2)
        for _ in range(200):
            state = move_ghost(state, source)
        self.assertEqual(dots_before, state.dots)
        self.assertEqual(score_before, state.score)
        self.assertEqual(0, state.score)

    def test_the_state_it_was_given_is_not_altered(self):
        # GameState is immutable, so this cannot fail by assignment -- but it
        # could by handing back the same object, and then a caller holding the
        # old state would see the ghost teleport.
        state = new_game(15)
        before = state.ghost
        moved = move_ghost(state, random.Random(0))
        self.assertEqual(before, state.ghost)
        self.assertIsNot(state, moved)

    def test_it_does_not_decide_the_outcome(self):
        # Caution C6: the ordered rule is WI-10's one function. A ghost move
        # that set `caught` here would put that decision in two places.
        state = state_on(LONG_CORRIDOR, ghost=(1, 1), heading=EAST,
                         player=(2, 1))
        moved = move_ghost(state, random.Random(0))
        self.assertEqual(moved.player, moved.ghost)
        self.assertEqual(Outcome.PLAYING, moved.outcome)


class ReproducibleTest(unittest.TestCase):
    """Plan §3 — randomness enters only through a source handed in."""

    @staticmethod
    def walk(game_seed, source_seed, steps=200):
        state = new_game(game_seed)
        source = random.Random(source_seed)
        path = []
        for _ in range(steps):
            state = move_ghost(state, source)
            path.append((state.ghost, state.ghost_heading.name))
        return path

    def test_the_same_seed_gives_the_same_walk(self):
        self.assertEqual(self.walk(20, 5), self.walk(20, 5))

    def test_different_sources_give_different_walks(self):
        # Otherwise "reproducible" would be indistinguishable from "fixed",
        # and the random source would not be doing anything at all.
        #
        # Game seed 0 is used rather than an arbitrary one because the ghost
        # there first faces a real choice at step 10 — measured, see
        # `docs/findings/WI-9-the-ghost-that-cannot-get-out.md`. On a maze
        # where it never faces one, every source gives the same walk and that
        # is correct behaviour, not a failure; the test below is about those.
        walks = set(tuple(self.walk(0, source)) for source in range(10))
        self.assertGreater(len(walks), 1)

    def test_the_random_source_is_required_rather_than_defaulted(self):
        # A default would let a caller get an unreproducible ghost by
        # forgetting an argument, which is exactly how §3 gets broken quietly.
        for function in (choose_heading, ghost_move, move_ghost):
            parameters = inspect.signature(function).parameters
            self.assertIs(inspect.Parameter.empty,
                          parameters["random_source"].default,
                          function.__name__)


class NowhereToGoTest(unittest.TestCase):
    """A ghost walled in on all four sides. Not reachable through MAZE-5."""

    WALLED_IN = Maze.from_text("###\n#.#\n###", wall="#")

    def test_it_stays_where_it_is_and_keeps_its_heading(self):
        square, heading = ghost_move(self.WALLED_IN, (1, 1), NORTH,
                                     random.Random(0))
        self.assertEqual((1, 1), square)
        self.assertEqual(NORTH, heading)

    def test_it_does_not_consult_chance_when_there_is_no_choice(self):
        class NeverAsked:
            def choice(self, options):
                raise AssertionError("there was nothing to choose between")

        self.assertEqual(NORTH, choose_heading(self.WALLED_IN, (1, 1), NORTH,
                                               NeverAsked()))

    def test_the_generator_never_produces_such_a_square(self):
        # Which is why the case above is written out by hand: MAZE-5 gives
        # every corridor square at least two ways on. Says out loud that the
        # branch is unreachable in play rather than leaving it looking like a
        # case somebody should have seen.
        for seed in range(20):
            maze = generate_maze(seed)
            for square in maze.corridor_squares():
                self.assertGreaterEqual(len(ways_on(maze, square)), 2,
                                        (seed, square))


class ConfinedToALoopTest(unittest.TestCase):
    """A consequence of GHOST-2 and GHOST-3 that is worth pinning.

    The ghost consults chance only where it cannot carry on **and** two or
    more ways other than back are open. Round a closed ring of corridor, every
    corner offers exactly one other way — so the ghost goes round for ever and
    no random source can alter it.

    This is correct under GHOST-2 and GHOST-3 as written, and it is measured
    at **8 games in 500** in `docs/findings/WI-9-the-ghost-that-cannot-get-out.md`.
    It is pinned here so that it is a known property rather than a surprise,
    and so that anyone who later changes the policy sees which tests move.

    **It sits awkwardly with GHOST-1's "one ghost roams the maze"** — that is
    raised in the PR summary for a ruling and is not this module's to decide.
    """

    #: Measured, not chosen: seeds whose ghost never faces a real choice.
    CONFINED_SEEDS = (21, 26)

    def faces_a_choice_within(self, game_seed, steps):
        state = new_game(game_seed)
        maze = state.maze
        square, heading = state.ghost, state.ghost_heading
        source = random.Random(game_seed)
        for _ in range(steps):
            available = ways_on(maze, square)
            if heading not in available:
                others = [d for d in available if d is not heading.opposite()]
                if len(others) > 1:
                    return True
            square, heading = ghost_move(maze, square, heading, source)
        return False

    def test_on_most_mazes_the_ghost_soon_faces_a_real_choice(self):
        # The positive half. Without it, the test below would be satisfied by
        # a ghost that never chose anything anywhere.
        facing = [seed for seed in range(30)
                  if self.faces_a_choice_within(seed, 400)]
        self.assertGreater(len(facing), 25)

    def test_on_a_few_mazes_it_never_does_and_every_source_agrees(self):
        for seed in self.CONFINED_SEEDS:
            self.assertFalse(self.faces_a_choice_within(seed, 400),
                             "seed {0} was measured as confined".format(seed))
            walks = set()
            for source_seed in range(8):
                state = new_game(seed)
                source = random.Random(source_seed)
                path = []
                for _ in range(120):
                    state = move_ghost(state, source)
                    path.append(state.ghost)
                walks.add(tuple(path))
            self.assertEqual(1, len(walks),
                             "seed {0} faces no choice, so chance cannot "
                             "change its walk".format(seed))

    def test_a_confined_ghost_still_obeys_every_rule_it_is_given(self):
        # The point of the finding: this is not a bug in the policy. The ghost
        # goes straight where it can, never reverses, and stays on corridor.
        seed = self.CONFINED_SEEDS[0]
        state = new_game(seed)
        maze = state.maze
        square, heading = state.ghost, state.ghost_heading
        source = random.Random(0)
        for _ in range(200):
            before, came_from = heading, heading.opposite()
            could_go_straight = before in ways_on(maze, square)
            square, heading = ghost_move(maze, square, heading, source)
            self.assertTrue(maze.is_corridor(*square))
            if could_go_straight:
                self.assertEqual(before, heading)
            self.assertIsNot(came_from, heading)


class TheDomainScanCoversThisModuleTest(unittest.TestCase):
    """That `ghost_policy.py` is inside the Domain's purity sweep.

    `tests/test_layering.py` walks the whole package, so this module is swept
    automatically and needs no entry in the list there. The assertion lives
    here rather than as a line added to that list because **DEV-A made the
    same choice for `player.py` in WI-8**, and an adjacent-line edit in one
    shared list is a predictable conflict between two lanes for no benefit.

    Recorded rather than silent, so the asymmetry with `maze.py` and
    `maze_generator.py` — which are listed there — reads as a decision.
    """

    def test_the_purity_sweep_includes_the_ghost_policy(self):
        from tests.test_layering import THE_DOMAIN, domain_files
        import os
        names = [name for name, _ in domain_files()]
        self.assertIn(os.path.join(THE_DOMAIN, "ghost_policy.py"), names)

    def test_the_ghost_policy_imports_nothing_at_all_from_outside_the_domain(self):
        from tests.test_layering import imported_game_modules, source_of
        import terminalgame.domain.ghost_policy as module
        imported = imported_game_modules(source_of(module.__file__))
        self.assertEqual([], imported,
                         "the policy needs nothing but its arguments; it does "
                         "not even import the maze")


class WaysOnTest(unittest.TestCase):

    def test_it_gives_the_directions_that_lead_onto_corridor(self):
        self.assertEqual(["east"], [d.name for d in ways_on(DEAD_END, (1, 1))])
        self.assertEqual(["east", "west"],
                         [d.name for d in ways_on(DEAD_END, (2, 1))])

    def test_it_gives_them_in_the_mazes_own_direction_order(self):
        # North, south, east, west. The order is what makes a seeded ghost
        # reproducible, so it is worth pinning rather than assuming.
        names = [d.name for d in ways_on(CROSSROADS, (2, 2))]
        self.assertEqual(["north", "south", "east", "west"], names)

    def test_a_walled_in_square_has_no_ways_on(self):
        self.assertEqual([], ways_on(Maze.from_text("###\n#.#\n###", wall="#"),
                                     (1, 1)))


if __name__ == "__main__":
    unittest.main()
