# -*- coding: utf-8 -*-
"""WI-16 — the look, seen.

Most of this work item is a person looking at a screen, and that is the
point. What a machine can check is here, and it is two things:

* **the colour vocabulary reaching the surface unchanged** — the picture
  itself is already pinned by WI-12 and the glyphs by WI-8, so this item's
  automated tests own only the journey from the requirement's name for a
  colour to the value the surface paints with;
* **that the tool cannot run unbounded** and cannot leave a window behind.

No test here opens a window. The surface is driven through the recording
double, and only ``the_look.main`` touches the real toolkit.
"""

from __future__ import annotations

import unittest

from terminal_game.presentation.frame import (
    FRAME_COLUMNS,
    FRAME_ROWS,
    MAZE_ROWS,
    STATUS_ROW,
    Colour,
    Frame,
)
from terminal_game.presentation.frame_composer import (
    DOT_GLYPH,
    GHOST_MOTIF,
    PLAYER_MOTIF,
)
from terminal_game.presentation.wall_glyphs import wall_layer
from terminal_game.shell.grid_surface import (
    FONT_POINT_SIZE,
    PALETTE,
    CellMetrics,
    CharacterGridSurface,
)

from tests.doubles import RecordingCanvas, assert_surface_shows
from tools.the_look import (
    DEFAULT_SECONDS,
    FRAME_FOR_VIEW,
    GAME_SEED,
    THE_THREE_QUESTIONS,
    VIEWS,
    colour_frame,
    game_frame,
    joinery_frame,
    lattice_maze,
    parse_options,
)

MEASURED = CellMetrics(width=10, height=19)


def a_surface():
    canvas = RecordingCanvas()
    return canvas, CharacterGridSurface(canvas, MEASURED)


class EveryViewIsAWellFormedPicture(unittest.TestCase):
    """Whatever a person is shown, it is 30 x 40 of characters."""

    def test_there_are_three_views_and_each_builds_a_frame(self):
        self.assertEqual({"game", "joinery", "colours"}, set(VIEWS))
        self.assertEqual(set(VIEWS), set(FRAME_FOR_VIEW))

    def test_each_view_is_thirty_rows_of_forty_characters(self):
        for view, build in FRAME_FOR_VIEW.items():
            frame = build()

            self.assertIsInstance(frame, Frame, view)
            lines = frame.to_text().split("\n")
            self.assertEqual(FRAME_ROWS, len(lines), view)
            self.assertEqual({FRAME_COLUMNS}, {len(l) for l in lines}, view)

    def test_each_view_uses_only_colours_from_the_closed_vocabulary(self):
        for view, build in FRAME_FOR_VIEW.items():
            frame = build()

            for row in range(FRAME_ROWS):
                for column in range(FRAME_COLUMNS):
                    self.assertIsInstance(
                        frame.cell_at(row, column).colour, Colour, view
                    )

    def test_no_view_is_blank(self):
        # A view that had quietly become empty would still be 30 x 40 and
        # would still paint; it would just show a person nothing. The floor
        # is well under the smallest view (the colour card, at 96 cells) and
        # well over nothing.
        for view, build in FRAME_FOR_VIEW.items():
            drawn = sum(
                1
                for row in range(FRAME_ROWS)
                for column in range(FRAME_COLUMNS)
                if build().cell_at(row, column).glyph != " "
            )

            self.assertGreater(drawn, 40, view)


