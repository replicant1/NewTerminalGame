# -*- coding: utf-8 -*-
"""WI-2 — the character grid surface.

Every test here runs with **no window**: the toolkit is stood in for by the
recording double in :mod:`tests.doubles`.
"""

from __future__ import annotations

import unittest

from terminal_game.presentation.frame import (
    FRAME_COLUMNS,
    FRAME_ROWS,
    STATUS_ROW,
    Colour,
    Frame,
    FrameBuilder,
)
from terminal_game.shell.grid_surface import (
    FONT_FAMILY,
    FONT_POINT_SIZE,
    GROUND,
    PALETTE,
    REQUIRED_GLYPHS,
    CellMetrics,
    CharacterGridSurface,
    FontNotAvailable,
    FontNotFixedWidth,
    FontSubstituted,
    GridGeometry,
    PixelSize,
    font_specification,
    measure_cell_metrics,
    pixel_size_for,
)
from terminal_game.shell.toolkit import PixelSize as ToolkitPixelSize

from tests.doubles import (
    FakeFontProbe,
    RecordingCanvas,
    assert_surface_shows,
    reconstruct_frame,
)
from tests.specimen import SPECIMEN_MAZE_ROWS, SPECIMEN_STATUS_ROW

#: Menlo at 16pt, as measured on this machine — see
#: docs/findings/WI-2-cell-metrics.md.
MEASURED = CellMetrics(width=10, height=19)

#: Which named colour a glyph of the specimen picture is drawn in.  This is
#: test data for painting a picture with several colours in it; composing a
#: real frame from a game state is WI-12's, not this item's.
_COLOUR_OF_GLYPH = {
    "▪": Colour.DOT_GOLD,
    "■": Colour.WALL_BLUE,
    "▐": Colour.PLAYER_YELLOW,
    "▌": Colour.PLAYER_YELLOW,
    "▗": Colour.GHOST_PINK,
    "▖": Colour.GHOST_PINK,
}

#: Measured from the specimen: the player's motif is on this row, its left
#: column here, and the ghost's motif is on this row.  Square *c* sits at
#: column 2c and the motif covers 2c-1 .. 2c+1, so a move of one square shifts
#: the motif by two columns.
PLAYER_ROW = 13
PLAYER_LEFT_COLUMN = 19
GHOST_ROW = 27


def specimen_frame(player_at=None):
    """The specimen picture as a frame, in several colours.

    *player_at* moves the player's motif so that it starts at that column,
    which is how two frames a known number of cells apart are built.
    """
    builder = FrameBuilder()
    for row, text in enumerate(SPECIMEN_MAZE_ROWS):
        for column, glyph in enumerate(text):
            if glyph == " ":
                continue
            if glyph == "█":
                colour = (
                    Colour.GHOST_PINK
                    if row == GHOST_ROW
                    else Colour.PLAYER_YELLOW
                )
            else:
                colour = _COLOUR_OF_GLYPH.get(glyph, Colour.WALL_BLUE)
            builder.set_cell(row, column, glyph, colour)
    builder.write(STATUS_ROW, 0, SPECIMEN_STATUS_ROW, Colour.STATUS_CYAN)
    if player_at is not None:
        for column in range(
            PLAYER_LEFT_COLUMN, PLAYER_LEFT_COLUMN + 3
        ):
            builder.set_cell(PLAYER_ROW, column, " ", Colour.GROUND_BLACK)
        builder.write(
            PLAYER_ROW, player_at, "▐█▌", Colour.PLAYER_YELLOW
        )
    return builder.build()


def non_blank_count(frame):
    return sum(
        1
        for row in range(FRAME_ROWS)
        for column in range(FRAME_COLUMNS)
        if frame.cell_at(row, column).glyph != " "
    )


def differing_cells(first, second):
    return [
        (row, column)
        for row in range(FRAME_ROWS)
        for column in range(FRAME_COLUMNS)
        if first.cell_at(row, column) != second.cell_at(row, column)
    ]


def a_surface(metrics=MEASURED):
    canvas = RecordingCanvas()
    return canvas, CharacterGridSurface(canvas, metrics)


