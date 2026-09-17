"""The 40 x 30 field of glyph-and-colour, and SCRN-2 enforced in the data.

SCRN-2 — *"everything is drawn from characters, there are no images"* — is a
rule under candidate 2 rather than a property of the medium, so these tests
own the half of it that can be made a fact: a cell is one character and two
colours, and there is no shape a cell can take that could carry anything else.
``tests/test_surface.py`` owns the other half, which is that nothing but text
and flat rectangles ever reaches the canvas.
"""

from __future__ import annotations

import pytest

from terminal_game.presentation import palette
from terminal_game.presentation.field import BLANK, Cell, Field
from terminal_game.presentation.metrics import COLUMNS, ROWS


class TestACellIsOneCharacter:
    """SCRN-2, in the data: there is nothing for an image to travel in."""

    def test_a_cell_holds_one_character(self):
        assert Cell("A").glyph == "A"

    def test_a_box_drawing_character_is_one_character(self):
        assert Cell("═").glyph == "═"

    @pytest.mark.parametrize("glyph", ["", "AB", "  ", "══", "a" * 40])
    def test_anything_other_than_one_character_is_refused(self, glyph):
        with pytest.raises(ValueError):
            Cell(glyph)

    @pytest.mark.parametrize("glyph", [None, 65, b"A", ["A"]])
    def test_something_that_is_not_a_string_is_refused(self, glyph):
        with pytest.raises(TypeError):
            Cell(glyph)

    @pytest.mark.parametrize("colour", ["pink", "#fff", "", None])
    def test_a_colour_that_is_not_a_colour_is_refused(self, colour):
        with pytest.raises(ValueError):
            Cell("A", colour=colour)

    @pytest.mark.parametrize("background", ["pink", "#fff", "", None])
    def test_a_background_that_is_not_a_colour_is_refused(self, background):
        with pytest.raises(ValueError):
            Cell("A", background=background)

    def test_a_cell_defaults_to_a_space_on_the_ground(self):
        cell = Cell()
        assert cell.glyph == BLANK
        assert cell.background == palette.GROUND
        assert cell.is_blank()

    def test_a_cell_with_something_in_it_is_not_blank(self):
        assert not Cell("▪", colour=palette.DOT).is_blank()

    def test_a_cell_with_a_coloured_background_is_not_blank(self):
        assert not Cell(BLANK, background=palette.WALL).is_blank()


class TestCellsCompareByValue:
    """A painter asks "did this cell change?" and wants an answer about the picture."""

    def test_two_cells_with_the_same_content_are_equal(self):
        assert Cell("A", palette.WALL) == Cell("A", palette.WALL)

    @pytest.mark.parametrize(
        "other",
        [
            Cell("B", palette.WALL),
            Cell("A", palette.DOT),
            Cell("A", palette.WALL, background=palette.WALL),
        ],
    )
    def test_a_cell_differing_in_anything_is_unequal(self, other):
        assert Cell("A", palette.WALL) != other

    def test_a_cell_is_not_equal_to_a_tuple_of_its_parts(self):
        assert Cell("A", palette.WALL) != ("A", palette.WALL, palette.GROUND)


class TestTheFieldIsFortyByThirty:
    """WIN-2 fixes the grid; no other shape is representable."""

    def test_a_new_field_is_entirely_blank(self):
        field = Field()
        assert all(cell.is_blank() for _, _, cell in field.cells())

    def test_a_field_has_exactly_twelve_hundred_cells(self):
        assert len(list(Field().cells())) == COLUMNS * ROWS == 1200

    def test_every_row_is_forty_characters(self):
        assert [len(row) for row in Field().rows()] == [COLUMNS] * ROWS

    def test_there_are_thirty_rows(self):
        assert len(list(Field().rows())) == ROWS

    @pytest.mark.parametrize(
        "column, row", [(COLUMNS, 0), (0, ROWS), (-1, 0), (0, -1), (40, 30)]
    )
    def test_reading_off_the_grid_raises(self, column, row):
        with pytest.raises(IndexError):
            Field()[column, row]

    @pytest.mark.parametrize("column, row", [(COLUMNS, 0), (0, ROWS), (-1, 0)])
    def test_writing_off_the_grid_raises(self, column, row):
        with pytest.raises(IndexError):
            Field()[column, row] = Cell("A")

    def test_only_cells_can_be_put_in_a_field(self):
        with pytest.raises(TypeError):
            Field()[0, 0] = "A"


