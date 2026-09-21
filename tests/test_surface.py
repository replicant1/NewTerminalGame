"""The character grid surface: SCRN-7, SCRN-2, and WIN-2's pixel size.

These tests run against a **real** Tk canvas on a root that never reaches the
screen.  They assert what the canvas actually holds, read back from the canvas
itself, rather than what the painter believes it painted.

What they deliberately do **not** do is re-derive the cell arithmetic
(``tests/test_metrics.py`` owns that), re-check the colours
(``tests/test_palette.py``), or re-check that a cell is one character
(``tests/test_field.py``).  What is owned here is the join — that a field of
glyph-and-colour becomes exactly that picture on a canvas of exactly that size
— and the two things only a real canvas can answer: that nothing but glyphs
and flat colour is ever on it, and that the picture is never torn down.
"""

from __future__ import annotations

import tkinter

import pytest

from terminal_game.presentation import palette
from terminal_game.presentation.field import Cell, Field
from terminal_game.presentation.metrics import (
    COLUMNS,
    MEASURED_MENLO_12,
    ROWS,
    CellMetrics,
)
from terminal_game.presentation.surface import PERMITTED_ITEM_TYPES, GridSurface
from terminal_game.presentation.wall_glyphs import ALL_WALL_GLYPHS


def a_full_field():
    """A field with something different in every cell, and every colour used."""
    field = Field()
    glyphs = sorted(ALL_WALL_GLYPHS) + ["▪", "█", "▐", "▌", "q"]
    colours = [palette.WALL, palette.DOT, palette.PLAYER, palette.GHOST, palette.STATUS]
    for row in range(ROWS):
        for column in range(COLUMNS):
            index = row * COLUMNS + column
            field[column, row] = Cell(
                glyphs[index % len(glyphs)], colours[index % len(colours)]
            )
    return field


class TestTheDefaultSuitePutsNoWindowOnTheScreen:
    """Plan section 1.6's bar, and one of the things WI-5 must establish.

    Asserted against the toolkit's own reported state, which is the only thing
    an agent can honestly check — see ``docs/findings/S-1-tk-headless.md``.
    """

    def test_the_root_is_withdrawn(self, tk_root):
        assert tk_root.state() == "withdrawn"

    def test_the_root_was_never_mapped(self, tk_root):
        assert not tk_root.winfo_ismapped()

    def test_the_root_is_not_viewable(self, tk_root):
        assert not tk_root.winfo_viewable()

    def test_building_a_surface_does_not_map_anything(self, tk_root):
        made = GridSurface(tk_root)
        try:
            made.widget.update_idletasks()
            assert tk_root.state() == "withdrawn"
            assert not tk_root.winfo_ismapped()
            assert not made.widget.winfo_ismapped()
        finally:
            made.widget.destroy()

    def test_presenting_a_frame_does_not_map_anything(self, surface, tk_root):
        surface.present(a_full_field())
        assert tk_root.state() == "withdrawn"
        assert not surface.widget.winfo_ismapped()
        assert not surface.widget.winfo_viewable()


class TestWinTwoThePixelSize:
    """WIN-2: 40 x 30 cells of the chosen font, derived from the real font."""

    def test_the_font_on_this_machine_gives_the_measured_cell(self, surface):
        # The one thing only a real font can answer: that Menlo 12 here is
        # the 10 x 19 cell S-1 measured, AMEND-6 re-measured on Tk 9.0.4, and
        # the plan's runtime table records.
        # The arithmetic that turns it into 400 x 570 is test_metrics.py's.
        assert surface.metrics == MEASURED_MENLO_12
        assert surface.metrics_match_measurement()

    def test_the_canvas_is_the_size_the_metrics_computed(self, surface):
        # The join.  Whatever the metrics say, the canvas is that; this test
        # fails if and only if the painter stopped using them.
        width, height = surface.metrics.window_pixel_size()
        assert int(surface.widget.cget("width")) == width
        assert int(surface.widget.cget("height")) == height

    def test_the_surface_reports_the_same_size_as_its_canvas(self, surface):
        assert surface.pixel_size == (
            int(surface.widget.cget("width")),
            int(surface.widget.cget("height")),
        )

    def test_nothing_is_lost_to_a_border_or_a_focus_ring(self, surface):
        # Two pixels of highlight ring would make the grid not fit the window.
        assert int(surface.widget.cget("highlightthickness")) == 0
        assert int(surface.widget.cget("borderwidth")) == 0

    def test_the_ground_is_black(self, surface):
        assert surface.ground == palette.GROUND
        assert surface.widget.cget("background") == palette.GROUND

    def test_the_font_asked_for_is_the_font_resolved(self, surface):
        # A substitution would silently change the window size.  S-1 measured
        # that Menlo is present; this is the test that notices if it stops
        # being, rather than the window quietly coming out a different size.
        family, size = surface.font_description
        assert family == "Menlo"
        assert size == 12

    def test_the_size_in_use_keeps_an_exact_cell_grid(self, surface):
        assert surface.exact_cell_grid()