class HowManyPixelsFortyByThirtyNeeds(unittest.TestCase):
    """WIN-2 is derived here, so it is the metrics multiplied out."""

    def test_the_measured_metrics_give_a_four_hundred_by_five_seventy_window(self):
        geometry = GridGeometry(MEASURED)

        self.assertEqual(PixelSize(400, 570), geometry.pixel_size)

    def test_the_size_is_always_the_metrics_multiplied_out(self):
        for metrics in (
            CellMetrics(8, 16),
            CellMetrics(10, 19),
            CellMetrics(11, 21),
            CellMetrics(12, 24),
        ):
            geometry = GridGeometry(metrics)

            self.assertEqual(
                PixelSize(
                    FRAME_COLUMNS * metrics.width, FRAME_ROWS * metrics.height
                ),
                geometry.pixel_size,
            )

    def test_a_bigger_font_gives_a_bigger_window(self):
        smaller = GridGeometry(CellMetrics(8, 16)).pixel_size
        larger = GridGeometry(CellMetrics(12, 24)).pixel_size

        self.assertLess(smaller.width, larger.width)
        self.assertLess(smaller.height, larger.height)

    def test_a_surface_reports_the_size_of_its_own_grid(self):
        _, surface = a_surface(CellMetrics(11, 21))

        self.assertEqual(PixelSize(440, 630), surface.pixel_size())

    def test_the_size_can_be_had_without_building_a_surface_first(self):
        # The window owner is told its size when it is built, and it is the
        # thing that makes the window — so the number has to be available
        # before there is anything to paint into.
        self.assertEqual(PixelSize(400, 570), pixel_size_for(MEASURED))

    def test_the_size_handed_over_is_the_type_the_window_owner_declares(self):
        # WI-2 / WI-3 seam: one PixelSize on the boundary, not two.
        _, surface = a_surface()

        self.assertIsInstance(surface.pixel_size(), ToolkitPixelSize)
        self.assertIs(PixelSize, ToolkitPixelSize)

    def test_a_cell_cannot_be_zero_pixels(self):
        with self.assertRaises(ValueError):
            GridGeometry(CellMetrics(0, 19))

    def test_a_cell_cannot_be_a_negative_size(self):
        with self.assertRaises(ValueError):
            GridGeometry(CellMetrics(10, -1))


class WhereEachCellLands(unittest.TestCase):
    """Each cell is drawn at its own computed position, not as a row."""

    def setUp(self):
        self.geometry = GridGeometry(MEASURED)

    def test_the_first_cell_is_at_the_top_left_corner(self):
        self.assertEqual((0, 0), self.geometry.cell_origin(0, 0))

    def test_moving_one_column_moves_one_cell_width(self):
        self.assertEqual((10, 0), self.geometry.cell_origin(0, 1))

    def test_moving_one_row_moves_one_cell_height(self):
        self.assertEqual((0, 19), self.geometry.cell_origin(1, 0))

    def test_the_last_cell_ends_exactly_at_the_bottom_right_of_the_window(self):
        x, y = self.geometry.cell_origin(FRAME_ROWS - 1, FRAME_COLUMNS - 1)

        self.assertEqual(
            self.geometry.pixel_size,
            PixelSize(x + MEASURED.width, y + MEASURED.height),
        )

    def test_a_position_maps_back_to_the_cell_it_came_from(self):
        for row, column in ((0, 0), (1, 1), (12, 25), (29, 39)):
            x, y = self.geometry.cell_origin(row, column)

            self.assertEqual((row, column), self.geometry.cell_at_pixel(x, y))

    def test_a_pixel_that_is_not_a_cell_origin_is_refused(self):
        with self.assertRaises(ValueError):
            self.geometry.cell_at_pixel(5, 19)

    def test_a_cell_outside_the_grid_has_no_position(self):
        with self.assertRaises(IndexError):
            self.geometry.cell_origin(FRAME_ROWS, 0)
        with self.assertRaises(IndexError):
            self.geometry.cell_origin(0, FRAME_COLUMNS)


