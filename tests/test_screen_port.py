"""The port on its own: frames, cells, colours and keys. No terminal."""

from __future__ import annotations

import unittest

from terminalgame.screen.port import (
    ALL_COLOURS,
    Cell,
    Colour,
    Frame,
    Key,
    REQUIRED_HEIGHT,
    REQUIRED_WIDTH,
    Screen,
    ScreenTooSmall,
)


class FrameTest(unittest.TestCase):

    def test_a_new_frame_is_the_size_asked_for_and_wholly_blank(self):
        frame = Frame(40, 30)
        self.assertEqual((40, 30), (frame.width, frame.height))
        self.assertEqual([" " * 40] * 30, frame.text_rows())

    def test_putting_a_cell_changes_that_cell_and_leaves_the_rest_alone(self):
        frame = Frame(5, 3)
        frame.put(2, 1, "X", Colour.PLAYER)
        self.assertEqual(Cell("X", Colour.PLAYER), frame.cell(2, 1))
        self.assertEqual(["     ", "  X  ", "     "], frame.text_rows())

    def test_put_text_lays_characters_out_left_to_right_on_one_row(self):
        frame = Frame(8, 2)
        frame.put_text(1, 0, "score 0", Colour.STATUS)
        self.assertEqual([" score 0", "        "], frame.text_rows())
        for column in range(1, 8):
            self.assertEqual(Colour.STATUS, frame.cell(column, 0).colour)

    def test_a_cell_outside_the_frame_is_refused_rather_than_wrapping_round(self):
        frame = Frame(4, 4)
        for column, row in [(-1, 0), (0, -1), (4, 0), (0, 4)]:
            with self.assertRaises(IndexError):
                frame.put(column, row, "X")
        # Nothing was written by any of those attempts.
        self.assertEqual(["    "] * 4, frame.text_rows())

    def test_a_cell_holds_exactly_one_character(self):
        frame = Frame(4, 4)
        with self.assertRaises(ValueError):
            frame.put(0, 0, "ab")
        with self.assertRaises(ValueError):
            frame.put(0, 0, "")

    def test_row_runs_cover_every_column_of_the_row_exactly_once(self):
        frame = Frame(6, 1)
        frame.put_text(0, 0, "ab", Colour.WALL)
        frame.put(2, 0, "c", Colour.DOT)
        frame.put_text(3, 0, "def", Colour.WALL)

        runs = frame.row_runs(0)
        self.assertEqual([(0, "ab", Colour.WALL),
                          (2, "c", Colour.DOT),
                          (3, "def", Colour.WALL)], runs)

        rebuilt = "".join(text for _, text, _ in runs)
        self.assertEqual("abcdef", rebuilt)
        self.assertEqual(frame.width, len(rebuilt))

    def test_row_runs_of_a_uniform_row_is_one_run_of_the_whole_width(self):
        frame = Frame(40, 1)
        self.assertEqual([(0, " " * 40, Colour.DEFAULT)], frame.row_runs(0))

    def test_cells_yields_every_cell_in_reading_order(self):
        frame = Frame(3, 2)
        frame.put(0, 0, "a")
        frame.put(2, 1, "b")
        seen = [(column, row, cell.character)
                for column, row, cell in frame.cells()]
        self.assertEqual(6, len(seen))
        self.assertEqual((0, 0, "a"), seen[0])
        self.assertEqual((2, 1, "b"), seen[-1])
        self.assertEqual([(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)],
                         [(column, row) for column, row, _ in seen])

    def test_two_frames_built_the_same_way_are_equal(self):
        first = Frame(4, 2)
        second = Frame(4, 2)
        self.assertEqual(first, second)
        first.put(1, 1, "X", Colour.GHOST)
        self.assertNotEqual(first, second)
        second.put(1, 1, "X", Colour.GHOST)
        self.assertEqual(first, second)

    def test_a_frame_differing_only_in_colour_is_not_equal(self):
        first = Frame(2, 1)
        second = Frame(2, 1)
        first.put(0, 0, "X", Colour.PLAYER)
        second.put(0, 0, "X", Colour.GHOST)
        self.assertNotEqual(first, second)

    def test_a_frame_must_have_a_positive_size(self):
        with self.assertRaises(ValueError):
            Frame(0, 10)
        with self.assertRaises(ValueError):
            Frame(10, 0)


class ColourTest(unittest.TestCase):

    def test_the_specification_s_five_colours_plus_a_default_are_all_distinct(self):
        self.assertEqual(6, len(ALL_COLOURS))
        self.assertEqual(6, len(set(ALL_COLOURS)))

    def test_colours_carry_no_terminal_detail(self):
        # A Colour is a name. If it ever grows a number, curses has leaked
        # above the port.
        self.assertEqual("Colour.WALL", repr(Colour.WALL))
        self.assertEqual(("name",), Colour.__slots__)


class KeyTest(unittest.TestCase):

    def test_the_four_arrows_are_distinct_named_keys(self):
        arrows = [Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT]
        self.assertEqual(4, len(set(arrows)))
        for arrow in arrows:
            self.assertTrue(arrow.is_arrow)
            self.assertFalse(arrow.is_printable)

    def test_a_printable_key_carries_its_character(self):
        key = Key.printable("q")
        self.assertTrue(key.is_printable)
        self.assertEqual("q", key.character)
        self.assertNotEqual(Key.printable("Q"), key)
        self.assertEqual(Key.printable("q"), key)

    def test_anything_else_arrives_as_other_and_is_neither_arrow_nor_printable(self):
        key = Key.other(265)
        self.assertFalse(key.is_arrow)
        self.assertFalse(key.is_printable)
        self.assertEqual(265, key.code)


class ScreenTooSmallTest(unittest.TestCase):

    def test_the_message_names_what_was_needed_and_what_was_found(self):
        error = ScreenTooSmall(80, 24)
        message = str(error)
        self.assertIn("40", message)
        self.assertIn("30", message)
        self.assertIn("80", message)
        self.assertIn("24", message)
        self.assertEqual((80, 24), (error.actual_width, error.actual_height))
        self.assertEqual((REQUIRED_WIDTH, REQUIRED_HEIGHT),
                         (error.required_width, error.required_height))


class PortShapeTest(unittest.TestCase):

    def test_the_port_cannot_be_instantiated_without_all_four_operations(self):
        class Half(Screen):
            def size(self):
                return (40, 30)

        with self.assertRaises(TypeError):
            Half()

    def test_the_port_module_imports_no_terminal_machinery(self):
        # The layer rule in the implementation plan, §3: nothing above the
        # port knows curses exists. A test is the cheapest way to keep it so.
        import terminalgame.screen.port as port_module
        with open(port_module.__file__, "r", encoding="utf-8") as handle:
            source = handle.read()
        for forbidden in ("import curses", "import subprocess", "import sys"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