class TestEveryGlyphTheGameDrawsSharesOneCellWidth:
    """If one glyph were wider than a letter, the grid would not be a grid.

    S-1 measured this and recorded it in a finding; nothing re-ran it.  It
    belongs to the cell-metrics responsibility, which is WI-5's, so it is
    pinned here.
    """

    def test_every_wall_glyph_is_one_cell_wide(self, surface):
        font = tkinter.font.Font(
            root=surface.widget, family="Menlo", size=12
        )
        one_cell = font.measure("M")
        wrong = {
            glyph: font.measure(glyph)
            for glyph in sorted(ALL_WALL_GLYPHS)
            if font.measure(glyph) != one_cell
        }
        assert wrong == {}, "these glyphs are not one cell wide: {}".format(wrong)

    def test_every_actor_and_dot_glyph_is_one_cell_wide(self, surface):
        font = tkinter.font.Font(root=surface.widget, family="Menlo", size=12)
        one_cell = font.measure("M")
        # The dot (SCRN-4) and the block glyphs the specimen draws the two
        # actors with (SCRN-5).
        drawn = ["▪", "█", "▐", "▌", "▗", "▖", "■"]
        wrong = {g: font.measure(g) for g in drawn if font.measure(g) != one_cell}
        assert wrong == {}, "these glyphs are not one cell wide: {}".format(wrong)

    def test_the_cell_width_is_not_zero(self, surface):
        # Keeps the two tests above from passing because everything measured 0.
        font = tkinter.font.Font(root=surface.widget, family="Menlo", size=12)
        assert font.measure("M") == surface.metrics.advance > 0


class TestScrnTwoNothingButGlyphsAndFlatColour:
    """SCRN-2: everything is drawn from characters; there are no images."""

    def test_a_new_surface_holds_only_text_and_rectangles(self, surface):
        assert surface.item_types() == PERMITTED_ITEM_TYPES

    def test_a_fully_painted_surface_holds_only_text_and_rectangles(self, surface):
        surface.present(a_full_field())
        assert surface.item_types() == PERMITTED_ITEM_TYPES

    def test_no_item_is_an_image_a_line_or_a_shape(self, surface):
        surface.present(a_full_field())
        forbidden = {"image", "bitmap", "line", "arc", "oval", "polygon", "window"}
        assert surface.item_types() & forbidden == set()

    def test_there_are_exactly_two_items_per_cell(self, surface):
        assert surface.item_count() == 2 * COLUMNS * ROWS == 2400

    def test_the_only_way_to_change_the_picture_takes_a_field(self, surface):
        with pytest.raises(TypeError):
            surface.present("not a field")

    def test_a_background_is_a_flat_colour_with_no_outline(self, surface):
        # An outline is a drawn stroke, which is the thing SCRN-2 rules out.
        first = surface.widget.find_all()[0]
        assert surface.widget.type(first) == "rectangle"
        assert float(surface.widget.itemcget(first, "width")) == 0.0


