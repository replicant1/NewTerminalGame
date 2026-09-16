"""The rules of a turn, and the order they are applied in (WI-11).

Requirements: GAME-2, CTRL-1, CTRL-2, CTRL-3, SCORE-1, SCORE-2, SCORE-3,
SCORE-4, END-1, END-2, END-3, END-5.

The mazes here are hand-built and tiny, so that where everything stands can
be read off the fixture. What the ghost's policy decides is WI-7's and is
not re-asserted; what a dot field or a score does is WI-6's and is not
re-asserted either. What is asserted here is the *order*: which rule wins
when two of them would fire in the same turn.
"""

import random
import unittest

from terminal_game.domain.dot_field import DotField
from terminal_game.domain.game_state import GameState, Outcome, Score
from terminal_game.domain.maze import Direction, Maze, Square
from terminal_game.domain.turn_resolver import resolve_move, resolve_tick

# A ring of eight corridor squares around one lone wall at (2, 2).
RING = Maze.from_text(
    """
#####
#...#
#.#.#
#...#
#####
"""
)

# A straight east-west corridor, five squares long.
CORRIDOR = Maze.from_text(
    """
#######
#.....#
#######
"""
)

# A corridor that reaches the left-hand edge of the grid, so that a move
# west from (0, 1) leaves the grid altogether rather than meeting a wall.
OPEN_EDGE = Maze.from_text(
    """
###
..#
###
"""
)


class NeverConsulted:
    """A random source that fails the test if anything draws from it.

    Used where the ghost's move is forced — which, measured in
    ``docs/findings/WI-7-ghost-roaming.md``, is about 95 ticks in 100. If the
    resolver dropped the ghost's heading, the policy would have to choose,
    and choosing would come through here. Without it the test would be a
    coin flip, because a policy choosing blind in a straight corridor
    happens to go the right way half the time.
    """

    def choice(self, sequence):
        raise AssertionError(
            "the ghost's policy was asked to choose where it should have "
            "carried straight on: the resolver did not carry the heading"
        )


def state_on(maze, player, ghost, dots=None, score=0, outcome=Outcome.UNDECIDED,
             ghost_heading=None):
    """A game state with everything said out loud."""
    if dots is None:
        dots = DotField.over_corridors_except(maze, player)
    return GameState(
        maze=maze,
        dots=DotField(dots) if not isinstance(dots, DotField) else dots,
        player=player,
        ghost=ghost,
        score=Score(score),
        outcome=outcome,
        ghost_heading=ghost_heading,
    )


class MovingIntoAWallTests(unittest.TestCase):
    def test_a_press_towards_a_wall_does_nothing_at_all(self):
        # CTRL-3. The whole state is compared, so this covers the square,
        # the score, the dot field, the ghost and the outcome at once.
        before = state_on(RING, player=Square(1, 1), ghost=Square(3, 3))
        self.assertEqual(before, resolve_move(before, Direction.NORTH))
        self.assertEqual(before, resolve_move(before, Direction.WEST))

    def test_a_press_towards_the_lone_wall_in_the_middle_does_nothing(self):
        before = state_on(RING, player=Square(2, 1), ghost=Square(3, 3))
        self.assertEqual(before, resolve_move(before, Direction.SOUTH))

    def test_a_press_off_the_edge_of_the_grid_does_nothing(self):
        before = state_on(OPEN_EDGE, player=Square(0, 1), ghost=Square(1, 1))
        self.assertEqual(before, resolve_move(before, Direction.WEST))


class MovingTests(unittest.TestCase):
    def test_each_arrow_moves_the_player_one_square_that_way(self):
        # CTRL-1 and CTRL-2: one square per press, and no drift, because
        # nothing but an intent ever moves the player.
        start = state_on(RING, player=Square(2, 1), ghost=Square(3, 3))
        self.assertEqual(Square(3, 1), resolve_move(start, Direction.EAST).player)
        self.assertEqual(Square(1, 1), resolve_move(start, Direction.WEST).player)

        from_below = state_on(RING, player=Square(1, 2), ghost=Square(3, 3))
        self.assertEqual(Square(1, 1), resolve_move(from_below, Direction.NORTH).player)
        self.assertEqual(Square(1, 3), resolve_move(from_below, Direction.SOUTH).player)

    def test_the_player_never_moves_more_than_one_square_in_a_turn(self):
        before = state_on(RING, player=Square(1, 1), ghost=Square(3, 3))
        after = resolve_move(before, Direction.EAST)
        self.assertIn(after.player, before.maze.corridor_neighbours(before.player))

    def test_a_move_does_not_shift_the_ghost(self):
        before = state_on(RING, player=Square(1, 1), ghost=Square(3, 3))
        after = resolve_move(before, Direction.EAST)
        self.assertEqual(before.ghost, after.ghost)
        self.assertEqual(before.ghost_heading, after.ghost_heading)