class MeasuringThePinnedFont(unittest.TestCase):
    """A silent substitution silently changes the size of the window."""

    def test_a_present_fixed_width_font_measures_to_its_cell(self):
        probe = FakeFontProbe(default_advance=10, linespace=19)

        self.assertEqual(
            CellMetrics(10, 19), measure_cell_metrics(probe, "Menlo", 16)
        )

    def test_a_font_that_is_not_installed_raises_rather_than_substituting(self):
        probe = FakeFontProbe(families=("Helvetica",))

        with self.assertRaises(FontNotAvailable) as raised:
            measure_cell_metrics(probe, "Menlo", 16)

        self.assertIn("Menlo", str(raised.exception))

    def test_a_font_the_toolkit_quietly_swaps_raises_and_names_both(self):
        probe = FakeFontProbe(resolves_to={"Menlo": ".AppleSystemUIFont"})

        with self.assertRaises(FontSubstituted) as raised:
            measure_cell_metrics(probe, "Menlo", 16)

        self.assertIn("Menlo", str(raised.exception))
        self.assertIn(".AppleSystemUIFont", str(raised.exception))

    def test_a_font_that_is_not_fixed_width_is_refused(self):
        probe = FakeFontProbe(advances={"i": 4, "W": 16})

        with self.assertRaises(FontNotFixedWidth):
            measure_cell_metrics(probe, "Menlo", 16)

    def test_a_font_whose_double_line_wall_glyph_is_a_different_width_is_refused(self):
        probe = FakeFontProbe(advances={"═": 20})

        with self.assertRaises(FontNotFixedWidth):
            measure_cell_metrics(probe, "Menlo", 16)

    def test_a_font_whose_block_glyph_is_a_different_width_is_refused(self):
        probe = FakeFontProbe(advances={"█": 20})

        with self.assertRaises(FontNotFixedWidth):
            measure_cell_metrics(probe, "Menlo", 16)

    def test_a_font_whose_dot_is_a_different_width_is_refused(self):
        probe = FakeFontProbe(advances={"▪": 6})

        with self.assertRaises(FontNotFixedWidth):
            measure_cell_metrics(probe, "Menlo", 16)

    def test_a_zero_width_measurement_is_refused(self):
        probe = FakeFontProbe(default_advance=0)

        with self.assertRaises(FontNotFixedWidth):
            measure_cell_metrics(probe, "Menlo", 16)

    def test_the_required_glyphs_are_the_ones_the_picture_is_made_of(self):
        for glyph in "═║╔╗╚╝╠╣" \
                     "╦╩╬▪■▐█▌" \
                     "▗▖ 0123456789qCAUGHTCLEARED,":
            self.assertIn(glyph, REQUIRED_GLYPHS)

    def test_the_pinned_font_is_named_and_sized_in_one_place(self):
        self.assertEqual((FONT_FAMILY, FONT_POINT_SIZE), font_specification())


class TheSurfacePreparesItsCanvas(unittest.TestCase):
    """A black ground, the exact size, no border and no caret."""

    def setUp(self):
        self.canvas, self.surface = a_surface()

    def test_the_canvas_is_sized_to_the_whole_grid(self):
        self.assertEqual(400, self.canvas.cget("width"))
        self.assertEqual(570, self.canvas.cget("height"))

    def test_the_ground_is_black(self):
        self.assertEqual(GROUND, self.canvas.cget("background"))
        self.assertEqual("#000000", GROUND)

    def test_there_is_no_border_and_no_focus_ring_round_the_grid(self):
        self.assertEqual(0, self.canvas.cget("highlightthickness"))
        self.assertEqual(0, self.canvas.cget("borderwidth"))

    def test_the_text_caret_has_no_width_so_it_can_never_show(self):
        self.assertEqual(0, self.canvas.cget("insertwidth"))

    def test_the_black_ground_is_the_canvas_and_not_a_rectangle_drawn_on_it(self):
        self.assertEqual([], self.canvas.drawing_calls())


