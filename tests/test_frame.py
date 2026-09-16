# -*- coding: utf-8 -*-
"""WI-1 — the picture as a value."""

from __future__ import annotations

import unittest
from enum import Enum

from terminal_game.presentation.frame import (
    BLANK,
    FRAME_COLUMNS,
    FRAME_ROWS,
    MAZE_COLUMNS,
    MAZE_ROWS,
    RIGHT_MARGIN_COLUMNS,
    STATUS_ROW,
    Cell,
    Colour,
    Frame,
    FrameBuilder,
)

from tests.specimen import (
    SPECIMEN_MAZE_ROWS,
    SPECIMEN_ROWS,
    SPECIMEN_STATUS_ROW,
)


def blank_rows():
    """Thirty rows of forty blank cells, as plain lists."""
    return [[BLANK] * FRAME_COLUMNS for _ in range(FRAME_ROWS)]


class FrameShape(unittest.TestCase):
    """A frame is 30 x 40 and refuses to be anything else."""

    def test_a_blank_frame_is_thirty_rows_of_forty_cells(self):
        frame = Frame.blank()

        self.assertEqual(FRAME_ROWS, len(frame.rows))
        for row in frame.rows:
            self.assertEqual(FRAME_COLUMNS, len(row))

    def test_a_blank_frame_renders_as_thirty_lines_of_forty_spaces(self):
        text = Frame.blank().to_text()

        lines = text.split("\n")
        self.assertEqual(FRAME_ROWS, len(lines))
        self.assertEqual([" " * FRAME_COLUMNS] * FRAME_ROWS, lines)

    def test_too_few_rows_is_refused(self):
        with self.assertRaises(ValueError):
            Frame(blank_rows()[:-1])

    def test_too_many_rows_is_refused(self):
        rows = blank_rows()
        rows.append([BLANK] * FRAME_COLUMNS)

        with self.assertRaises(ValueError):
            Frame(rows)

    def test_a_short_row_is_refused(self):
        rows = blank_rows()
        rows[7] = rows[7][:-1]

        with self.assertRaises(ValueError):
            Frame(rows)

    def test_a_long_row_is_refused(self):
        rows = blank_rows()
        rows[7] = rows[7] + [BLANK]

        with self.assertRaises(ValueError):
            Frame(rows)


class PositionsOutsideTheFrame(unittest.TestCase):
    """A cell out of range is refused, not silently ignored."""

    def test_reading_past_the_last_row_raises(self):
        with self.assertRaises(IndexError):
            Frame.blank().cell_at(FRAME_ROWS, 0)

    def test_reading_past_the_last_column_raises(self):
        with self.assertRaises(IndexError):
            Frame.blank().cell_at(0, FRAME_COLUMNS)

    def test_a_negative_row_raises_rather_than_wrapping_round(self):
        with self.assertRaises(IndexError):
            Frame.blank().cell_at(-1, 0)

    def test_a_negative_column_raises_rather_than_wrapping_round(self):
        with self.assertRaises(IndexError):
            Frame.blank().cell_at(0, -1)

    def test_writing_past_the_last_row_raises_and_changes_nothing(self):
        builder = FrameBuilder()

        with self.assertRaises(IndexError):
            builder.set_cell(FRAME_ROWS, 0, "x", Colour.WALL_BLUE)

        self.assertEqual(Frame.blank(), builder.build())

    def test_writing_to_a_negative_column_raises_and_changes_nothing(self):
        builder = FrameBuilder()

        with self.assertRaises(IndexError):
            builder.set_cell(0, -1, "x", Colour.WALL_BLUE)

        self.assertEqual(Frame.blank(), builder.build())

    def test_text_running_past_the_right_edge_writes_nothing_at_all(self):
        builder = FrameBuilder()

        with self.assertRaises(IndexError):
            builder.write(0, FRAME_COLUMNS - 3, "four", Colour.STATUS_CYAN)

        self.assertEqual(" " * FRAME_COLUMNS, builder.build().row_text(0))

    def test_text_ending_exactly_at_the_right_edge_is_written(self):
        builder = FrameBuilder()

        builder.write(0, FRAME_COLUMNS - 4, "four", Colour.STATUS_CYAN)

        self.assertEqual(
            " " * (FRAME_COLUMNS - 4) + "four", builder.build().row_text(0)
        )


