"""WI-7 — the game state and the opening position. START-1 to START-5, GAME-3.

Where a placement rule is tested, it is tested by **searching the maze** rather
than by recomputing the formula the code used: no corridor square is nearer the
centre than the player's, and none is further from the player than the ghost's.
A test that reapplied `min` with the same key would agree with the code however
wrong they both were.

The metric tests are written so that they would fail on Manhattan and on
Chebyshev, because "it satisfies START-2's words" is exactly what those two also
do. `DISTANCE_METRIC` is an assumption and not a ruling.
"""

from __future__ import annotations

import random
import unittest

from terminalgame.domain import game_state
from terminalgame.domain.game_state import (
    DISTANCE_METRIC,
    GameState,
    NoCorridorToStartOn,
    Outcome,
    furthest_from,
    nearest_to_centre,
    new_game,
    new_game_with,
    open_game_on,
    opening_heading,
    squared_distance,
)
from terminalgame.domain.maze import CORRIDOR, DIRECTIONS, WALL, Maze, solid
from terminalgame.domain.maze_generator import generate_maze

#: Enough seeds to be sure the placement rules are not true by luck on one maze,
#: few enough that the suite stays quick.
SEEDS = range(30)

#: Odd on both sides, as the generator requires, and none of them 19 x 29.
#: Plan §11.9: keep testing at other sizes, because a screen dimension
#: hard-coded anywhere in the Domain fails these outright.
OTHER_SIZES = ((7, 7), (9, 13), (11, 9), (13, 21), (21, 11))


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def maze_from_lines(lines):
    return Maze.from_text("\n".join(lines))


#: A hand-built maze with deliberate ties, for pinning the tie-break rule.
#: Centre of a 5 x 5 grid is (2, 2), which is wall here. Four corridor squares
#: sit equally near it and two sit equally far from the player.
TIED = [
    "#####",
    "#   #",
    "# # #",
    "#   #",
    "#####",
]


class TheMetricIsStraightLine(unittest.TestCase):
    """Q3 / START-2. Stated, pinned, and recorded as an assumption."""

    def test_it_is_the_squared_euclidean_distance(self):
        # 3-4-5: the one triangle where the three candidate metrics disagree
        # by amounts nobody can mistake for rounding.
        self.assertEqual(25, squared_distance((0, 0), (3, 4)))

    def test_it_is_not_manhattan(self):
        a, b = (0, 0), (3, 4)
        self.assertEqual(7, manhattan(a, b))
        self.assertNotEqual(manhattan(a, b) ** 2, squared_distance(a, b))

    def test_it_is_not_chebyshev(self):
        a, b = (0, 0), (3, 4)
        self.assertEqual(4, chebyshev(a, b))
        self.assertNotEqual(chebyshev(a, b) ** 2, squared_distance(a, b))

    def test_the_metrics_disagree_about_which_square_is_further(self):
        """Why the choice had to be made rather than left implicit.

        From the origin, (0, 5) is **further** than (3, 3) under straight-line
        distance — 25 against 18 — and **nearer** under Manhattan — 5 against
        6. START-2 puts the ghost on the furthest square, so the two metrics
        would start it in different places on the same maze. That is what makes
        this an assumption worth writing down rather than a detail.
        """
        origin, along, diagonal = (0, 0), (0, 5), (3, 3)
        self.assertGreater(squared_distance(origin, along),
                           squared_distance(origin, diagonal))
        self.assertLess(manhattan(origin, along), manhattan(origin, diagonal))

    def test_it_is_symmetric_and_zero_only_on_the_same_square(self):
        self.assertEqual(squared_distance((2, 7), (5, 1)),
                         squared_distance((5, 1), (2, 7)))
        self.assertEqual(0, squared_distance((4, 4), (4, 4)))

    def test_the_metric_is_written_down(self):
        # "State which metric" — the plan asks for it in words, not only in
        # code, because the next person needs to know it was a choice.
        self.assertIn("straight-line", DISTANCE_METRIC)


