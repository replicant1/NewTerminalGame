"""WI-8 — the player's move. CTRL-1 to CTRL-3, SCORE-1 to SCORE-3, SCORE-5.

Two of these requirements are satisfied by a function that does nothing at all,
and a careless test would not notice:

* **CTRL-3** — "a press towards a wall does nothing" is green against a
  `move_player` that never moves anybody.
* **SCORE-3** — "re-entering an eaten square scores nothing" is green against
  one that never scores.

So every test of either also exercises, against the same state, the case that
**must** change: the wall tests move the other way and check it worked, and the
re-entry test checks the first entry scored before checking the second did not.
A do-nothing implementation fails them rather than passing them.
"""

from __future__ import annotations

import os
import random
import unittest

from terminalgame.domain.game_state import GameState, Outcome, new_game
from terminalgame.domain.maze import (
    DIRECTIONS,
    EAST,
    NORTH,
    SOUTH,
    WEST,
    Maze,
)
from terminalgame.domain.player import NotADirection, move_player
from tests.test_layering import domain_files

#: A maze with a wall in the middle, so that (2, 1) has wall to the north and
#: to the south and corridor to the east and to the west. That one square is
#: where most of the CTRL-3 work happens: from it, two presses must do nothing
#: and two must do something.
#
#    01234
#  0 #####
#  1 #   #
#  2 # # #
#  3 #   #
#  4 #####
RING = [
    "#####",
    "#   #",
    "# # #",
    "#   #",
    "#####",
]


def ring_maze():
    return Maze.from_text("\n".join(RING))


def state_on_ring(player=(2, 1), dots=None, score=0,
                  ghost=(2, 3), heading=EAST, outcome=Outcome.PLAYING):
    """A game on the ring maze, with exactly the dots asked for.

    Built directly rather than through `new_game`, so each test says what it
    depends on instead of inheriting a whole opening position.
    """
    maze = ring_maze()
    if dots is None:
        dots = set(maze.corridor_squares()) - {player}
    return GameState(maze=maze, player=player, ghost=ghost,
                     ghost_heading=heading, dots=dots, score=score,
                     outcome=outcome)


class OneSquarePerPress(unittest.TestCase):
    """CTRL-1 and CTRL-2."""

    def test_each_of_the_four_directions_moves_that_way(self):
        # From the middle of the ring's top corridor, east and west are open;
        # from the middle of its left corridor, north and south are.
        self.assertEqual((3, 1), move_player(state_on_ring((2, 1)), EAST).player)
        self.assertEqual((1, 1), move_player(state_on_ring((2, 1)), WEST).player)
        self.assertEqual((1, 1), move_player(state_on_ring((1, 2)), NORTH).player)
        self.assertEqual((1, 3), move_player(state_on_ring((1, 2)), SOUTH).player)

    def test_north_is_upwards_on_the_screen(self):
        """y counts down from the top, so north is y - 1.

        Pinned because it is the one thing in this coordinate system that is
        easy to get backwards and impossible to notice later — DEV-B flagged it
        out of WI-4 for exactly that reason.
        """
        before = state_on_ring((1, 2))
        self.assertEqual(before.player[1] - 1, move_player(before, NORTH).player[1])
        self.assertEqual(before.player[1] + 1, move_player(before, SOUTH).player[1])

    def test_a_move_is_exactly_one_square(self):
        for direction in DIRECTIONS:
            before = state_on_ring((2, 1))
            after = move_player(before, direction)
            steps = (abs(after.player[0] - before.player[0])
                     + abs(after.player[1] - before.player[1]))
            self.assertIn(steps, (0, 1),
                          "%s moved %d squares" % (direction.name, steps))

    def test_the_state_carries_nothing_that_could_make_the_player_drift(self):
        """CTRL-2 — "the player never drifts on their own".

        A structural argument rather than a behavioural one, and it is the
        honest form of this requirement: drift would need somewhere to live,
        and there is nowhere. The player has a square and no velocity and no
        heading of their own — `ghost_heading` belongs to the ghost, and the
        exact name `heading` is absent. The behavioural half of CTRL-2 is
        `test_moving_twice_covers_two_squares_and_not_more`.
        """
        self.assertIn("player", GameState.FIELDS)
        self.assertNotIn("velocity", GameState.FIELDS)
        self.assertNotIn("momentum", GameState.FIELDS)
        self.assertNotIn("heading", GameState.FIELDS)
        self.assertNotIn("player_heading", GameState.FIELDS)

    def test_moving_twice_covers_two_squares_and_not_more(self):
        state = state_on_ring((1, 1))
        state = move_player(state, EAST)
        self.assertEqual((2, 1), state.player)
        state = move_player(state, EAST)
        self.assertEqual((3, 1), state.player)

    def test_anything_that_is_not_one_of_the_four_is_refused(self):
        with self.assertRaises(NotADirection):
            move_player(state_on_ring(), "north")
        with self.assertRaises(NotADirection):
            move_player(state_on_ring(), None)