class TestThePictureIsWhatTheFieldSaid:
    """The join: a field of glyph-and-colour becomes exactly that picture."""

    def test_a_presented_cell_is_on_the_canvas(self, surface):
        field = Field()
        field[4, 6] = Cell("═", palette.WALL)
        surface.present(field)
        assert surface.shown_cell(4, 6) == Cell("═", palette.WALL)

    def test_every_cell_of_a_full_frame_reaches_the_canvas(self, surface):
        field = a_full_field()
        surface.present(field)
        wrong = [
            (column, row)
            for column, row, cell in field.cells()
            if surface.shown_cell(column, row) != cell
        ]
        assert wrong == []

    def test_a_row_reads_back_as_it_was_written(self, surface):
        field = Field()
        field.write(1, 29, "score 0    arrows, q quits", palette.STATUS)
        surface.present(field)
        assert surface.shown_row(29) == field.row_text(29)

    def test_a_cell_changed_between_frames_changes_on_the_canvas(self, surface):
        field = Field()
        field[4, 6] = Cell("█", palette.PLAYER)
        surface.present(field)
        field[4, 6] = Cell("█", palette.GHOST)
        surface.present(field)
        assert surface.shown_cell(4, 6).colour == palette.GHOST

    def test_a_cell_cleared_between_frames_clears_on_the_canvas(self, surface):
        field = Field()
        field[4, 6] = Cell("█", palette.PLAYER)
        surface.present(field)
        field[4, 6] = Cell()
        surface.present(field)
        assert surface.shown_cell(4, 6) == Cell()

    def test_a_background_colour_reaches_the_canvas(self, surface):
        field = Field()
        field[2, 3] = Cell(" ", palette.GROUND, background=palette.WALL)
        surface.present(field)
        assert surface.shown_cell(2, 3).background == palette.WALL

    def test_presenting_the_same_field_twice_leaves_the_same_picture(self, surface):
        field = a_full_field()
        surface.present(field)
        first = [surface.shown_cell(c, r) for c, r, _ in field.cells()]
        surface.present(field)
        assert [surface.shown_cell(c, r) for c, r, _ in field.cells()] == first

    def test_going_back_to_a_blank_field_blanks_every_cell(self, surface):
        surface.present(a_full_field())
        surface.present(Field())
        not_blank = [
            (column, row)
            for column in range(COLUMNS)
            for row in range(ROWS)
            if not surface.shown_cell(column, row).is_blank()
        ]
        assert not_blank == []

    def test_the_corners_are_painted(self, surface):
        field = Field()
        corners = [(0, 0), (COLUMNS - 1, 0), (0, ROWS - 1), (COLUMNS - 1, ROWS - 1)]
        for index, (column, row) in enumerate(corners):
            field[column, row] = Cell(str(index), palette.STATUS)
        surface.present(field)
        assert [surface.shown_cell(c, r).glyph for c, r in corners] == [
            "0",
            "1",
            "2",
            "3",
        ]

    @pytest.mark.parametrize("column, row", [(COLUMNS, 0), (0, ROWS), (-1, 0)])
    def test_reading_a_cell_off_the_grid_raises(self, surface, column, row):
        with pytest.raises(IndexError):
            surface.shown_cell(column, row)