class EatingTests(unittest.TestCase):
    def test_moving_onto_a_dotted_square_eats_it_and_scores_exactly_one(self):
        before = state_on(RING, player=Square(1, 1), ghost=Square(3, 3))
        self.assertTrue(before.dots.has_dot(Square(2, 1)))

        after = resolve_move(before, Direction.EAST)
        self.assertFalse(after.dots.has_dot(Square(2, 1)))
        self.assertEqual(1, after.score.points)
        self.assertEqual(before.dots.remaining - 1, after.dots.remaining)

    def test_moving_onto_a_square_whose_dot_has_gone_scores_nothing(self):
        # SCORE-3, walked rather than contrived: east onto the dot, back
        # west, and east onto the same square again.
        state = state_on(RING, player=Square(1, 1), ghost=Square(3, 3))
        state = resolve_move(state, Direction.EAST)
        self.assertEqual(1, state.score.points)

        state = resolve_move(state, Direction.WEST)
        state = resolve_move(state, Direction.EAST)
        self.assertEqual(Square(2, 1), state.player)
        self.assertEqual(1, state.score.points)

    def test_each_dot_eaten_adds_one_so_the_score_is_the_dots_taken(self):
        state = state_on(RING, player=Square(1, 1), ghost=Square(3, 3))
        for direction in (Direction.EAST, Direction.EAST, Direction.SOUTH):
            state = resolve_move(state, direction)
        self.assertEqual(Square(3, 2), state.player)
        self.assertEqual(3, state.score.points)


class CollisionTests(unittest.TestCase):
    def test_walking_into_the_ghost_loses_the_game(self):
        before = state_on(RING, player=Square(1, 1), ghost=Square(2, 1))
        after = resolve_move(before, Direction.EAST)
        self.assertEqual(Outcome.CAUGHT, after.outcome)
        self.assertTrue(after.is_over)

    def test_the_ghost_walking_into_the_player_loses_the_game(self):
        # END-1's second arm. The ghost is heading east and the player is
        # the square it walks onto.
        before = state_on(
            CORRIDOR,
            player=Square(4, 1),
            ghost=Square(3, 1),
            ghost_heading=Direction.EAST,
        )
        after = resolve_tick(before, NeverConsulted())
        self.assertEqual(Square(4, 1), after.ghost)
        self.assertEqual(Outcome.CAUGHT, after.outcome)


class WinningTests(unittest.TestCase):
    def test_eating_the_last_dot_wins_the_game(self):
        before = state_on(
            RING,
            player=Square(1, 1),
            ghost=Square(3, 3),
            dots=DotField([Square(2, 1)]),
        )
        after = resolve_move(before, Direction.EAST)
        self.assertTrue(after.dots.is_empty)
        self.assertEqual(Outcome.CLEARED, after.outcome)

    def test_eating_a_dot_that_is_not_the_last_wins_nothing(self):
        before = state_on(
            RING,
            player=Square(1, 1),
            ghost=Square(3, 3),
            dots=DotField([Square(2, 1), Square(3, 1)]),
        )
        after = resolve_move(before, Direction.EAST)
        self.assertEqual(Outcome.UNDECIDED, after.outcome)
        self.assertFalse(after.is_over)


class EndThreePrecedenceTests(unittest.TestCase):
    """END-3, asserted directly: the collision is decided before the win."""

    def setUp(self):
        # The one dot left in the whole game is on the square the ghost is
        # standing on, and the player is next to it. Moving east both
        # empties the dot field and puts the two actors on one square, so
        # the winning rule and the losing rule fire in the same turn.
        self.before = state_on(
            RING,
            player=Square(1, 1),
            ghost=Square(2, 1),
            dots=DotField([Square(2, 1)]),
            score=6,
        )

    def test_eating_the_last_dot_on_the_ghosts_square_is_a_loss(self):
        after = resolve_move(self.before, Direction.EAST)
        self.assertEqual(Outcome.CAUGHT, after.outcome)

    def test_the_winning_condition_really_did_hold_in_that_same_turn(self):
        # Without this the test above could pass because the dot field was
        # not actually emptied, which would make it a test about something
        # else entirely.
        after = resolve_move(self.before, Direction.EAST)
        self.assertTrue(after.dots.is_empty)
        self.assertTrue(after.actors_share_a_square)

    def test_the_dot_is_still_eaten_and_still_scores_on_the_losing_turn(self):
        # The step order is move, collision, eat, win — so eating happens
        # after the collision is decided, not instead of it. The player did
        # move onto a square that still had a dot (SCORE-1), so the dot goes
        # and the point counts; only the *ending* is the collision's.
        # A judgement call on the plan's ordering, pinned here so that
        # changing it is a deliberate act. See the PR summary.
        after = resolve_move(self.before, Direction.EAST)
        self.assertEqual(7, after.score.points)
        self.assertEqual(Outcome.CAUGHT, after.outcome)

    def test_an_ending_once_decided_is_not_replaced_by_a_later_one(self):
        # The second thing holding END-3 up, independent of the step order:
        # a game already lost cannot be turned into a win.
        lost = state_on(
            RING,
            player=Square(1, 1),
            ghost=Square(3, 3),
            dots=DotField([Square(2, 1)]),
            outcome=Outcome.CAUGHT,
        )
        self.assertEqual(lost, resolve_move(lost, Direction.EAST))
        self.assertEqual(Outcome.CAUGHT, resolve_move(lost, Direction.EAST).outcome)