class TheColoursReachTheSurfaceUnchanged(unittest.TestCase):
    """What this item's automated tests own, per the plan.

    The picture is pinned by WI-12 and the glyphs by WI-8. What is left, and
    what no other item checks, is that a colour the requirements *name*
    arrives at the surface as the value it is supposed to be painted in.
    """

    def test_every_view_survives_the_journey_to_the_surface(self):
        for view, build in FRAME_FOR_VIEW.items():
            canvas, surface = a_surface()
            frame = build()

            surface.paint(frame)

            assert_surface_shows(self, canvas, surface, frame)

    def test_each_kind_of_thing_reaches_the_surface_in_its_own_colour(self):
        canvas, surface = a_surface()
        frame = game_frame()

        surface.paint(frame)

        painted = {}
        for item in canvas.live_items():
            painted.setdefault(item.options["fill"], set()).add(
                item.options["text"]
            )

        # SCRN-4, SCRN-5, SCRN-3: the glyph each requirement names turns up
        # under the colour that requirement names, on the real surface.
        self.assertIn(DOT_GLYPH, painted[PALETTE[Colour.DOT_GOLD]])
        for glyph in PLAYER_MOTIF:
            self.assertIn(glyph, painted[PALETTE[Colour.PLAYER_YELLOW]])
        for glyph in GHOST_MOTIF:
            self.assertIn(glyph, painted[PALETTE[Colour.GHOST_PINK]])
        self.assertIn("║", painted[PALETTE[Colour.WALL_BLUE]])

    def test_the_status_row_reaches_the_surface_in_cyan(self):
        canvas, surface = a_surface()

        surface.paint(game_frame())

        for item in canvas.live_items():
            row, _ = surface.geometry.cell_at_pixel(*item.coordinates)
            if row == STATUS_ROW:
                self.assertEqual(
                    PALETTE[Colour.STATUS_CYAN], item.options["fill"]
                )

    def test_the_five_visible_colours_are_all_different_on_the_surface(self):
        # SCRN-5 asks that the two actors be told apart by colour; there is
        # no point showing a person two hues that are the same value.
        _, surface = a_surface()
        visible = [c for c in Colour if c is not Colour.GROUND_BLACK]

        painted = {surface.colour_of(colour) for colour in visible}

        self.assertEqual(len(visible), len(painted))

    def test_nothing_but_characters_is_ever_shown_to_the_person(self):
        for view, build in FRAME_FOR_VIEW.items():
            canvas, surface = a_surface()

            surface.paint(build())

            self.assertEqual({"text"}, canvas.kinds_drawn(), view)


class TheJoineryViewShowsEveryJunction(unittest.TestCase):
    """SCRN-3 — the question a measurement cannot close."""

    def test_the_lattice_produces_every_glyph_wi_eight_can_draw(self):
        from terminal_game.presentation import wall_glyphs

        drawn = {
            cell.glyph
            for row in wall_layer(lattice_maze())
            for cell in row
            if cell.glyph != " "
        }

        # Every junction the resolver can produce, including the crossing
        # the specimen picture happens not to contain. Named from WI-8's own
        # constants rather than retyped here.
        for glyph in (
            wall_glyphs.HORIZONTAL_GLYPH,
            wall_glyphs.VERTICAL_GLYPH,
            wall_glyphs.CROSSING_GLYPH,
        ):
            self.assertIn(glyph, drawn)
        self.assertGreaterEqual(len(drawn), 11)

    def test_the_joinery_view_is_all_wall_blue_above_the_status_row(self):
        frame = joinery_frame()

        for row in range(MAZE_ROWS):
            for column in range(FRAME_COLUMNS):
                cell = frame.cell_at(row, column)
                if cell.glyph != " ":
                    self.assertEqual(Colour.WALL_BLUE, cell.colour)

    def test_the_joinery_view_declares_no_glyph_of_its_own(self):
        import inspect

        import tools.the_look as the_look

        source = inspect.getsource(the_look)
        executable = "".join(source.split('"""')[::2])

        for glyph in "╔╗╚╝╠╣╦╩╬■":
            self.assertNotIn(
                glyph,
                executable,
                "the tool has declared the wall glyph {0!r}, which is "
                "WI-8's".format(glyph),
            )


class TheColourViewNamesWhatItShows(unittest.TestCase):
    def test_it_labels_each_colour_with_the_thing_it_belongs_to(self):
        text = colour_frame().to_text()

        for label in ("wall", "dot", "you", "ghost"):
            self.assertIn(label, text)

    def test_it_shows_both_actor_motifs_so_the_shapes_can_be_compared(self):
        text = colour_frame().to_text()

        self.assertIn(PLAYER_MOTIF, text)
        self.assertIn(GHOST_MOTIF, text)

    def test_row_twenty_nine_is_the_real_status_line_not_a_sample(self):
        from terminal_game.domain.game_state import Outcome
        from terminal_game.presentation.status_line import status_row

        for build in (colour_frame, joinery_frame):
            self.assertEqual(
                list(status_row(0, Outcome.UNDECIDED)),
                list(build().rows[STATUS_ROW]),
            )


