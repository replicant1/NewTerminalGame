"""The M0 placeholder picture and the way it is written out.

None of this survives WI-3 and WI-9, which land the real maze. What is worth
asserting now is the two things that would otherwise be found on a screen: that
the picture is exactly the size of the window, and that painting it never
touches the bottom-right cell (ARCHITECTURE.md C1).
"""

import io
import unittest

from termgame import loop


class PlaceholderScreenTest(unittest.TestCase):
    def test_the_picture_is_exactly_the_size_of_the_window(self):
        lines = loop.placeholder_screen()
        self.assertEqual(30, len(lines))
        for line in lines:
            self.assertEqual(40, len(line))

    def test_an_odd_size_is_still_filled_exactly(self):
        lines = loop.placeholder_screen(columns=13, rows=5)
        self.assertEqual(5, len(lines))
        for line in lines:
            self.assertEqual(13, len(line))

    def test_the_player_is_told_how_to_leave(self):
        text = "\n".join(loop.placeholder_screen())
        self.assertIn("press q to quit", text)

    def test_the_size_label_is_shown_so_a_human_can_check_win_2(self):
        text = "\n".join(loop.placeholder_screen(size_label="40 columns x 30 rows"))
        self.assertIn("40 columns x 30 rows", text)

    def test_a_label_too_wide_for_the_window_is_cut_not_wrapped(self):
        lines = loop.placeholder_screen(size_label="x" * 200)
        for line in lines:
            self.assertEqual(40, len(line))


class PaintTest(unittest.TestCase):
    def test_the_bottom_right_cell_is_never_written(self):
        # C1: a write to the last cell of the last row scrolls a plain
        # terminal, and raises addwstr() ERR under curses.
        stream = io.StringIO()
        loop.paint(loop.placeholder_screen(), stream=stream)
        written = stream.getvalue()
        last_row = written.split("\033[30;1H")[-1]
        self.assertEqual(39, len(last_row))

    def test_every_row_is_addressed_absolutely_so_nothing_scrolls(self):
        stream = io.StringIO()
        loop.paint(loop.placeholder_screen(), stream=stream)
        written = stream.getvalue()
        for row in range(1, 31):
            self.assertIn("\033[%d;1H" % row, written)
        self.assertNotIn("\n", written)

    def test_the_screen_is_cleared_and_the_cursor_hidden_first(self):
        stream = io.StringIO()
        loop.paint(["ab", "cd"], stream=stream)
        self.assertTrue(stream.getvalue().startswith("\033[2J\033[H\033[?25l"))


class QuitTest(unittest.TestCase):
    """END-6, and rule 4 of plan section 2.6."""

    class NotATerminal(object):
        def fileno(self):
            raise ValueError("I/O operation on closed file")

    def test_it_returns_at_once_when_there_is_no_terminal_to_read_from(self):
        self.assertEqual(0, loop.wait_for_quit(stream=self.NotATerminal()))


if __name__ == "__main__":
    unittest.main()