class TheGhostsTurnTests(unittest.TestCase):
    def test_a_tick_moves_the_ghost_one_square_along_a_way_on(self):
        before = state_on(RING, player=Square(1, 1), ghost=Square(3, 3))
        after = resolve_tick(before, random.Random(0))
        self.assertIn(after.ghost, before.maze.corridor_neighbours(before.ghost))
        self.assertNotEqual(before.ghost, after.ghost)

    def test_a_tick_leaves_the_player_where_they_are(self):
        before = state_on(RING, player=Square(1, 1), ghost=Square(3, 3))
        after = resolve_tick(before, random.Random(0))
        self.assertEqual(before.player, after.player)

    def test_the_ghost_neither_eats_a_dot_nor_scores_a_point(self):
        # SCORE-4, over five ticks: the whole dot field and the whole score
        # are compared after each one.
        state = state_on(RING, player=Square(1, 1), ghost=Square(3, 3), score=4)
        dots_before = state.dots
        source = random.Random(1)
        walked_over = {state.ghost}

        for _ in range(5):
            state = resolve_tick(state, source)
            walked_over.add(state.ghost)
            self.assertEqual(dots_before, state.dots)
            self.assertEqual(4, state.score.points)

        # And the ghost really did walk over dots, so the test is about
        # SCORE-4 rather than about a ghost that never went anywhere.
        self.assertGreater(len(walked_over), 1)
        self.assertTrue(
            any(dots_before.has_dot(square) for square in walked_over),
            "the ghost never stood on a dot, so nothing was proved",
        )

    def test_the_heading_the_policy_returns_is_carried_to_the_next_tick(self):
        # The seam to WI-7, and the only thing this test owns. The ghost is
        # heading east down a straight corridor, where carrying straight on
        # is forced; a source that raises if consulted turns "the heading
        # was dropped" into a failure rather than a coin flip.
        state = state_on(
            CORRIDOR,
            player=Square(1, 1),
            ghost=Square(2, 1),
            ghost_heading=Direction.EAST,
        )

        state = resolve_tick(state, NeverConsulted())
        self.assertEqual(Square(3, 1), state.ghost)
        self.assertEqual(Direction.EAST, state.ghost_heading)

        state = resolve_tick(state, NeverConsulted())
        self.assertEqual(Square(4, 1), state.ghost)
        self.assertEqual(Direction.EAST, state.ghost_heading)

    def test_a_ghost_that_has_not_moved_yet_has_its_way_chosen_for_it(self):
        # The opening position leaves the heading None. The first tick must
        # therefore ask the policy, and the state must come back with a
        # heading it can carry from then on.
        before = state_on(CORRIDOR, player=Square(1, 1), ghost=Square(3, 1))
        self.assertIsNone(before.ghost_heading)

        after = resolve_tick(before, random.Random(0))
        self.assertIsNotNone(after.ghost_heading)
        self.assertEqual(
            after.ghost, before.ghost.neighbour(after.ghost_heading)
        )


class AFinishedGameTests(unittest.TestCase):
    """END-5: once a game has ended, everything stops."""

    def test_an_arrow_key_after_a_loss_changes_nothing(self):
        over = state_on(
            RING, player=Square(1, 1), ghost=Square(3, 3), outcome=Outcome.CAUGHT
        )
        for direction in Direction:
            self.assertEqual(over, resolve_move(over, direction))

    def test_an_arrow_key_after_a_win_changes_nothing(self):
        over = state_on(
            RING,
            player=Square(1, 1),
            ghost=Square(3, 3),
            dots=DotField([]),
            score=7,
            outcome=Outcome.CLEARED,
        )
        for direction in Direction:
            self.assertEqual(over, resolve_move(over, direction))

    def test_a_tick_after_the_game_has_ended_moves_nothing(self):
        over = state_on(
            RING, player=Square(1, 1), ghost=Square(3, 3), outcome=Outcome.CAUGHT
        )
        self.assertEqual(over, resolve_tick(over, NeverConsulted()))


if __name__ == "__main__":
    unittest.main()
