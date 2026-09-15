"""WIN-4: a little below and to the right, and always somewhere visible."""

import unittest

from launcher.geometry import (
    DEFAULT_OFFSET,
    Offset,
    Point,
    Rect,
    Size,
    target_position,
)

# The window this launcher actually produces, measured on the development
# machine: 40 columns by 30 rows of Menlo 14 came out 357 by 558 points.
GAME_SIZE = Size(357, 558)

# A generously large single screen, used where the clamp is not the point.
BIG_SCREEN = Rect(0, 0, 3000, 2000)


class TheOffset(unittest.TestCase):
    def test_the_window_sits_down_and_right_of_the_reference_window(self):
        reference = Rect(400, 300, 1000, 800)
        position = target_position(reference, GAME_SIZE, BIG_SCREEN, Offset(32, 32))
        self.assertEqual(Point(432, 332), position)

    def test_the_default_offset_is_small_and_moves_both_ways(self):
        # Assumption A4 leaves the number to the implementer; what WIN-4 fixes
        # is that it is positive in both axes and modest.
        self.assertGreater(DEFAULT_OFFSET.dx, 0)
        self.assertGreater(DEFAULT_OFFSET.dy, 0)
        self.assertLessEqual(DEFAULT_OFFSET.dx, 64)
        self.assertLessEqual(DEFAULT_OFFSET.dy, 64)

    def test_a_reference_window_on_a_display_left_of_the_main_one_stays_there(self):
        # Measured on the development machine: a terminal window reported its
        # position as (-879, 84). A clamp that assumed coordinates start at zero
        # would throw the game window onto a different screen.
        screen = Rect(-3509, -1440, 1611, 982)
        reference = Rect(-879, 84, -282, 469)
        position = target_position(reference, GAME_SIZE, screen, Offset(32, 32))
        self.assertEqual(Point(-847, 116), position)


class TheClamp(unittest.TestCase):
    def test_a_reference_window_at_the_bottom_right_is_pulled_back_on_screen(self):
        # Note where this lands: outside the reference window's own frame. That
        # is the documented precedence, not an oversight -- see
        # `test_the_screen_clamp_beats_the_reference_frame_when_they_conflict`.
        screen = Rect(0, 0, 1440, 900)
        reference = Rect(1300, 800, 1440, 900)
        position = target_position(reference, GAME_SIZE, screen, Offset(32, 32))
        self.assertEqual(Point(1440 - GAME_SIZE.width, 900 - GAME_SIZE.height), position)
        self.assertTrue(screen.contains_point(position))

    def test_the_whole_window_fits_on_the_screen_when_it_is_pulled_back(self):
        screen = Rect(0, 0, 1440, 900)
        reference = Rect(1300, 800, 1440, 900)
        position = target_position(reference, GAME_SIZE, screen, Offset(32, 32))
        landed = Rect.from_origin_and_size(position, GAME_SIZE)
        self.assertGreaterEqual(landed.left, screen.left)
        self.assertGreaterEqual(landed.top, screen.top)
        self.assertLessEqual(landed.right, screen.right)
        self.assertLessEqual(landed.bottom, screen.bottom)

    def test_a_window_larger_than_the_screen_is_pinned_to_its_top_left(self):
        # Not off the top or the left, where the title bar would be out of reach.
        screen = Rect(0, 0, 200, 200)
        reference = Rect(50, 50, 150, 150)
        position = target_position(reference, GAME_SIZE, screen, Offset(32, 32))
        self.assertEqual(Point(0, 0), position)

    def test_the_offset_stays_inside_the_reference_frame_where_it_can(self):
        # A preference, not a guarantee -- see the precedence test below. The
        # reference window is the one the player was looking at, so a point
        # inside it is a point on a real display, and that is worth having
        # wherever the screen clamp does not overrule it. Here the screen is
        # enormous, so nothing overrules it.
        screen = Rect(-3509, -1440, 1611, 982)
        reference = Rect(100, 100, 110, 108)  # ten points wide, eight deep
        position = target_position(reference, GAME_SIZE, screen, Offset(32, 32))
        self.assertEqual(Point(109, 107), position)
        self.assertTrue(reference.contains_point(position))

    def test_the_screen_clamp_beats_the_reference_frame_when_they_conflict(self):
        """Which of the two rules wins, pinned rather than left to emerge.

        They conflict when the reference window is near an edge and the game
        window is large next to the room that is left. Rule 3 is applied last,
        so rule 3 holds: the window comes back onto the screen even though that
        carries its corner out of the frame it was meant to sit inside. Ruled
        this way deliberately; `target_position` says why, and says what it
        costs.
        """
        screen = Rect(0, 0, 1440, 900)
        reference = Rect(1300, 800, 1440, 900)
        position = target_position(reference, GAME_SIZE, screen, Offset(32, 32))

        # The screen clamp got its way...
        self.assertTrue(screen.contains_point(position))
        landed = Rect.from_origin_and_size(position, GAME_SIZE)
        self.assertLessEqual(landed.right, screen.right)
        self.assertLessEqual(landed.bottom, screen.bottom)

        # ...and the frame preference did not. 217 points to the LEFT of a
        # window it was asked to sit below and to the right of.
        self.assertFalse(reference.contains_point(position))
        self.assertLess(position.x, reference.left)

    def test_a_reference_window_with_no_area_still_yields_its_own_corner(self):
        reference = Rect(500, 400, 500, 400)
        position = target_position(reference, GAME_SIZE, BIG_SCREEN, Offset(32, 32))
        self.assertEqual(Point(500, 400), position)


class RectArithmetic(unittest.TestCase):
    def test_width_and_height_come_from_the_edges(self):
        rect = Rect(10, 20, 110, 220)
        self.assertEqual(100, rect.width)
        self.assertEqual(200, rect.height)
        self.assertEqual(Size(100, 200), rect.size)
        self.assertEqual(Point(10, 20), rect.origin)

    def test_from_origin_and_size_is_the_inverse(self):
        rect = Rect.from_origin_and_size(Point(-879, 84), Size(357, 558))
        self.assertEqual(Rect(-879, 84, -522, 642), rect)

    def test_the_right_and_bottom_edges_are_outside_the_rectangle(self):
        rect = Rect(0, 0, 10, 10)
        self.assertTrue(rect.contains_point(Point(9, 9)))
        self.assertFalse(rect.contains_point(Point(10, 9)))
        self.assertFalse(rect.contains_point(Point(9, 10)))


if __name__ == "__main__":
    unittest.main()