class TheColourVocabulary(unittest.TestCase):
    """Only colours in the closed vocabulary are accepted."""

    def test_the_vocabulary_is_the_six_colours_the_requirements_name(self):
        self.assertEqual(
            {
                "WALL_BLUE",
                "DOT_GOLD",
                "PLAYER_YELLOW",
                "GHOST_PINK",
                "STATUS_CYAN",
                "GROUND_BLACK",
            },
            {member.name for member in Colour},
        )

    def test_every_named_colour_is_accepted(self):
        builder = FrameBuilder()

        for column, colour in enumerate(Colour):
            builder.set_cell(0, column, "x", colour)

        frame = builder.build()
        for column, colour in enumerate(Colour):
            self.assertEqual(colour, frame.colour_at(0, column))

    def test_a_colour_named_as_a_string_is_refused(self):
        builder = FrameBuilder()

        with self.assertRaises(ValueError):
            builder.set_cell(0, 0, "x", "blue")

    def test_a_colour_from_some_other_vocabulary_is_refused(self):
        class OtherPalette(Enum):
            MAGENTA = "magenta"

        builder = FrameBuilder()

        with self.assertRaises(ValueError):
            builder.set_cell(0, 0, "x", OtherPalette.MAGENTA)

    def test_no_colour_at_all_is_refused(self):
        builder = FrameBuilder()

        with self.assertRaises(ValueError):
            builder.set_cell(0, 0, "x", None)

    def test_a_frame_assembled_from_cells_with_a_foreign_colour_is_refused(self):
        rows = blank_rows()
        rows[3][4] = Cell("x", "blue")

        with self.assertRaises(ValueError):
            Frame(rows)


class ACellHoldsOneCharacter(unittest.TestCase):
    """SCRN-2 as a rule, not a fact: nothing but a character goes in a cell."""

    def test_an_empty_glyph_is_refused(self):
        builder = FrameBuilder()

        with self.assertRaises(ValueError):
            builder.set_cell(0, 0, "", Colour.WALL_BLUE)

    def test_two_characters_in_one_cell_are_refused(self):
        builder = FrameBuilder()

        with self.assertRaises(ValueError):
            builder.set_cell(0, 0, "ab", Colour.WALL_BLUE)

    def test_something_that_is_not_text_is_refused(self):
        builder = FrameBuilder()

        with self.assertRaises(ValueError):
            builder.set_cell(0, 0, 7, Colour.WALL_BLUE)

    def test_the_three_column_actor_motifs_are_three_separate_cells(self):
        builder = FrameBuilder()

        builder.write(12, 10, "▐█▌", Colour.PLAYER_YELLOW)

        frame = builder.build()
        self.assertEqual("▐", frame.cell_at(12, 10).glyph)
        self.assertEqual("█", frame.cell_at(12, 11).glyph)
        self.assertEqual("▌", frame.cell_at(12, 12).glyph)