class TestReadingAndWritingCells:

    def test_a_cell_written_is_the_cell_read_back(self):
        field = Field()
        cell = Cell("═", palette.WALL)
        field[7, 11] = cell
        assert field[7, 11] == cell

    def test_writing_one_cell_leaves_its_neighbours_alone(self):
        field = Field()
        field[7, 11] = Cell("═", palette.WALL)
        for column, row in [(6, 11), (8, 11), (7, 10), (7, 12)]:
            assert field[column, row].is_blank()

    def test_the_corners_are_reachable(self):
        field = Field()
        corners = [(0, 0), (COLUMNS - 1, 0), (0, ROWS - 1), (COLUMNS - 1, ROWS - 1)]
        for index, (column, row) in enumerate(corners):
            field[column, row] = Cell(str(index), palette.STATUS)
        for index, (column, row) in enumerate(corners):
            assert field[column, row].glyph == str(index)

    def test_rows_and_columns_are_not_transposed(self):
        # A 40 x 30 grid would accept (29, 39) if the two were swapped.
        field = Field()
        field[39, 29] = Cell("X")
        assert field[39, 29].glyph == "X"
        with pytest.raises(IndexError):
            field[29, 39]


class TestWritingText:
    """The convenience WI-12's status line and WI-4's wall runs both want."""

    def test_text_goes_into_consecutive_cells(self):
        field = Field()
        field.write(0, 29, "score 0", palette.STATUS)
        assert field.row_text(29) == "score 0".ljust(COLUMNS)

    def test_text_is_written_at_the_column_asked_for(self):
        field = Field()
        field.write(3, 5, "abc", palette.STATUS)
        assert field.row_text(5) == "   abc" + " " * (COLUMNS - 6)

    def test_every_character_written_carries_the_colour(self):
        field = Field()
        field.write(0, 0, "abc", palette.STATUS)
        assert [field[c, 0].colour for c in range(3)] == [palette.STATUS] * 3

    def test_text_running_off_the_end_of_the_row_raises(self):
        field = Field()
        with pytest.raises(IndexError):
            field.write(COLUMNS - 2, 0, "abc", palette.STATUS)

    def test_a_row_that_exactly_fills_the_width_is_allowed(self):
        field = Field()
        field.write(0, 0, "x" * COLUMNS, palette.STATUS)
        assert field.row_text(0) == "x" * COLUMNS

    def test_writing_nothing_changes_nothing(self):
        field = Field()
        field.write(5, 5, "", palette.STATUS)
        assert field == Field()


class TestWhatChangedBetweenTwoFields:
    """What the painter uses to touch only the cells that moved."""

    def test_two_identical_fields_differ_nowhere(self):
        assert list(Field().differences(Field())) == []

    def test_one_changed_cell_is_the_only_difference(self):
        after = Field()
        after[4, 6] = Cell("█", palette.PLAYER)
        assert [(c, r) for c, r, _ in after.differences(Field())] == [(4, 6)]

    def test_the_difference_carries_the_new_cell(self):
        after = Field()
        new = Cell("█", palette.PLAYER)
        after[4, 6] = new
        assert [cell for _, _, cell in after.differences(Field())] == [new]

    def test_a_cell_changed_back_is_not_a_difference(self):
        after = Field()
        after[4, 6] = Cell("█", palette.PLAYER)
        after[4, 6] = Cell()
        assert list(after.differences(Field())) == []

    def test_differences_are_reported_row_major(self):
        after = Field()
        for column, row in [(9, 2), (1, 2), (5, 0)]:
            after[column, row] = Cell("X")
        assert [(c, r) for c, r, _ in after.differences(Field())] == [
            (5, 0),
            (1, 2),
            (9, 2),
        ]

    def test_everything_differs_when_everything_changed(self):
        after = Field()
        for column in range(COLUMNS):
            for row in range(ROWS):
                after[column, row] = Cell("X")
        assert len(list(after.differences(Field()))) == COLUMNS * ROWS


class TestASnapshotIsFrozen:
    """The painter holds one of these between frames; it must not be a back door."""

    def test_a_snapshot_has_one_entry_per_cell(self):
        assert len(Field().snapshot()) == COLUMNS * ROWS

    def test_a_snapshot_does_not_change_when_the_field_does(self):
        field = Field()
        before = field.snapshot()
        field[0, 0] = Cell("X")
        assert before[0] == Cell()
        assert field.snapshot()[0] == Cell("X")

    def test_a_snapshot_cannot_be_written_to(self):
        with pytest.raises(TypeError):
            Field().snapshot()[0] = Cell("X")


class TestFieldsCompareByValue:

    def test_two_empty_fields_are_equal(self):
        assert Field() == Field()

    def test_a_field_with_a_cell_changed_is_unequal(self):
        other = Field()
        other[0, 0] = Cell("X")
        assert Field() != other

    def test_a_field_is_not_equal_to_its_rows(self):
        assert Field() != list(Field().rows())