class TheGameViewIsTheRealThing(unittest.TestCase):
    def test_it_is_the_real_composer_over_a_real_generated_maze(self):
        # WI-22a.  This used to rebuild the picture out of the composer and
        # the status line and compare against that, which reimplemented the
        # tool's own job inside the test.  What the tool owes is that the
        # game view is **Presentation's** picture of the seed's opening
        # position — not a picture the tool assembled for itself — and that
        # is the whole of what is asserted.
        import random

        from terminal_game.domain.maze_generator import generate_maze
        from terminal_game.domain.opening_position import opening_position
        from terminal_game.presentation.picture import frame_for

        state = opening_position(generate_maze(random.Random(GAME_SEED)))

        self.assertEqual(frame_for(state), game_frame())

    def test_the_same_seed_shows_the_same_picture_to_everybody(self):
        self.assertEqual(game_frame().to_text(), game_frame().to_text())

    def test_both_actors_are_on_screen_exactly_once(self):
        text = "\n".join(game_frame().to_text().split("\n")[:MAZE_ROWS])

        self.assertEqual(1, text.count(PLAYER_MOTIF))
        self.assertEqual(1, text.count(GHOST_MOTIF))


class TheToolCannotRunUnbounded(unittest.TestCase):
    """Section 4: never launch something that blocks forever."""

    def test_by_default_it_shows_every_view_once_at_the_chosen_size(self):
        options = parse_options([])

        self.assertEqual(VIEWS, options.views)
        self.assertEqual((FONT_POINT_SIZE,), options.sizes)
        self.assertEqual(DEFAULT_SECONDS, options.seconds)
        self.assertEqual(len(VIEWS), options.windows)

    def test_the_default_deadline_is_positive_and_short(self):
        self.assertGreater(DEFAULT_SECONDS, 0)
        self.assertLessEqual(DEFAULT_SECONDS, 30)

    def test_a_deadline_of_zero_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--seconds", "0"])

    def test_a_negative_deadline_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--seconds", "-1"])

    def test_one_view_can_be_asked_for_on_its_own(self):
        options = parse_options(["--view", "joinery"])

        self.assertEqual(("joinery",), options.views)
        self.assertEqual(1, options.windows)

    def test_a_view_that_does_not_exist_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--view", "nonesuch"])

    def test_several_sizes_open_one_window_each_per_view(self):
        options = parse_options(["--sizes", "14,16,18,20", "--view", "game"])

        self.assertEqual((14, 16, 18, 20), options.sizes)
        self.assertEqual(4, options.windows)

    def test_a_font_size_of_zero_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--sizes", "0"])

    def test_asking_for_no_views_at_all_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--view", ""])

    def test_every_run_is_bounded_however_it_is_configured(self):
        for argv in (
            [],
            ["--view", "game"],
            ["--sizes", "14,20"],
            ["--seconds", "1"],
            ["--json"],
        ):
            options = parse_options(argv)

            self.assertGreater(options.seconds, 0, argv)
            self.assertGreater(options.windows, 0, argv)

    def test_the_three_questions_are_put_to_the_person_in_words(self):
        # The tool is worth nothing if it opens a window and does not say
        # what the person is meant to be looking for.
        asked = " ".join(THE_THREE_QUESTIONS)

        self.assertIn("SCRN-3", asked)
        self.assertIn("A4", asked)
        self.assertIn("A1", asked)
        self.assertIn("Terminal Game", asked)


class TheToolIsNotPartOfTheSuite(unittest.TestCase):
    def test_importing_it_constructs_no_toolkit_interpreter(self):
        import tkinter

        import tools.the_look  # noqa: F401 - the import is the test

        self.assertIsNone(tkinter._default_root)

    def test_building_every_view_constructs_no_toolkit_interpreter(self):
        import tkinter

        for build in FRAME_FOR_VIEW.values():
            build()

        self.assertIsNone(tkinter._default_root)


if __name__ == "__main__":
    unittest.main()