class PaintingAFrame(unittest.TestCase):
    """One placement per non-blank cell, where the mapping says, in its colour."""

    def setUp(self):
        self.canvas, self.surface = a_surface()
        self.frame = specimen_frame()
        # 696 of the 1,200 cells carry a glyph, in five of the six colours.
        # A fixture that had quietly become blank would make most of this
        # class assert nothing, so it is checked rather than assumed.
        self.assertEqual(696, non_blank_count(self.frame))
        self.assertEqual(
            5,
            len({
                self.frame.cell_at(row, column).colour
                for row in range(FRAME_ROWS)
                for column in range(FRAME_COLUMNS)
                if self.frame.cell_at(row, column).glyph != " "
            }),
        )

    def test_the_picture_painted_is_the_picture_given(self):
        self.surface.paint(self.frame)

        assert_surface_shows(self, self.canvas, self.surface, self.frame)

    def test_there_is_one_placement_per_non_blank_cell_and_no_more(self):
        self.surface.paint(self.frame)

        self.assertEqual(
            non_blank_count(self.frame), len(self.canvas.live_items())
        )

    def test_a_blank_cell_has_nothing_drawn_in_it(self):
        self.surface.paint(self.frame)

        drawn = {
            self.surface.geometry.cell_at_pixel(*item.coordinates)
            for item in self.canvas.live_items()
        }
        self.assertNotIn((0, FRAME_COLUMNS - 1), drawn)
        self.assertNotIn((STATUS_ROW, FRAME_COLUMNS - 1), drawn)

    def test_every_glyph_is_drawn_in_the_pinned_font(self):
        self.surface.paint(self.frame)

        fonts = {item.options["font"] for item in self.canvas.live_items()}
        self.assertEqual({(FONT_FAMILY, FONT_POINT_SIZE)}, fonts)

    def test_every_glyph_is_anchored_at_the_top_left_of_its_own_cell(self):
        self.surface.paint(self.frame)

        anchors = {item.options["anchor"] for item in self.canvas.live_items()}
        self.assertEqual({"nw"}, anchors)

    def test_nothing_but_characters_is_ever_drawn(self):
        self.surface.paint(self.frame)

        self.assertEqual({"text"}, self.canvas.kinds_drawn())

    def test_no_caret_is_ever_asked_for(self):
        self.surface.paint(self.frame)

        self.assertEqual([], self.canvas.caret_calls)

    def test_a_blank_frame_draws_nothing_at_all(self):
        self.surface.paint(Frame.blank())

        self.assertEqual([], self.canvas.live_items())

    def test_painting_something_that_is_not_a_frame_is_refused(self):
        with self.assertRaises(TypeError):
            self.surface.paint("\n".join([" " * 40] * 30))


class TheRuleThatThereAreNoImages(unittest.TestCase):
    """SCRN-2, caution C5 — a rule now, not a fact, so it is asserted."""

    def test_the_recording_canvas_would_notice_an_image(self):
        canvas = RecordingCanvas()

        canvas.create_image(0, 0, image="anything")

        self.assertEqual({"image"}, canvas.kinds_drawn())

    def test_the_recording_canvas_would_notice_a_rectangle(self):
        canvas = RecordingCanvas()

        canvas.create_rectangle(0, 0, 10, 10, fill="#ff0000")

        self.assertEqual({"rectangle"}, canvas.kinds_drawn())

    def test_the_recording_canvas_would_notice_a_caret(self):
        canvas = RecordingCanvas()

        canvas.focus(1)
        canvas.icursor(1, 0)

        self.assertEqual(2, len(canvas.caret_calls))

    def test_reconstructing_a_picture_containing_an_image_fails_loudly(self):
        canvas, surface = a_surface()
        canvas.create_image(0, 0, image="a photograph")

        with self.assertRaises(AssertionError):
            reconstruct_frame(
                canvas,
                surface.geometry,
                {colour: surface.colour_of(colour) for colour in Colour},
            )