class TestScrnSevenTheFlickerHalf:
    """SCRN-7: *"the picture is redrawn as things move, without flicker"*.

    Flicker is a picture torn down and rebuilt.  These tests ask whether it
    ever was — which is the mechanism, not a proxy for it.
    """

    def test_the_canvas_items_are_the_same_objects_after_a_repaint(self, surface):
        before = surface.item_ids()
        surface.present(a_full_field())
        assert surface.item_ids() == before

    def test_the_canvas_items_survive_many_repaints(self, surface):
        before = surface.item_ids()
        for index in range(10):
            field = Field()
            field[index, index] = Cell("█", palette.PLAYER)
            surface.present(field)
        assert surface.item_ids() == before

    def test_the_canvas_is_not_emptied_to_go_from_a_full_frame_to_a_blank_one(
        self, surface
    ):
        # Full picture to blank picture is the case a delete-and-recreate
        # painter would implement by emptying the canvas.  Item *identity* is
        # what catches it: a count would not, because such a painter puts the
        # same number of items back.
        before = surface.item_ids()
        surface.present(a_full_field())
        surface.present(Field())
        assert surface.item_ids() == before

    def test_changing_one_cell_does_not_disturb_another(self, surface):
        field = a_full_field()
        surface.present(field)
        unchanged = surface.shown_cell(20, 20)
        field[0, 0] = Cell("Z", palette.STATUS)
        surface.present(field)
        assert surface.shown_cell(20, 20) == unchanged
        assert surface.shown_cell(0, 0).glyph == "Z"

    def test_a_repaint_from_scratch_gives_the_same_picture(self, surface):
        # `repaint` exists for a canvas disturbed from outside.  It must not
        # be a different painter with a different answer.
        field = a_full_field()
        surface.present(field)
        before = [surface.shown_cell(c, r) for c, r, _ in field.cells()]
        surface.repaint()
        assert [surface.shown_cell(c, r) for c, r, _ in field.cells()] == before

    def test_a_repaint_restores_a_cell_disturbed_from_outside(self, surface):
        # The case the method exists for.  The canvas is changed behind the
        # painter's back — as a display change or a stray caller would — and
        # `repaint` has to put it right.  A cell the painter believes is
        # *blank* is the hard case, because a diff would skip it.
        field = a_full_field()
        field[3, 4] = Cell()
        surface.present(field)
        # item_ids() is every background, then every glyph, both row-major.
        every_item = surface.item_ids()
        glyph_of_3_4 = every_item[len(every_item) // 2 + 4 * COLUMNS + 3]
        surface.widget.itemconfigure(glyph_of_3_4, text="?", fill=palette.STATUS)
        # The disturbance landed where the test meant it to, which is what
        # makes the assertion after the repaint mean anything.
        assert surface.shown_cell(3, 4).glyph == "?"
        surface.repaint()
        assert surface.shown_cell(3, 4) == Cell()


class TestScrnSevenTheCaretHalf:
    """SCRN-7: *"and the text cursor is never visible"*."""

    def test_a_caret_cannot_appear(self, surface):
        assert surface.caret_is_impossible()

    def test_the_canvas_refuses_the_keyboard_focus(self, surface):
        assert str(surface.widget.cget("takefocus")) in ("0", "")

    def test_no_canvas_item_holds_the_focus(self, surface):
        surface.present(a_full_field())
        assert not surface.widget.focus()

    def test_the_insertion_caret_has_no_width(self, surface):
        assert int(surface.widget.cget("insertwidth")) == 0

    def test_the_surface_creates_no_widget_that_edits_text(self, surface):
        classes = surface.descendant_widget_classes()
        assert classes == frozenset({"Canvas"})
        assert classes & {"Entry", "Text", "TEntry", "Spinbox", "TCombobox"} == set()

    def test_the_focus_stays_away_after_repaints(self, surface):
        for _ in range(3):
            surface.present(a_full_field())
            surface.present(Field())
        assert surface.caret_is_impossible()


class TestBuildingASurface:
    """What a surface refuses at construction, and what it reports."""

    def test_a_ground_that_is_not_a_colour_is_refused(self, tk_root):
        with pytest.raises(ValueError):
            GridSurface(tk_root, ground="black")

    def test_a_surface_can_be_given_a_different_ground(self, tk_root):
        made = GridSurface(tk_root, ground="#102030")
        try:
            assert made.ground == "#102030"
            assert made.shown_cell(0, 0).background == "#102030"
        finally:
            made.widget.destroy()

    def test_a_different_font_size_gives_a_different_window(self, tk_root):
        made = GridSurface(tk_root, size=8)
        try:
            # AMEND-6's rescan: Menlo 8 is advance 7, linespace 13 on Tk 9.0.4.
            # (S-1 read 5 x 9 for it on Tk 8.5.9 — the same 4/3 the chosen size
            # moved by, which is why this test's numbers moved and the window's
            # did not.)
            assert made.metrics == CellMetrics(7, 13)
            assert made.pixel_size == (280, 390)
            assert not made.metrics_match_measurement()
        finally:
            made.widget.destroy()

    def test_a_surface_describes_itself(self, surface):
        assert "40 x 30 cells" in repr(surface)
        assert "400 x 570 px" in repr(surface)