class FramesCompareAsValues(unittest.TestCase):
    """Two frames built the same way are equal; one cell apart, they are not."""

    def two_builders(self):
        first, second = FrameBuilder(), FrameBuilder()
        for builder in (first, second):
            builder.write(0, 0, "╔══╗", Colour.WALL_BLUE)
            builder.set_cell(5, 5, "▪", Colour.DOT_GOLD)
            builder.write(
                STATUS_ROW, 0, "score 0    arrows, q quits", Colour.STATUS_CYAN
            )
        return first, second

    def test_frames_built_the_same_way_are_equal(self):
        first, second = self.two_builders()

        self.assertEqual(first.build(), second.build())

    def test_frames_built_the_same_way_hash_alike(self):
        first, second = self.two_builders()

        self.assertEqual(hash(first.build()), hash(second.build()))

    def test_one_different_glyph_makes_two_frames_unequal(self):
        first, second = self.two_builders()
        second.set_cell(5, 5, "■", Colour.DOT_GOLD)

        self.assertNotEqual(first.build(), second.build())

    def test_one_different_colour_makes_two_frames_unequal(self):
        first, second = self.two_builders()
        second.set_cell(5, 5, "▪", Colour.PLAYER_YELLOW)

        self.assertNotEqual(first.build(), second.build())

    def test_two_frames_differing_only_in_colour_still_render_alike(self):
        first, second = self.two_builders()
        second.set_cell(5, 5, "▪", Colour.PLAYER_YELLOW)

        self.assertEqual(first.build().to_text(), second.build().to_text())

    def test_a_frame_is_not_equal_to_its_own_text(self):
        frame = Frame.blank()

        self.assertNotEqual(frame, frame.to_text())


class AFrameIsImmutable(unittest.TestCase):
    """What was handed over stays as it was handed over."""

    def test_a_built_frame_does_not_change_when_the_builder_carries_on(self):
        builder = FrameBuilder()
        builder.set_cell(1, 1, "▪", Colour.DOT_GOLD)
        frame = builder.build()

        builder.set_cell(1, 1, "█", Colour.GHOST_PINK)

        self.assertEqual("▪", frame.cell_at(1, 1).glyph)
        self.assertEqual(Colour.DOT_GOLD, frame.colour_at(1, 1))

    def test_the_rows_handed_out_cannot_be_written_through(self):
        frame = Frame.blank()

        with self.assertRaises(TypeError):
            frame.rows[0][0] = Cell("x", Colour.WALL_BLUE)


class RowTwentyNineIsPlacedAsAValue(unittest.TestCase):
    """STAT-1: whoever owns row 29 hands it over whole (WI-13 will)."""

    def test_a_row_of_forty_cells_can_be_placed_whole(self):
        given = [Cell(character, Colour.STATUS_CYAN) for character in "CAUGHT"]
        given += [BLANK] * (FRAME_COLUMNS - len(given))
        builder = FrameBuilder()

        builder.place_row(STATUS_ROW, given)

        frame = builder.build()
        self.assertEqual("CAUGHT" + " " * 34, frame.row_text(STATUS_ROW))
        self.assertEqual(Colour.STATUS_CYAN, frame.colour_at(STATUS_ROW, 0))

    def test_a_row_of_the_wrong_length_is_refused(self):
        builder = FrameBuilder()

        with self.assertRaises(ValueError):
            builder.place_row(STATUS_ROW, [BLANK] * (FRAME_COLUMNS - 1))

    def test_a_row_outside_the_frame_is_refused(self):
        builder = FrameBuilder()

        with self.assertRaises(IndexError):
            builder.place_row(FRAME_ROWS, [BLANK] * FRAME_COLUMNS)