class APressTowardsAWall(unittest.TestCase):
    """CTRL-3 — "does nothing at all", which is stronger than "does not move".

    Every test here also moves a way that is open, so that a `move_player`
    which did nothing ever would fail rather than pass.
    """

    def test_the_state_that_comes_back_is_the_very_same_state(self):
        before = state_on_ring((2, 1))
        self.assertIs(before, move_player(before, NORTH))
        self.assertIs(before, move_player(before, SOUTH))
        # ... and the same function does move when the way is open.
        self.assertIsNot(before, move_player(before, EAST))

    def test_not_the_score_and_not_the_dots_and_not_the_outcome(self):
        # The player stands beside a wall with a dot on the far side of it, so
        # a move that half-happened would show up as a score.
        before = state_on_ring((2, 1), dots={(2, 2), (3, 1)}, score=7)
        blocked = move_player(before, NORTH)   # (2, 2) is wall
        for field in GameState.FIELDS:
            self.assertEqual(getattr(before, field), getattr(blocked, field),
                             "%s changed on a move into a wall" % field)
        # The same state, the same dots, moved the other way: this one counts.
        allowed = move_player(before, EAST)    # (3, 1) is corridor and dotted
        self.assertEqual(8, allowed.score)
        self.assertEqual((3, 1), allowed.player)

    def test_a_wall_with_a_dot_drawn_on_it_is_still_a_wall(self):
        # Nothing should ever put a dot on a wall, but if something did, the
        # wall check has to come first or the player would score through it.
        before = state_on_ring((2, 1), dots={(2, 2)}, score=0)
        self.assertIs(before, move_player(before, NORTH))
        self.assertEqual(0, move_player(before, NORTH).score)

    def test_the_outer_border_stops_the_player_on_every_side(self):
        # Anything off the grid reads as wall, so the ring needs no special
        # case — but the player must not walk off the edge either.
        self.assertIs(*self._blocked((1, 1), NORTH))
        self.assertIs(*self._blocked((1, 1), WEST))
        self.assertIs(*self._blocked((3, 3), SOUTH))
        self.assertIs(*self._blocked((3, 3), EAST))

    def _blocked(self, square, direction):
        before = state_on_ring(square)
        return before, move_player(before, direction)

    def test_a_blocked_move_does_not_stop_a_later_one_working(self):
        state = state_on_ring((2, 1))
        state = move_player(state, NORTH)      # nothing
        state = move_player(state, EAST)       # something
        self.assertEqual((3, 1), state.player)


class EatingADot(unittest.TestCase):
    """SCORE-1 and SCORE-2."""

    def test_stepping_onto_a_dot_takes_it_and_scores_one(self):
        before = state_on_ring((2, 1), dots={(3, 1)}, score=0)
        after = move_player(before, EAST)
        self.assertEqual(1, after.score)
        self.assertFalse(after.dot_at((3, 1)))
        self.assertEqual(0, after.dots_remaining)

    def test_the_dot_is_gone_for_the_rest_of_the_game(self):
        state = state_on_ring((2, 1), dots={(3, 1)}, score=0)
        state = move_player(state, EAST)       # eats (3, 1)
        for direction in (SOUTH, NORTH, WEST, EAST):
            state = move_player(state, direction)
            self.assertFalse(state.dot_at((3, 1)),
                             "the dot came back after moving %s" % direction.name)

    def test_exactly_one_point_per_dot_and_exactly_one_dot_removed(self):
        before = state_on_ring((1, 1), dots={(2, 1), (3, 1)}, score=0)
        after = move_player(before, EAST)
        self.assertEqual(before.score + 1, after.score)
        self.assertEqual(before.dots - {(2, 1)}, after.dots)

    def test_a_dot_under_the_ghost_is_still_there_to_be_taken(self):
        """SCORE-4's other half, from the player's side.

        The ghost does not hide a dot, so walking onto the ghost's square eats
        the dot that is on it. Whether that move also ends the game is WI-10's
        question, not this one's — here it must simply score.
        """
        before = state_on_ring((2, 1), dots={(3, 1)}, score=0, ghost=(3, 1))
        after = move_player(before, EAST)
        self.assertEqual(1, after.score)
        self.assertEqual((3, 1), after.player)
        self.assertEqual(after.player, after.ghost)

    def test_stepping_onto_an_empty_square_scores_nothing(self):
        before = state_on_ring((2, 1), dots=set(), score=4)
        after = move_player(before, EAST)
        self.assertEqual(4, after.score)
        self.assertEqual((3, 1), after.player)