class WhereThePlayerStarts(unittest.TestCase):
    """START-1 — the corridor square nearest the middle."""

    def test_the_player_is_always_on_a_corridor_square(self):
        for seed in SEEDS:
            state = new_game(seed)
            self.assertTrue(state.maze.is_corridor(*state.player),
                            "seed %d put the player at %r, which is wall"
                            % (seed, state.player))

    def test_no_corridor_square_is_nearer_the_middle(self):
        """Searched, not recomputed — see the module docstring."""
        for seed in SEEDS:
            state = new_game(seed)
            maze = state.maze
            centre = (maze.width - 1, maze.height - 1)   # doubled
            chosen = squared_distance(
                (2 * state.player[0], 2 * state.player[1]), centre)
            for square in maze.corridor_squares():
                rival = squared_distance((2 * square[0], 2 * square[1]), centre)
                self.assertLessEqual(
                    chosen, rival,
                    "seed %d: %r is nearer the middle than the player's %r"
                    % (seed, square, state.player))

    def test_it_lands_on_the_exact_centre_when_that_is_corridor(self):
        # The strongest case of START-1, and one a "nearest" rule could get
        # wrong while still looking plausible on the mazes above.
        maze = maze_from_lines([
            "#####",
            "#   #",
            "#   #",
            "#   #",
            "#####",
        ])
        self.assertEqual((2, 2), nearest_to_centre(maze))

    def test_ties_go_to_the_first_square_in_reading_order(self):
        maze = maze_from_lines(TIED)
        centre = (maze.width - 1, maze.height - 1)
        nearest = squared_distance((2 * 2, 2 * 1), centre)
        tied = [square for square in maze.corridor_squares()
                if squared_distance((2 * square[0], 2 * square[1]), centre)
                == nearest]
        # There really is a tie to break, otherwise this proves nothing.
        self.assertEqual([(2, 1), (1, 2), (3, 2), (2, 3)], tied)
        self.assertEqual((2, 1), nearest_to_centre(maze))

    def test_the_same_maze_always_places_the_player_on_the_same_square(self):
        maze = generate_maze(11)
        self.assertEqual(nearest_to_centre(maze), nearest_to_centre(maze))


class WhereTheGhostStarts(unittest.TestCase):
    """START-2 — the corridor square furthest from the player."""

    def test_the_ghost_is_always_on_a_corridor_square(self):
        for seed in SEEDS:
            state = new_game(seed)
            self.assertTrue(state.maze.is_corridor(*state.ghost))

    def test_no_corridor_square_is_further_from_the_player(self):
        for seed in SEEDS:
            state = new_game(seed)
            chosen = squared_distance(state.player, state.ghost)
            for square in state.maze.corridor_squares():
                self.assertGreaterEqual(
                    chosen, squared_distance(state.player, square),
                    "seed %d: %r is further from the player than the ghost's %r"
                    % (seed, square, state.ghost))

    def test_the_ghost_never_starts_on_the_player(self):
        for seed in SEEDS:
            state = new_game(seed)
            self.assertNotEqual(state.player, state.ghost)

    def test_they_start_well_apart(self):
        """The purpose clause of START-2, not merely its mechanism.

        The ceiling is how far the grid could put the ghost from this player at
        all — the furthest of the four corners, whether or not it is corridor.
        Asking for at least half of that (in squared terms) is a bar a real
        maximisation clears comfortably and a placement that had stopped
        maximising would not.
        """
        for seed in SEEDS:
            state = new_game(seed)
            corners = [(0, 0),
                       (state.maze.width - 1, 0),
                       (0, state.maze.height - 1),
                       (state.maze.width - 1, state.maze.height - 1)]
            ceiling = max(squared_distance(state.player, corner)
                          for corner in corners)
            self.assertGreater(squared_distance(state.player, state.ghost),
                               ceiling / 2.0,
                               "seed %d started them too close together" % seed)

    def test_ties_go_to_the_first_square_in_reading_order(self):
        maze = maze_from_lines(TIED)
        player = (2, 1)
        furthest = max(squared_distance(player, square)
                       for square in maze.corridor_squares())
        tied = [square for square in maze.corridor_squares()
                if squared_distance(player, square) == furthest]
        self.assertEqual([(1, 3), (3, 3)], tied)
        self.assertEqual((1, 3), furthest_from(maze, player))