class RenderingTheSpecimenPicture(unittest.TestCase):
    """The picture measured in section 5 of the plan, rendered as text."""

    def specimen_frame(self):
        builder = FrameBuilder()
        for row, text in enumerate(SPECIMEN_MAZE_ROWS):
            builder.write(row, 0, text, Colour.WALL_BLUE)
        builder.write(STATUS_ROW, 0, SPECIMEN_STATUS_ROW, Colour.STATUS_CYAN)
        return builder.build()

    def test_the_geometry_constants_are_the_specimen_picture_as_measured(self):
        self.assertEqual(FRAME_ROWS, len(SPECIMEN_ROWS))
        self.assertEqual(MAZE_ROWS, len(SPECIMEN_MAZE_ROWS))
        self.assertEqual(
            {MAZE_COLUMNS}, {len(row) for row in SPECIMEN_MAZE_ROWS}
        )
        self.assertEqual(
            RIGHT_MARGIN_COLUMNS, FRAME_COLUMNS - MAZE_COLUMNS
        )
        self.assertEqual(MAZE_ROWS, STATUS_ROW)

    def test_the_whole_picture_renders_character_for_character(self):
        expected = "\n".join(
            line.ljust(FRAME_COLUMNS) for line in SPECIMEN_ROWS
        )

        self.assertEqual(expected, self.specimen_frame().to_text())

    def test_every_maze_row_ends_in_a_three_column_blank_margin(self):
        frame = self.specimen_frame()

        for row in range(MAZE_ROWS):
            text = frame.row_text(row)
            self.assertEqual(FRAME_COLUMNS, len(text))
            self.assertEqual(SPECIMEN_MAZE_ROWS[row], text[:MAZE_COLUMNS])
            self.assertEqual(" " * RIGHT_MARGIN_COLUMNS, text[MAZE_COLUMNS:])

    def test_the_right_hand_margin_is_black_ground_and_not_merely_spaces(self):
        frame = self.specimen_frame()

        for row in range(MAZE_ROWS):
            for column in range(MAZE_COLUMNS, FRAME_COLUMNS):
                self.assertEqual(BLANK, frame.cell_at(row, column))

    def test_the_actors_are_three_column_motifs_centred_on_their_square(self):
        """Measured from the specimen picture — plan section 5, assumption A6.

        This is a statement about the *requirements document*, not about the
        composer: it says what the picture we are copying actually does.  WI-12
        owns the separate question of whether the composer reproduces it.
        """
        player_row = 13
        ghost_row = 27

        player = SPECIMEN_MAZE_ROWS[player_row]
        ghost = SPECIMEN_MAZE_ROWS[ghost_row]

        self.assertEqual("▐█▌", player[19:22])
        self.assertEqual("▗█▖", ghost[1:4])
        # Centre column is 2c, so the motif covers 2c-1 .. 2c+1 and eats the
        # connector on each side.
        for centre in (20, 2):
            self.assertEqual(0, centre % 2)
        # The motifs appear exactly once each in the whole picture.
        self.assertEqual(
            1,
            sum(row.count("▐█▌") for row in SPECIMEN_MAZE_ROWS),
        )
        self.assertEqual(
            1,
            sum(row.count("▗█▖") for row in SPECIMEN_MAZE_ROWS),
        )

    def test_the_status_row_carries_the_colour_it_was_written_in(self):
        frame = self.specimen_frame()

        for column in range(len(SPECIMEN_STATUS_ROW)):
            self.assertEqual(
                Colour.STATUS_CYAN, frame.colour_at(STATUS_ROW, column)
            )


class BuildingAFrameFromText(unittest.TestCase):
    """A convenience for picture comparisons — 30 lines, one colour."""

    def test_short_lines_are_padded_out_to_forty_columns(self):
        frame = Frame.from_text("\n".join(["ab"] * FRAME_ROWS))

        self.assertEqual("ab" + " " * 38, frame.row_text(0))

    def test_the_text_given_comes_back_from_to_text_padded(self):
        given = "\n".join(SPECIMEN_ROWS)

        frame = Frame.from_text(given, Colour.WALL_BLUE)

        self.assertEqual(
            "\n".join(line.ljust(FRAME_COLUMNS) for line in SPECIMEN_ROWS),
            frame.to_text(),
        )

    def test_the_wrong_number_of_lines_is_refused(self):
        with self.assertRaises(ValueError):
            Frame.from_text("\n".join([""] * (FRAME_ROWS - 1)))

    def test_a_line_wider_than_the_frame_is_refused(self):
        lines = [""] * FRAME_ROWS
        lines[0] = "x" * (FRAME_COLUMNS + 1)

        with self.assertRaises(ValueError):
            Frame.from_text("\n".join(lines))

    def test_a_colour_outside_the_vocabulary_is_refused(self):
        with self.assertRaises(ValueError):
            Frame.from_text("\n".join([""] * FRAME_ROWS), "blue")


if __name__ == "__main__":
    unittest.main()