class ComingBackToASquareAlreadyEaten(unittest.TestCase):
    """SCORE-3, tested so that "it never scores" would fail it."""

    def test_the_first_visit_scores_and_the_second_does_not(self):
        state = state_on_ring((2, 1), dots={(3, 1)}, score=0)

        state = move_player(state, EAST)       # onto (3, 1), which has a dot
        self.assertEqual(1, state.score, "the first visit did not score")

        state = move_player(state, WEST)       # back to (2, 1)
        state = move_player(state, EAST)       # onto (3, 1) again, now empty
        self.assertEqual(1, state.score, "the second visit scored again")

    def test_walking_the_whole_ring_twice_scores_only_the_first_lap(self):
        maze = ring_maze()
        lap = [EAST, EAST, SOUTH, SOUTH, WEST, WEST, NORTH, NORTH]
        state = state_on_ring((1, 1))
        dots_at_the_start = state.dots_remaining

        for direction in lap:
            state = move_player(state, direction)
        after_one_lap = state.score
        self.assertEqual(dots_at_the_start, after_one_lap,
                         "one lap should have eaten every dot on the ring")

        for direction in lap:
            state = move_player(state, direction)
        self.assertEqual(after_one_lap, state.score)
        self.assertEqual(0, state.dots_remaining)
        self.assertEqual((1, 1), state.player)


class TheScoreNeverGoesDown(unittest.TestCase):
    """SCORE-5, over a long random walk on real generated mazes."""

    def test_over_a_thousand_moves_it_only_ever_rises(self):
        for seed in range(6):
            state = new_game(seed)
            walker = random.Random(seed)
            for _ in range(1000):
                before = state
                state = move_player(state, walker.choice(DIRECTIONS))
                self.assertGreaterEqual(state.score, before.score)
                self.assertGreaterEqual(before.dots_remaining,
                                        state.dots_remaining)

    def test_the_score_is_the_number_of_distinct_dotted_squares_entered(self):
        """The plan's own wording for WI-8, checked directly.

        The bookkeeping is done independently of the state: `eaten` is built
        from what the walk saw, not from what `move_player` reported.
        """
        for seed in range(6):
            state = new_game(seed)
            dotted_at_the_start = set(state.dots)
            walker = random.Random(seed + 100)
            eaten = set()
            for _ in range(1500):
                direction = walker.choice(DIRECTIONS)
                after = move_player(state, direction)
                if after.player in dotted_at_the_start:
                    eaten.add(after.player)
                state = after
            self.assertEqual(len(eaten), state.score)
            self.assertEqual(dotted_at_the_start - eaten, set(state.dots))

    def test_a_walk_leaves_the_player_on_corridor_and_the_dots_on_corridor(self):
        state = new_game(3)
        walker = random.Random(3)
        for _ in range(500):
            state = move_player(state, walker.choice(DIRECTIONS))
            self.assertTrue(state.maze.is_corridor(*state.player))
        for square in state.dots:
            self.assertTrue(state.maze.is_corridor(*square))


class WhatAMoveIsNotAllowedToTouch(unittest.TestCase):
    """The boundary with WI-9 and WI-10, kept by test rather than by agreement.

    WI-8 owns the player's square, the dots and the score. The ghost is DEV-B's
    and the outcome is WI-10's, and a move must leave both exactly as it found
    them.
    """

    def test_a_move_never_moves_the_ghost_or_turns_it(self):
        before = state_on_ring((2, 1), ghost=(1, 3), heading=NORTH)
        for direction in (EAST, WEST, NORTH, SOUTH):
            after = move_player(before, direction)
            self.assertEqual((1, 3), after.ghost)
            self.assertIs(NORTH, after.ghost_heading)

    def test_a_move_never_decides_the_outcome(self):
        # Walking onto the ghost is a legal move that leaves the outcome alone;
        # reading a loss out of that state is WI-10's, and it runs afterwards.
        before = state_on_ring((2, 1), ghost=(3, 1))
        after = move_player(before, EAST)
        self.assertEqual(Outcome.PLAYING, after.outcome)
        self.assertEqual(after.ghost, after.player)

    def test_taking_the_last_dot_does_not_itself_win_the_game(self):
        before = state_on_ring((2, 1), dots={(3, 1)})
        after = move_player(before, EAST)
        self.assertEqual(0, after.dots_remaining)
        self.assertEqual(Outcome.PLAYING, after.outcome)

    def test_a_move_never_changes_the_maze(self):
        before = state_on_ring((2, 1))
        after = move_player(before, EAST)
        self.assertIs(before.maze, after.maze)

    def test_the_state_handed_in_is_never_modified(self):
        before = state_on_ring((2, 1), dots={(3, 1)}, score=0)
        snapshot = {field: getattr(before, field) for field in GameState.FIELDS}
        move_player(before, EAST)
        for field, value in snapshot.items():
            self.assertEqual(value, getattr(before, field),
                             "%s was modified in place" % field)


class TheModuleSitsInTheDomain(unittest.TestCase):
    """The layering guard, without editing the shared file.

    `tests/test_layering.py` sweeps every file under `terminalgame/domain/`,
    so this module is already covered by its purity, dependency and
    screen-geometry scans. What that file also does is name each module
    explicitly, so that moving one cannot leave the scans quietly checking
    less than they claim. That assertion is made here rather than there
    because DEV-B is adding WI-9 to the same list at the same time, and an
    adjacent-line edit to one shared file is a conflict neither of us needs.
    """

    def test_the_layering_scan_really_does_look_at_this_module(self):
        names = [name for name, _ in domain_files()]
        self.assertIn(os.path.join("domain", "player.py"), names)


if __name__ == "__main__":
    unittest.main()