class WhereTheDotsAre(unittest.TestCase):
    """START-3 — every corridor square but the player's."""

    def test_every_corridor_square_except_the_players_holds_a_dot(self):
        for seed in SEEDS:
            state = new_game(seed)
            expected = set(state.maze.corridor_squares()) - {state.player}
            self.assertEqual(expected, set(state.dots))

    def test_the_count_is_the_corridor_count_less_one(self):
        for seed in SEEDS:
            state = new_game(seed)
            self.assertEqual(len(state.maze.corridor_squares()) - 1,
                             state.dots_remaining)

    def test_the_player_starts_on_the_one_square_without_a_dot(self):
        for seed in SEEDS:
            state = new_game(seed)
            self.assertFalse(state.dot_at(state.player))

    def test_the_ghost_starts_on_a_square_that_does_hold_a_dot(self):
        """START-3 excepts the player's square and no other.

        This is what makes END-3 reachable at all — the last dot of a game can
        be the one underneath the ghost. WI-10 depends on it, so it is pinned
        here rather than left as a consequence nobody stated.
        """
        for seed in SEEDS:
            state = new_game(seed)
            self.assertTrue(state.dot_at(state.ghost),
                            "seed %d left the ghost's square empty" % seed)

    def test_no_dot_is_ever_on_a_wall(self):
        for seed in SEEDS:
            state = new_game(seed)
            for square in state.dots:
                self.assertTrue(state.maze.is_corridor(*square))


class HowAGameOpens(unittest.TestCase):
    """START-4 and START-5, and the shape of a fresh state."""

    def test_the_score_starts_at_zero(self):
        for seed in SEEDS:
            self.assertEqual(0, new_game(seed).score)

    def test_the_game_is_already_under_way(self):
        for seed in SEEDS:
            state = new_game(seed)
            self.assertEqual(Outcome.PLAYING, state.outcome)
            self.assertFalse(state.is_over)

    def test_the_ghost_is_already_moving(self):
        """START-5 — "the ghost is already moving".

        So it has a heading from the first instant, and the heading is a way it
        can actually travel rather than a direction into the wall it would
        spend its first move turning away from.
        """
        for seed in SEEDS:
            state = new_game(seed)
            self.assertIn(state.ghost_heading, DIRECTIONS)
            ahead = state.ghost_heading.from_square(*state.ghost)
            self.assertTrue(
                state.maze.is_corridor(*ahead),
                "seed %d headed the ghost at %r into a wall" % (seed, ahead))

    def test_a_heading_is_chosen_from_the_ways_on(self):
        maze = maze_from_lines([
            "#####",
            "#   #",
            "# # #",
            "#   #",
            "#####",
        ])
        # (1, 1) has exactly two ways on: east and south.
        headings = {opening_heading(maze, (1, 1), random.Random(seed)).name
                    for seed in range(40)}
        self.assertEqual({"east", "south"}, headings)

    def test_a_square_with_nowhere_to_go_still_yields_a_heading(self):
        # Not producible by the generator (MAZE-5), but constructible by hand,
        # and a ghost with nowhere to go is a maze problem rather than a reason
        # for opening a game to fail.
        island = maze_from_lines([
            "###",
            "# #",
            "###",
        ])
        self.assertIn(opening_heading(island, (1, 1), random.Random(0)),
                      DIRECTIONS)


