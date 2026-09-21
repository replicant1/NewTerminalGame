"""WIN-2 as arithmetic: 40 x 30 cells of the chosen font make a pixel rectangle.

These tests own the *derivation*.  ``tests/test_surface.py`` owns only the join
— that the canvas really is the size this arithmetic computed — and does not
re-derive any of it.
"""

from __future__ import annotations

import pytest

from terminal_game.presentation.metrics import (
    COLUMNS,
    EXACT_GRID_CEILING,
    FONT_FAMILY,
    FONT_SIZE,
    MEASURED_MENLO_12,
    ROWS,
    CellMetrics,
)


class TestTheGridIsFixed:
    """WIN-2 fixes the grid at 40 x 30, and it is not a parameter anywhere."""

    def test_the_grid_is_forty_by_thirty(self):
        assert (COLUMNS, ROWS) == (40, 30)

    def test_every_cell_of_the_grid_is_inside_it(self):
        outside = [
            (column, row)
            for column in range(COLUMNS)
            for row in range(ROWS)
            if not CellMetrics.in_grid(column, row)
        ]
        assert outside == []

    @pytest.mark.parametrize(
        "column, row",
        [
            (COLUMNS, 0),       # one past the right edge
            (0, ROWS),          # one below the bottom
            (-1, 0),            # negative indices do not wrap round
            (0, -1),
            (COLUMNS, ROWS),
            (999, 999),
        ],
    )
    def test_a_coordinate_off_the_grid_is_not_in_it(self, column, row):
        assert not CellMetrics.in_grid(column, row)

    @pytest.mark.parametrize(
        "column, row", [(COLUMNS, 0), (0, ROWS), (-1, 0), (0, -1)]
    )
    def test_asking_for_a_cell_off_the_grid_raises(self, column, row):
        metrics = CellMetrics(10, 19)
        with pytest.raises(IndexError):
            metrics.cell_origin(column, row)


class TestThePixelSize:
    """WIN-2's window size, derived from a cell size."""

    def test_the_measured_cell_gives_four_hundred_by_five_seventy(self):
        # The number S-1 measured and the plan's runtime table records.  This
        # is the derivation, not the measurement: given a 10 x 19 cell, a
        # 40 x 30 grid is 400 x 570 and could not be anything else.
        assert MEASURED_MENLO_12.window_pixel_size() == (400, 570)

    def test_the_measured_cell_is_ten_by_nineteen(self):
        assert (MEASURED_MENLO_12.advance, MEASURED_MENLO_12.linespace) == (10, 19)

    @pytest.mark.parametrize(
        "advance, linespace, expected",
        [
            (5, 9, (200, 270)),      # Menlo 8 as S-1 read it on Tk 8.5.9
            (7, 13, (280, 390)),     # Menlo 8 as AMEND-6 reads it on Tk 9.0.4
            (10, 19, (400, 570)),    # the cell in use, under both
            (14, 28, (560, 840)),    # a cell twice the width of a Menlo 8
            (1, 1, (40, 30)),        # the degenerate but legal cell
        ],
    )
    def test_the_window_is_the_cell_times_the_grid(self, advance, linespace, expected):
        assert CellMetrics(advance, linespace).window_pixel_size() == expected

    def test_a_grid_of_no_cells_has_no_pixels(self):
        assert CellMetrics(10, 19).pixel_size(0, 0) == (0, 0)

    def test_a_negative_grid_is_refused(self):
        with pytest.raises(ValueError):
            CellMetrics(10, 19).pixel_size(-1, 30)


class TestCellPlacement:
    """Where each cell sits, and that the cells tile the rectangle exactly."""

    def test_the_first_cell_starts_at_the_origin(self):
        assert CellMetrics(10, 19).cell_origin(0, 0) == (0, 0)

    def test_a_cell_starts_where_the_one_before_it_ends(self):
        metrics = CellMetrics(10, 19)
        for column in range(1, COLUMNS):
            previous_right = metrics.cell_bounds(column - 1, 0)[2]
            this_left = metrics.cell_origin(column, 0)[0]
            assert this_left == previous_right, (
                "column {} starts at {} but column {} ended at {}: the cells "
                "either overlap or leave a gap".format(
                    column, this_left, column - 1, previous_right
                )
            )

    def test_a_row_starts_where_the_one_above_it_ends(self):
        metrics = CellMetrics(10, 19)
        for row in range(1, ROWS):
            previous_bottom = metrics.cell_bounds(0, row - 1)[3]
            this_top = metrics.cell_origin(0, row)[1]
            assert this_top == previous_bottom

    def test_the_last_cell_ends_exactly_at_the_window_edge(self):
        metrics = MEASURED_MENLO_12
        _, _, right, bottom = metrics.cell_bounds(COLUMNS - 1, ROWS - 1)
        assert (right, bottom) == metrics.window_pixel_size()

    def test_every_cell_has_a_different_origin(self):
        metrics = MEASURED_MENLO_12
        origins = {
            metrics.cell_origin(column, row)
            for column in range(COLUMNS)
            for row in range(ROWS)
        }
        assert len(origins) == COLUMNS * ROWS


class TestACellMustHaveASize:
    """A zero or negative cell would collapse the grid to a single point."""

    @pytest.mark.parametrize("advance", [0, -1, -10])
    def test_a_cell_with_no_width_is_refused(self, advance):
        with pytest.raises(ValueError):
            CellMetrics(advance, 19)

    @pytest.mark.parametrize("linespace", [0, -1, -19])
    def test_a_cell_with_no_height_is_refused(self, linespace):
        with pytest.raises(ValueError):
            CellMetrics(10, linespace)


class TestTheFontConstants:
    """The font is fixed by S-1's measurement, and the ceiling is the reason."""

    def test_the_family_is_the_one_that_owns_every_glyph(self):
        assert FONT_FAMILY == "Menlo"

    def test_the_size_is_at_the_exact_grid_ceiling(self):
        # AMEND-6 measured that a 40-character row lines up with 40 placed
        # cells only at size 12 and below on Tk 9.0.4.  The size in use is the
        # largest that still does, which is why it is 12 and not 13 or 15.
        # (S-1 measured the same property on Tk 8.5.9 and found the ceiling at
        # 16; both readings describe the same cell — see metrics.py.)
        assert FONT_SIZE == EXACT_GRID_CEILING

    def test_the_size_is_not_above_the_ceiling(self):
        assert FONT_SIZE <= EXACT_GRID_CEILING


class TestMetricsCompareByValue:
    """Two metrics with the same cell are the same metrics."""

    def test_the_same_cell_compares_equal(self):
        assert CellMetrics(10, 19) == CellMetrics(10, 19)

    def test_a_different_cell_compares_unequal(self):
        assert CellMetrics(10, 19) != CellMetrics(10, 20)

    def test_metrics_can_be_put_in_a_set(self):
        assert len({CellMetrics(10, 19), CellMetrics(10, 19), CellMetrics(11, 22)}) == 2

    def test_metrics_are_not_equal_to_other_things(self):
        assert CellMetrics(10, 19) != (10, 19)
