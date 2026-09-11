"""WIN-4: where the game window goes, and which window it is offset from.

Both decisions are pure functions of what the AppleScript queries returned, so
they are tested here directly and no window is opened.
"""

import unittest

from termgame import window


class OffsetArithmeticTest(unittest.TestCase):
    """The offset is a pure function of the reference position."""

    SCREEN = (1512, 982)  # measured on this machine

    def test_offset_is_thirty_down_and_thirty_right(self):
        self.assertEqual(
            (130, 230),
            window.offset_position((100, 200), screen_size=self.SCREEN),
        )

    def test_a_reference_at_the_bottom_right_still_lands_fully_on_screen(self):
        # The whole point of WIN-4: "so it always lands somewhere visible".
        # A naive +30 from here would put the window 480 px off the right edge
        # and 675 px off the bottom.
        placed = window.offset_position((1480, 950), screen_size=self.SCREEN)
        width, height = window.GAME_WINDOW_PIXELS
        self.assertEqual((1512 - 477, 982 - 707), placed)
        self.assertLessEqual(placed[0] + width, self.SCREEN[0])
        self.assertLessEqual(placed[1] + height, self.SCREEN[1])

    def test_the_naive_offset_from_the_bottom_right_would_not_fit(self):
        # Pins that the previous test is testing the clamp and not an accident
        # of the numbers.
        width, height = window.GAME_WINDOW_PIXELS
        self.assertGreater(1480 + 30 + width, self.SCREEN[0])
        self.assertGreater(950 + 30 + height, self.SCREEN[1])

    def test_a_reference_at_the_top_left_is_pushed_below_the_menu_bar(self):
        placed = window.offset_position((0, 0), screen_size=self.SCREEN)
        self.assertEqual(30, placed[0])
        self.assertGreaterEqual(placed[1], window.MENU_BAR_HEIGHT)

    def test_a_negative_reference_never_yields_a_negative_coordinate(self):
        placed = window.offset_position((-500, -500), screen_size=self.SCREEN)
        self.assertEqual((0, window.MENU_BAR_HEIGHT), placed)

    def test_a_screen_smaller_than_the_window_still_yields_the_top_left(self):
        placed = window.offset_position((400, 400), screen_size=(400, 400))
        self.assertEqual((0, window.MENU_BAR_HEIGHT), placed)

    def test_coordinates_are_integers_applescript_can_take(self):
        placed = window.offset_position((10.0, 20.0), screen_size=self.SCREEN)
        self.assertIsInstance(placed[0], int)
        self.assertIsInstance(placed[1], int)


class FallbackChainTest(unittest.TestCase):
    """Reference found / not found but a front window exists / neither."""

    def test_the_window_with_our_tty_wins(self):
        self.assertEqual(
            ((11, 22), "tty"),
            window.choose_reference((11, 22), (33, 44)),
        )

    def test_the_front_window_is_used_when_no_tab_has_our_tty(self):
        self.assertEqual(
            ((33, 44), "front"),
            window.choose_reference(None, (33, 44)),
        )

    def test_a_fixed_position_is_used_when_terminal_has_no_window(self):
        self.assertEqual(
            (window.FALLBACK_POSITION, "fallback"),
            window.choose_reference(None, None),
        )


class QueryParsingTest(unittest.TestCase):
    """What the AppleScript queries hand back, turned into values."""

    def test_a_position_is_two_numbers(self):
        self.assertEqual((12, 34), window.parse_position("12 34"))

    def test_applescript_may_comma_separate_a_point(self):
        self.assertEqual((12, 34), window.parse_position("12, 34"))

    def test_no_such_window_parses_as_no_reference(self):
        self.assertIsNone(window.parse_position("none"))
        self.assertIsNone(window.parse_position(""))
        self.assertIsNone(window.parse_position("  "))

    def test_nonsense_parses_as_no_reference_rather_than_raising(self):
        self.assertIsNone(window.parse_position("no idea"))
        self.assertIsNone(window.parse_position("7"))

    def test_a_tab_state_is_a_busy_flag_and_a_process_count(self):
        self.assertEqual((False, 2), window.parse_tab_state("false 2"))
        self.assertEqual((True, 0), window.parse_tab_state("true 0"))
        self.assertEqual((False, 0), window.parse_tab_state("false 0"))

    def test_an_unreadable_tab_state_is_not_read_as_a_running_game(self):
        # Erring here would leave the window open, never close a live one.
        self.assertEqual((False, 0), window.parse_tab_state(""))
        self.assertEqual((False, 0), window.parse_tab_state("false lots"))

    def test_the_window_census_is_a_list_of_ids(self):
        self.assertEqual([367, 2486], window.parse_window_ids("367\n2486\n"))
        self.assertEqual([367, 2486], window.parse_window_ids("367, 2486"))
        self.assertEqual([], window.parse_window_ids(""))


class ChildCommandTest(unittest.TestCase):
    """What Terminal is asked to run -- WIN-3 depends on every part of it."""

    def test_the_command_execs_the_child_with_no_arguments(self):
        command = window.child_command("/Users/somebody/NewTerminalGame")
        self.assertEqual(
            "exec '/Users/somebody/NewTerminalGame/Terminal Game'", command
        )

    def test_the_child_is_named_exactly_terminal_game(self):
        # C2: the file name *is* the window title. If this constant is ever
        # edited, WIN-3 is gone and only a human would notice.
        self.assertEqual("Terminal Game", window.CHILD_NAME)

    def test_a_path_containing_a_quote_is_still_one_argument(self):
        command = window.child_command("/tmp/it's here")
        self.assertEqual("exec '/tmp/it'\\''s here/Terminal Game'", command)


if __name__ == "__main__":
    unittest.main()