class TheSameSeedGivesTheSameGame(unittest.TestCase):

    def test_one_seed_names_one_opening_position(self):
        for seed in SEEDS:
            self.assertEqual(new_game(seed), new_game(seed))

    def test_every_field_of_it_and_not_merely_the_maze(self):
        first, second = new_game(5), new_game(5)
        for field in GameState.FIELDS:
            self.assertEqual(getattr(first, field), getattr(second, field),
                             "%s differed between two games on seed 5" % field)

    def test_no_state_carries_between_calls(self):
        # Making other games in between must not shift the one that follows.
        expected = new_game(7)
        for other in range(4):
            new_game(100 + other)
        self.assertEqual(expected, new_game(7))

    def test_different_seeds_give_different_games(self):
        games = [new_game(seed) for seed in SEEDS]
        self.assertEqual(len(games), len({game.maze for game in games}),
                         "two seeds produced the same maze")
        self.assertGreater(len({game.ghost for game in games}), 1)

    def test_a_caller_can_own_the_whole_games_randomness(self):
        self.assertEqual(new_game_with(random.Random(3)),
                         new_game_with(random.Random(3)))


class AStateIsImmutable(unittest.TestCase):

    def setUp(self):
        self.state = new_game(1)

    def test_a_field_cannot_be_assigned_to(self):
        with self.assertRaises(AttributeError):
            self.state.score = 99

    def test_a_field_cannot_be_deleted(self):
        with self.assertRaises(AttributeError):
            del self.state.player

    def test_the_dots_cannot_be_added_to(self):
        self.assertIsInstance(self.state.dots, frozenset)
        with self.assertRaises(AttributeError):
            self.state.dots.add((0, 0))

    def test_with_changes_leaves_the_original_alone(self):
        before_score = self.state.score
        before_dots = self.state.dots
        moved = self.state.with_changes(score=10)
        self.assertEqual(10, moved.score)
        self.assertEqual(before_score, self.state.score)
        self.assertEqual(before_dots, self.state.dots)

    def test_with_changes_carries_everything_it_was_not_asked_to_change(self):
        moved = self.state.with_changes(score=3)
        for field in GameState.FIELDS:
            if field != "score":
                self.assertEqual(getattr(self.state, field),
                                 getattr(moved, field), field)

    def test_with_changes_refuses_a_field_that_does_not_exist(self):
        with self.assertRaises(TypeError) as caught:
            self.state.with_changes(lives=3)
        self.assertIn("lives", str(caught.exception))

    def test_states_with_the_same_facts_are_equal_and_hash_alike(self):
        twin = new_game(1)
        self.assertEqual(self.state, twin)
        self.assertEqual(hash(self.state), hash(twin))
        self.assertEqual({self.state, twin}, {self.state})

    def test_a_changed_state_is_not_equal_to_the_one_it_came_from(self):
        self.assertNotEqual(self.state, self.state.with_changes(score=1))

    def test_a_state_is_not_equal_to_something_that_is_not_a_state(self):
        self.assertNotEqual(self.state, "playing")


class OneGamePerProcess(unittest.TestCase):
    """GAME-3 — no lives, no levels, no timer, no pause, no restart."""

    FORBIDDEN = ("lives", "level", "timer", "time_limit", "pause", "paused",
                 "restart", "power", "bonus")

    def test_the_state_carries_none_of_the_things_game_3_rules_out(self):
        fields = set(GameState.FIELDS)
        self.assertEqual([], [name for name in self.FORBIDDEN
                              if name in fields])

    def test_the_vocabulary_is_exactly_what_the_rest_of_the_game_needs(self):
        # Pinned because WI-8, WI-9, WI-10, WI-6, WI-5b and WI-11 all speak it,
        # and a field appearing or vanishing silently would reach all six.
        self.assertEqual(
            ("maze", "player", "ghost", "ghost_heading", "dots", "score",
             "outcome"),
            tuple(GameState.FIELDS))

    def test_the_module_offers_no_way_to_restart_or_pause(self):
        public = [name for name in dir(game_state) if not name.startswith("_")]
        for name in public:
            for forbidden in self.FORBIDDEN:
                self.assertNotIn(forbidden, name.lower(),
                                 "%s looks like %s, which GAME-3 rules out"
                                 % (name, forbidden))

    def test_there_are_exactly_three_outcomes(self):
        self.assertEqual(3, len(Outcome.ALL))
        self.assertEqual(("playing", "caught", "cleared"), Outcome.ALL)


