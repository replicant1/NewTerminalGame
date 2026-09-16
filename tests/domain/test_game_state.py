"""The vocabulary a game is carried in (WI-6): score, outcome, game state."""

import unittest

from terminal_game.domain.dot_field import DotField
from terminal_game.domain.game_state import GameState, Outcome, Score
from terminal_game.domain.maze import Maze, Square

RING = Maze.from_text(
    """
#####
#...#
#.#.#
#...#
#####
"""
)


def a_state(**changes):
    """A perfectly ordinary game state, with anything named here changed."""
    fields = dict(
        maze=RING,
        dots=DotField.over_corridors_except(RING, Square(1, 1)),
        player=Square(1, 1),
        ghost=Square(3, 3),
        score=Score.zero(),
        outcome=Outcome.UNDECIDED,
    )
    fields.update(changes)
    return GameState(**fields)


class ScoreTests(unittest.TestCase):
    def test_a_game_starts_at_zero(self):
        self.assertEqual(0, Score.zero().points)

    def test_one_dot_adds_exactly_one_point(self):
        self.assertEqual(1, Score.zero().plus_one().points)
        self.assertEqual(4, Score(3).plus_one().points)

    def test_scoring_leaves_the_score_it_came_from_alone(self):
        before = Score(7)
        before.plus_one()
        self.assertEqual(7, before.points)

    def test_a_negative_score_cannot_be_made_at_all(self):
        with self.assertRaises(ValueError):
            Score(-1)

    def test_a_score_is_a_whole_number_of_points(self):
        with self.assertRaises(TypeError):
            Score(1.5)
        with self.assertRaises(TypeError):
            Score("3")
        with self.assertRaises(TypeError):
            Score(True)

    def test_scores_of_equal_points_are_the_same_value(self):
        self.assertEqual(Score(3), Score(3))
        self.assertEqual(hash(Score(3)), hash(Score(3)))
        self.assertNotEqual(Score(3), Score(4))
        self.assertNotEqual(Score(3), 3)

    def test_the_score_cannot_be_written_to(self):
        score = Score(3)
        with self.assertRaises(AttributeError):
            score.points = 99
        with self.assertRaises(AttributeError):
            score.anything_else = 99

    def test_a_score_offers_nothing_that_could_lower_it(self):
        # SCORE-5 says the score never goes down. This is a guard on the
        # shape of the class, not a duplicate of the behaviour tests above:
        # it is what notices if somebody later adds a setter, a reset or a
        # subtraction, which is the only way SCORE-5 could be broken.
        offered = {name for name in dir(Score) if not name.startswith("_")}
        self.assertEqual({"points", "zero", "plus_one"}, offered)

    def test_every_operation_a_score_offers_leaves_it_no_smaller(self):
        for points in (0, 1, 7, 274):
            score = Score(points)
            self.assertGreaterEqual(score.plus_one().points, score.points)
            self.assertGreaterEqual(Score.zero().points, 0)


class OutcomeTests(unittest.TestCase):
    def test_there_are_two_endings_and_the_state_of_not_having_ended(self):
        self.assertEqual(
            {Outcome.UNDECIDED, Outcome.CAUGHT, Outcome.CLEARED}, set(Outcome)
        )

    def test_only_the_two_endings_count_as_decided(self):
        self.assertFalse(Outcome.UNDECIDED.is_decided)
        self.assertTrue(Outcome.CAUGHT.is_decided)
        self.assertTrue(Outcome.CLEARED.is_decided)


class GameStateTests(unittest.TestCase):
    def test_a_state_carries_the_maze_the_dots_the_actors_and_the_score(self):
        state = a_state()
        self.assertEqual(RING, state.maze)
        self.assertEqual(Square(1, 1), state.player)
        self.assertEqual(Square(3, 3), state.ghost)
        self.assertEqual(Score.zero(), state.score)
        self.assertEqual(Outcome.UNDECIDED, state.outcome)

    def test_a_game_is_over_only_once_an_ending_has_happened(self):
        self.assertFalse(a_state().is_over)
        self.assertTrue(a_state(outcome=Outcome.CAUGHT).is_over)
        self.assertTrue(a_state(outcome=Outcome.CLEARED).is_over)

    def test_the_actors_share_a_square_only_when_they_stand_on_one(self):
        self.assertFalse(a_state().actors_share_a_square)
        self.assertTrue(a_state(ghost=Square(1, 1)).actors_share_a_square)

    def test_two_states_built_the_same_way_are_the_same_value(self):
        self.assertEqual(a_state(), a_state())

    def test_states_differing_in_one_field_are_different_values(self):
        self.assertNotEqual(a_state(), a_state(player=Square(3, 1)))
        self.assertNotEqual(a_state(), a_state(score=Score(1)))
        self.assertNotEqual(a_state(), a_state(outcome=Outcome.CAUGHT))

    def test_a_state_cannot_be_written_to(self):
        state = a_state()
        with self.assertRaises(AttributeError):
            state.player = Square(3, 1)

    def test_moving_the_player_changes_that_and_nothing_else(self):
        before = a_state()
        after = before.with_player_at(Square(3, 1))
        self.assertEqual(Square(3, 1), after.player)
        self.assertEqual(before, after.with_player_at(before.player))

    def test_moving_the_ghost_changes_that_and_nothing_else(self):
        before = a_state()
        after = before.with_ghost_at(Square(1, 3))
        self.assertEqual(Square(1, 3), after.ghost)
        self.assertEqual(before, after.with_ghost_at(before.ghost))

    def test_taking_a_dot_scoring_and_ending_each_change_one_thing(self):
        before = a_state()
        fewer = before.dots.without_dot_at(Square(2, 1))

        self.assertEqual(fewer, before.with_dots(fewer).dots)
        self.assertEqual(before, before.with_dots(fewer).with_dots(before.dots))

        self.assertEqual(Score(1), before.with_score(Score(1)).score)
        self.assertEqual(before, before.with_score(Score(1)).with_score(before.score))

        caught = before.with_outcome(Outcome.CAUGHT)
        self.assertEqual(Outcome.CAUGHT, caught.outcome)
        self.assertEqual(before, caught.with_outcome(before.outcome))

    def test_the_state_changed_from_is_itself_left_alone(self):
        before = a_state()
        before.with_player_at(Square(3, 1)).with_score(Score(9)).with_outcome(
            Outcome.CLEARED
        )
        self.assertEqual(a_state(), before)


if __name__ == "__main__":
    unittest.main()
