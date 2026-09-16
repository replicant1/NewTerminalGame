"""The dots along the corridors (WI-6): START-3, SCORE-1, SCORE-3."""

import unittest

from terminal_game.domain.dot_field import DotField
from terminal_game.domain.maze import Maze, Square

# The ring maze again: eight corridor squares around one lone wall.
RING = Maze.from_text(
    """
#####
#...#
#.#.#
#...#
#####
"""
)


class LayingTheDotsOutTests(unittest.TestCase):
    def test_every_corridor_square_but_the_players_holds_a_dot(self):
        field = DotField.over_corridors_except(RING, Square(1, 1))
        self.assertEqual(len(RING.corridor_squares()) - 1, field.remaining)
        self.assertFalse(field.has_dot(Square(1, 1)))
        for square in RING.corridor_squares():
            if square != Square(1, 1):
                self.assertTrue(field.has_dot(square), "%r has no dot" % (square,))

    def test_no_dot_ever_sits_on_a_wall_square(self):
        field = DotField.over_corridors_except(RING, Square(1, 1))
        for square in RING.squares():
            if RING.is_wall(square):
                self.assertFalse(field.has_dot(square), "%r has a dot" % (square,))

    def test_the_empty_square_must_be_a_corridor_square(self):
        with self.assertRaises(ValueError):
            DotField.over_corridors_except(RING, Square(2, 2))
        with self.assertRaises(ValueError):
            DotField.over_corridors_except(RING, Square(0, 0))

    def test_a_dot_must_sit_on_a_square(self):
        with self.assertRaises(ValueError):
            DotField([(1, 1)])


class TakingADotTests(unittest.TestCase):
    def setUp(self):
        self.field = DotField.over_corridors_except(RING, Square(1, 1))

    def test_taking_a_dot_leaves_none_behind_on_that_square(self):
        after = self.field.without_dot_at(Square(2, 1))
        self.assertFalse(after.has_dot(Square(2, 1)))
        self.assertEqual(self.field.remaining - 1, after.remaining)

    def test_the_field_taken_from_is_itself_unchanged(self):
        before = self.field.remaining
        self.field.without_dot_at(Square(2, 1))
        self.assertTrue(self.field.has_dot(Square(2, 1)))
        self.assertEqual(before, self.field.remaining)

    def test_taking_a_dot_twice_takes_one_dot(self):
        once = self.field.without_dot_at(Square(2, 1))
        twice = once.without_dot_at(Square(2, 1))
        self.assertEqual(once, twice)
        self.assertEqual(self.field.remaining - 1, twice.remaining)

    def test_a_square_whose_dot_has_gone_reports_no_dot(self):
        after = self.field.without_dot_at(Square(2, 1))
        self.assertFalse(after.has_dot(Square(2, 1)))

    def test_taking_from_a_square_that_never_had_one_changes_nothing(self):
        self.assertIs(self.field, self.field.without_dot_at(Square(1, 1)))
        self.assertIs(self.field, self.field.without_dot_at(Square(2, 2)))

    def test_taking_every_dot_empties_the_field(self):
        field = self.field
        self.assertFalse(field.is_empty)
        for square in sorted(field.squares()):
            field = field.without_dot_at(square)
        self.assertTrue(field.is_empty)
        self.assertEqual(0, field.remaining)


class DotFieldValueTests(unittest.TestCase):
    def test_two_fields_over_the_same_squares_are_the_same_value(self):
        one = DotField([Square(1, 1), Square(2, 1)])
        another = DotField([Square(2, 1), Square(1, 1)])
        self.assertEqual(one, another)
        self.assertEqual(hash(one), hash(another))
        self.assertEqual(1, len({one, another}))

    def test_fields_differing_by_one_dot_are_different_values(self):
        one = DotField([Square(1, 1), Square(2, 1)])
        another = DotField([Square(1, 1)])
        self.assertNotEqual(one, another)

    def test_a_field_is_not_equal_to_a_set_of_the_same_squares(self):
        self.assertNotEqual(DotField([Square(1, 1)]), {Square(1, 1)})


if __name__ == "__main__":
    unittest.main()