class AMazeThatCannotOpenAGame(unittest.TestCase):
    """Plan §11.8 — refuse and name the requirement, do not degrade."""

    def test_a_maze_with_no_corridor_refuses_and_names_start_1(self):
        # `solid` gives the rows the generator starts from, so it needs
        # wrapping to be a maze at all.
        nothing_but_wall = Maze(solid(5, 5))
        self.assertEqual([], nothing_but_wall.corridor_squares())
        with self.assertRaises(NoCorridorToStartOn) as caught:
            nearest_to_centre(nothing_but_wall)
        self.assertIn("START-1", str(caught.exception))

    def test_a_maze_with_one_corridor_refuses_and_names_start_2(self):
        one = maze_from_lines([
            "###",
            "# #",
            "###",
        ])
        self.assertEqual([(1, 1)], one.corridor_squares())
        with self.assertRaises(NoCorridorToStartOn) as caught:
            furthest_from(one, (1, 1))
        self.assertIn("START-2", str(caught.exception))

    def test_one_corridor_square_is_enough_for_the_player_alone(self):
        one = maze_from_lines([
            "###",
            "# #",
            "###",
        ])
        self.assertEqual((1, 1), nearest_to_centre(one))


class OnGridsOtherThanTheSpecifiedOne(unittest.TestCase):
    """Plan §11.9 — a screen dimension hard-coded in the Domain fails here."""

    def test_a_game_opens_on_every_size_and_keeps_every_start_rule(self):
        for width, height in OTHER_SIZES:
            for seed in range(5):
                state = new_game(seed, width=width, height=height)
                maze = state.maze
                self.assertEqual((width, height), (maze.width, maze.height))
                self.assertTrue(maze.is_corridor(*state.player))
                self.assertTrue(maze.is_corridor(*state.ghost))
                self.assertNotEqual(state.player, state.ghost)
                self.assertEqual(len(maze.corridor_squares()) - 1,
                                 state.dots_remaining)
                self.assertEqual(0, state.score)
                self.assertEqual(Outcome.PLAYING, state.outcome)

    def test_the_placements_are_still_extremal_at_other_sizes(self):
        for width, height in OTHER_SIZES:
            state = new_game(0, width=width, height=height)
            centre = (width - 1, height - 1)
            player_distance = squared_distance(
                (2 * state.player[0], 2 * state.player[1]), centre)
            ghost_distance = squared_distance(state.player, state.ghost)
            for square in state.maze.corridor_squares():
                self.assertLessEqual(
                    player_distance,
                    squared_distance((2 * square[0], 2 * square[1]), centre))
                self.assertGreaterEqual(
                    ghost_distance, squared_distance(state.player, square))


class OpeningAGameOnAMazeYouAlreadyHave(unittest.TestCase):

    def test_it_places_both_actors_and_lays_the_dots(self):
        maze = generate_maze(2)
        state = open_game_on(maze, random.Random(0))
        self.assertIs(maze, state.maze)
        self.assertEqual(nearest_to_centre(maze), state.player)
        self.assertEqual(furthest_from(maze, state.player), state.ghost)
        self.assertEqual(len(maze.corridor_squares()) - 1, state.dots_remaining)

    def test_a_hand_built_maze_opens_a_game_without_the_generator(self):
        maze = maze_from_lines(TIED)
        state = open_game_on(maze, random.Random(0))
        self.assertEqual((2, 1), state.player)
        self.assertEqual((1, 3), state.ghost)
        self.assertEqual(7, state.dots_remaining)


if __name__ == "__main__":
    unittest.main()