class RepaintingIsADifference(unittest.TestCase):
    """SCRN-7 — no clear-then-redraw for the window server to catch halfway."""

    def setUp(self):
        self.canvas, self.surface = a_surface()
        self.first = specimen_frame(player_at=PLAYER_LEFT_COLUMN)
        self.moved = specimen_frame(player_at=PLAYER_LEFT_COLUMN + 2)
        # A fixture that had become identical would make the two tests below
        # assert nothing at all, so say out loud what it is worth.
        self.changed = differing_cells(self.first, self.moved)
        self.assertEqual(5, len(self.changed))

    def test_repainting_the_same_frame_shows_the_same_picture(self):
        self.surface.paint(self.first)
        self.surface.paint(self.first)

        assert_surface_shows(self, self.canvas, self.surface, self.first)

    def test_repainting_an_unchanged_frame_costs_no_drawing_at_all(self):
        self.surface.paint(self.first)
        before = len(self.canvas.drawing_calls())

        self.surface.paint(self.first)

        self.assertEqual(before, len(self.canvas.drawing_calls()))

    def test_repainting_an_equal_but_separate_frame_also_costs_nothing(self):
        self.surface.paint(self.first)
        before = len(self.canvas.drawing_calls())

        self.surface.paint(specimen_frame(player_at=PLAYER_LEFT_COLUMN))

        self.assertEqual(before, len(self.canvas.drawing_calls()))

    def test_moving_the_player_touches_only_the_cells_that_changed(self):
        self.surface.paint(self.first)
        before = len(self.canvas.drawing_calls())

        self.surface.paint(self.moved)

        self.assertEqual(
            len(self.changed), len(self.canvas.drawing_calls()) - before
        )

    def test_a_move_costs_five_cells_and_not_the_whole_twelve_hundred(self):
        self.surface.paint(self.first)
        before = len(self.canvas.drawing_calls())

        self.surface.paint(self.moved)

        self.assertEqual(5, len(self.canvas.drawing_calls()) - before)

    def test_the_picture_after_the_player_moves_is_the_new_picture(self):
        self.surface.paint(self.first)

        self.surface.paint(self.moved)

        assert_surface_shows(self, self.canvas, self.surface, self.moved)

    def test_a_cell_that_becomes_blank_is_left_showing_the_ground(self):
        builder = FrameBuilder()
        builder.set_cell(3, 4, "▪", Colour.DOT_GOLD)
        self.surface.paint(builder.build())

        self.surface.paint(Frame.blank())

        self.assertEqual([], self.canvas.live_items())
        assert_surface_shows(self, self.canvas, self.surface, Frame.blank())

    def test_a_cell_that_becomes_filled_gets_a_glyph(self):
        self.surface.paint(Frame.blank())
        builder = FrameBuilder()
        builder.set_cell(3, 4, "█", Colour.GHOST_PINK)
        second = builder.build()

        self.surface.paint(second)

        assert_surface_shows(self, self.canvas, self.surface, second)

    def test_a_cell_that_only_changes_colour_is_repainted_in_the_new_colour(self):
        first = FrameBuilder()
        first.set_cell(3, 4, "█", Colour.PLAYER_YELLOW)
        second = FrameBuilder()
        second.set_cell(3, 4, "█", Colour.GHOST_PINK)
        self.surface.paint(first.build())

        self.surface.paint(second.build())

        assert_surface_shows(self, self.canvas, self.surface, second.build())

    def test_the_surface_remembers_what_it_last_painted(self):
        self.assertIsNone(self.surface.painted)

        self.surface.paint(self.first)

        self.assertEqual(self.first, self.surface.painted)

    def test_clearing_takes_everything_off_and_the_next_paint_still_works(self):
        self.surface.paint(self.first)

        self.surface.clear()

        self.assertEqual([], self.canvas.live_items())
        self.assertIsNone(self.surface.painted)

        self.surface.paint(self.first)
        assert_surface_shows(self, self.canvas, self.surface, self.first)


class TheColoursReachingTheSurface(unittest.TestCase):
    """SCRN-3 to SCRN-6: the vocabulary arrives unchanged and stays distinct."""

    def test_every_named_colour_has_something_to_look_like(self):
        for colour in Colour:
            self.assertIn(colour, PALETTE)

    def test_the_six_colours_are_all_different(self):
        self.assertEqual(len(Colour), len({PALETTE[c] for c in Colour}))

    def test_the_player_and_the_ghost_are_different_colours(self):
        self.assertNotEqual(
            PALETTE[Colour.PLAYER_YELLOW], PALETTE[Colour.GHOST_PINK]
        )

    def test_each_colour_survives_the_journey_to_the_surface_and_back(self):
        canvas, surface = a_surface()
        builder = FrameBuilder()
        for column, colour in enumerate(Colour):
            builder.set_cell(0, column, "█", colour)
        frame = builder.build()

        surface.paint(frame)

        assert_surface_shows(self, canvas, surface, frame)

    def test_a_palette_missing_a_colour_is_refused_at_construction(self):
        short = {c: PALETTE[c] for c in Colour if c is not Colour.STATUS_CYAN}

        with self.assertRaises(ValueError):
            CharacterGridSurface(RecordingCanvas(), MEASURED, palette=short)

    def test_asking_for_a_colour_outside_the_vocabulary_is_refused(self):
        _, surface = a_surface()

        with self.assertRaises(ValueError):
            surface.colour_of("blue")


if __name__ == "__main__":
    unittest.main()
