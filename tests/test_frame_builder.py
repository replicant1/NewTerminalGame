# -*- coding: utf-8 -*-
"""Frame composition — SCRN-1, SCRN-2, SCRN-4, SCRN-5, SCRN-7, MAZE-1, END-4, SCORE-4.

The centrepiece here is `TheSpecificationsOwnPictureTest`: the specification
contains a worked example of a game in progress, and this composes a state
that matches its maze and its two actors and compares the result **character
for character against the document**. All 29 rows, 1 073 cells of picture,
authored by a person before any of this code existed.

That single test is worth more than the rest put together, because it cannot
agree with a mistake this code also makes. The rest are here for the things it
cannot see: a picture drawn once says nothing about a dot that has been eaten,
about what happens when the two actors stand on the same square, or about the
frame being rebuilt rather than patched.

The picture is parsed by the helpers in `tests/test_wall_glyphs.py` rather
than by a second copy of the same code, so if the document is ever reformatted
both items fail together and neither drifts.
"""

from __future__ import annotations

import random
import unittest

from terminalgame.domain.game_state import GameState, Outcome, new_game
from terminalgame.domain.maze import CORRIDOR, NORTH, WALL, Maze
from terminalgame.domain.maze_generator import generate_maze
from terminalgame.presentation.frame_builder import (
    MazeWillNotFit,
    ACTOR_WIDTH,
    DOT,
    GHOST_GLYPH,
    HEIGHT,
    JOINER,
    MARGIN_WIDTH,
    MAZE_ROWS,
    PICTURE_WIDTH,
    PLAYER_GLYPH,
    STATUS_ROW,
    StatusLineTooWide,
    WIDTH,
    column_of,
    compose,
    joiner_column,
    picture_rows,
)
from terminalgame.presentation.wall_glyphs import WALL_COLOUR, wall_glyph
from terminalgame.screen.port import BLANK, Colour, Frame
from tests.test_wall_glyphs import (
    maze_from_picture,
    picture_glyphs,
    specification_picture,
)

# A maze small enough to write the expected picture out by hand.
SMALL = Maze.from_text(
    "#####\n"
    "#...#\n"
    "#.#.#\n"
    "#...#\n"
    "#####", wall="#")


def state_on(maze, player, ghost, dots=None, score=0,
             outcome=Outcome.PLAYING):
    if dots is None:
        dots = frozenset(maze.corridor_squares()) - {player}
    return GameState(maze=maze, player=player, ghost=ghost,
                     ghost_heading=NORTH, dots=frozenset(dots), score=score,
                     outcome=outcome)


class TheSpecificationsOwnPictureTest(unittest.TestCase):
    """Compose the document's worked example and compare it to the document."""

    PLAYER = (10, 13)
    GHOST = (1, 27)

    @classmethod
    def setUpClass(cls):
        cls.rows = specification_picture()
        cls.maze = maze_from_picture(picture_glyphs(cls.rows))
        cls.state = state_on(cls.maze, cls.PLAYER, cls.GHOST)
        cls.frame = compose(cls.state)

    def test_the_actors_are_where_the_picture_puts_them(self):
        # Pins the fixture. If the picture were edited and the actors moved,
        # the comparison below would fail with 29 confusing diffs instead of
        # this one clear statement.
        drawn = picture_glyphs(self.rows)
        self.assertEqual(PLAYER_GLYPH[1], drawn[self.PLAYER[1]][self.PLAYER[0]])
        self.assertEqual(GHOST_GLYPH[1], drawn[self.GHOST[1]][self.GHOST[0]])

    def test_every_maze_row_matches_the_document_character_for_character(self):
        composed = picture_rows(self.frame)
        self.assertEqual(MAZE_ROWS, len(composed))
        for index, (expected, got) in enumerate(zip(self.rows, composed)):
            self.assertEqual(expected, got,
                             u"row {0} of the composed picture differs from "
                             u"the specification".format(index))

    def test_it_is_the_whole_picture_and_not_a_lucky_prefix(self):
        # 29 rows of 37 columns, all of them compared above.
        self.assertEqual(MAZE_ROWS * PICTURE_WIDTH,
                         sum(len(row) for row in picture_rows(self.frame)))
        self.assertEqual(29 * 37, 1073)


class TheShapeOfTheFrameTest(unittest.TestCase):
    """SCRN-1 and MAZE-1 — 40 x 30, of which 37 columns are picture."""

    def setUp(self):
        self.frame = compose(new_game(3))

    def test_the_frame_is_exactly_forty_by_thirty(self):
        self.assertEqual(40, self.frame.width)
        self.assertEqual(30, self.frame.height)
        self.assertEqual((WIDTH, HEIGHT), (self.frame.width, self.frame.height))
        self.assertEqual(30, len(self.frame.text_rows()))
        for row in self.frame.text_rows():
            self.assertEqual(40, len(row))

    def test_the_maze_takes_the_top_twenty_nine_rows(self):
        self.assertEqual(29, MAZE_ROWS)
        self.assertEqual(29, STATUS_ROW)
        self.assertEqual(HEIGHT, MAZE_ROWS + 1)

    def test_thirty_seven_columns_of_picture_and_three_of_margin(self):
        # The architecture said 38 + 2 and was wrong; the plan corrected it to
        # 37 + 3. This is that correction, pinned.
        self.assertEqual(37, PICTURE_WIDTH)
        self.assertEqual(3, MARGIN_WIDTH)
        self.assertEqual(WIDTH, PICTURE_WIDTH + MARGIN_WIDTH)
        self.assertEqual(PICTURE_WIDTH, 2 * 19 - 1)

    def test_the_right_margin_is_blank_on_every_row(self):
        for row_index, row in enumerate(self.frame.text_rows()):
            margin = row[PICTURE_WIDTH:]
            self.assertEqual(BLANK * MARGIN_WIDTH, margin,
                             "row {0} wrote into the margin".format(row_index))

    def test_squares_are_two_columns_apart_starting_at_zero(self):
        self.assertEqual(0, column_of(0))
        self.assertEqual(36, column_of(18))
        self.assertEqual(1, joiner_column(0))
        self.assertEqual(35, joiner_column(17))

    def test_the_last_square_lands_inside_the_picture(self):
        self.assertLess(column_of(18), PICTURE_WIDTH)


class TheWallsTest(unittest.TestCase):
    """SCRN-3 carried into the frame, plus the joiner columns."""

    def setUp(self):
        self.maze = generate_maze(6)
        self.frame = compose(state_on(self.maze, player=(1, 1), ghost=(17, 27)))

    def test_every_wall_square_carries_its_glyph_in_its_own_column(self):
        for (x, y) in self.maze.squares():
            if not self.maze.is_wall(x, y):
                continue
            cell = self.frame.cell(column_of(x), y)
            self.assertEqual(wall_glyph(self.maze, x, y), cell.character, (x, y))
            self.assertEqual(WALL_COLOUR, cell.colour, (x, y))

    def test_two_adjacent_wall_squares_are_joined_and_nothing_else_is(self):
        for y in range(self.maze.height):
            for x in range(self.maze.width - 1):
                both = self.maze.is_wall(x, y) and self.maze.is_wall(x + 1, y)
                cell = self.frame.cell(joiner_column(x), y)
                if both:
                    self.assertEqual(JOINER, cell.character, (x, y))
                    self.assertEqual(WALL_COLOUR, cell.colour, (x, y))
                else:
                    self.assertNotEqual(JOINER, cell.character, (x, y))

    def test_there_really_are_joins_and_really_are_gaps(self):
        # Otherwise the test above is satisfied by a frame with no joins at
        # all, or one that is nothing but joins.
        joined = sum(1 for y in range(self.maze.height)
                     for x in range(self.maze.width - 1)
                     if self.frame.cell(joiner_column(x), y).character == JOINER)
        total = self.maze.height * (self.maze.width - 1)
        self.assertGreater(joined, 0)
        self.assertLess(joined, total)

    def test_the_walls_are_blue_and_that_is_the_only_colour_they_have(self):
        colours = set()
        for (x, y) in self.maze.squares():
            if self.maze.is_wall(x, y):
                colours.add(self.frame.cell(column_of(x), y).colour)
        self.assertEqual({Colour.WALL}, colours)


class TheDotsTest(unittest.TestCase):
    """SCRN-4 — one small dim gold square per corridor square that has one."""

    def setUp(self):
        self.maze = generate_maze(9)
        # Actors tucked into a corner so they cover as little as possible, and
        # named explicitly so the eaten-dot arithmetic below is readable.
        self.player = self.maze.corridor_squares()[0]
        self.ghost = self.maze.corridor_squares()[-1]

    def frame_with(self, dots):
        return compose(state_on(self.maze, self.player, self.ghost, dots=dots))

    def covered(self):
        """Squares an actor is drawn over, so their dots cannot be seen."""
        return {self.player, self.ghost}

    def test_a_dot_appears_on_every_square_that_has_one(self):
        dots = frozenset(self.maze.corridor_squares()) - {self.player}
        frame = self.frame_with(dots)
        for (x, y) in sorted(dots - self.covered()):
            self.assertEqual(DOT, frame.cell(column_of(x), y).character, (x, y))
            self.assertEqual(Colour.DOT, frame.cell(column_of(x), y).colour)

    def test_and_on_no_square_that_does_not(self):
        # The other direction. Without it a builder that painted a dot on
        # every corridor square, eaten or not, would pass the test above.
        eaten = set(sorted(self.maze.corridor_squares())[:40])
        dots = frozenset(self.maze.corridor_squares()) - eaten - {self.player}
        frame = self.frame_with(dots)
        for (x, y) in sorted(eaten - self.covered()):
            self.assertNotEqual(DOT, frame.cell(column_of(x), y).character,
                                "a dot was drawn on an eaten square {0}"
                                .format((x, y)))

    def test_an_eaten_dot_changes_the_picture(self):
        # Pins that the two tests above are looking at something that moves.
        before = compose(state_on(self.maze, self.player, self.ghost))
        square = sorted(before and
                        (frozenset(self.maze.corridor_squares())
                         - {self.player} - self.covered()))[0]
        after = compose(state_on(
            self.maze, self.player, self.ghost,
            dots=frozenset(self.maze.corridor_squares()) - {self.player, square}))
        self.assertNotEqual(before.text_rows(), after.text_rows())
        self.assertEqual(DOT, before.cell(column_of(square[0]), square[1]).character)
        self.assertEqual(BLANK, after.cell(column_of(square[0]), square[1]).character)

    def test_no_dot_is_ever_drawn_on_a_wall_square(self):
        frame = self.frame_with(frozenset(self.maze.corridor_squares())
                                - {self.player})
        for (x, y) in self.maze.squares():
            if self.maze.is_wall(x, y):
                self.assertNotEqual(DOT, frame.cell(column_of(x), y).character,
                                    (x, y))

    def test_the_player_starts_on_the_one_square_without_a_dot(self):
        state = new_game(9)
        self.assertFalse(state.dot_at(state.player))
        self.assertEqual(len(state.maze.corridor_squares()) - 1,
                         state.dots_remaining)


class TheTwoActorsTest(unittest.TestCase):
    """SCRN-5 — distinguishable by **both** colour and outline."""

    def setUp(self):
        self.maze = generate_maze(11)
        corridors = self.maze.corridor_squares()
        self.player = corridors[len(corridors) // 3]
        self.ghost = corridors[2 * len(corridors) // 3]
        self.frame = compose(state_on(self.maze, self.player, self.ghost))

    def glyph_at(self, square):
        x, y = square
        return "".join(self.frame.cell(column_of(x) + offset, y).character
                       for offset in (-1, 0, 1))

    def colour_at(self, square):
        x, y = square
        return self.frame.cell(column_of(x), y).colour

    def test_each_actor_is_three_columns_wide_centred_on_its_square(self):
        self.assertEqual(3, ACTOR_WIDTH)
        self.assertEqual(PLAYER_GLYPH, self.glyph_at(self.player))
        self.assertEqual(GHOST_GLYPH, self.glyph_at(self.ghost))
        self.assertEqual(3, len(PLAYER_GLYPH))
        self.assertEqual(3, len(GHOST_GLYPH))

    def test_their_outlines_differ(self):
        self.assertNotEqual(PLAYER_GLYPH, GHOST_GLYPH)
        self.assertNotEqual(self.glyph_at(self.player), self.glyph_at(self.ghost))

    def test_their_colours_differ(self):
        # SCRN-5 asks for **both**. A test of the glyphs alone would pass on a
        # picture where both actors were the same colour, and a player who is
        # colour-blind to shape would have nothing left.
        self.assertNotEqual(Colour.PLAYER, Colour.GHOST)
        self.assertNotEqual(self.colour_at(self.player), self.colour_at(self.ghost))

    def test_the_player_is_bright_yellow_and_the_ghost_pink(self):
        for offset in (-1, 0, 1):
            self.assertEqual(Colour.PLAYER,
                             self.frame.cell(column_of(self.player[0]) + offset,
                                             self.player[1]).colour)
            self.assertEqual(Colour.GHOST,
                             self.frame.cell(column_of(self.ghost[0]) + offset,
                                             self.ghost[1]).colour)

    def test_the_actors_cover_the_dot_they_stand_on(self):
        # They are drawn over it; SCORE-4 is about the state, tested below.
        self.assertEqual(PLAYER_GLYPH[1], self.glyph_at(self.player)[1])
        self.assertEqual(GHOST_GLYPH[1], self.glyph_at(self.ghost)[1])

    def test_an_actor_never_runs_off_an_edge_of_any_generated_maze(self):
        # The M0 ruling, checked rather than trusted: the border ring means an
        # actor stands only on squares 1..17, so its glyph spans columns
        # 1..35 of 0..36 and `Frame.put` never has to clip.
        for seed in range(20):
            maze = generate_maze(seed)
            for (x, y) in maze.corridor_squares():
                self.assertGreaterEqual(column_of(x) - 1, 0, (seed, x, y))
                self.assertLess(column_of(x) + 1, PICTURE_WIDTH, (seed, x, y))


class TheDrawOrderTest(unittest.TestCase):
    """END-4 — the ghost is drawn after the player, so a loss shows why."""

    def setUp(self):
        self.maze = generate_maze(13)
        self.square = self.maze.corridor_squares()[30]

    def glyph_at(self, frame, square):
        x, y = square
        return "".join(frame.cell(column_of(x) + offset, y).character
                       for offset in (-1, 0, 1))

    def test_on_the_same_square_the_ghost_is_what_shows(self):
        frame = compose(state_on(self.maze, self.square, self.square))
        self.assertEqual(GHOST_GLYPH, self.glyph_at(frame, self.square))
        self.assertEqual(Colour.GHOST,
                         frame.cell(column_of(self.square[0]),
                                    self.square[1]).colour)

    def test_apart_the_player_still_shows(self):
        # Without this, a builder that never drew the player at all would
        # satisfy the test above.
        other = self.maze.corridor_squares()[60]
        frame = compose(state_on(self.maze, self.square, other))
        self.assertEqual(PLAYER_GLYPH, self.glyph_at(frame, self.square))
        self.assertEqual(GHOST_GLYPH, self.glyph_at(frame, other))

    def test_the_order_does_not_depend_on_which_walked_into_which(self):
        # The state carries no notion of who moved last, so it cannot: this
        # says so, because END-4 is about what the picture shows and not about
        # how the collision came about.
        caught = state_on(self.maze, self.square, self.square,
                          outcome=Outcome.CAUGHT)
        playing = state_on(self.maze, self.square, self.square)
        self.assertEqual(compose(caught).text_rows(),
                         compose(playing).text_rows())

    def test_the_actors_are_drawn_over_the_maze_and_not_under_it(self):
        # An actor beside a wall covers the joiner column next to it. That is
        # correct -- the actor is in front -- and it is worth pinning, because
        # a builder that drew the walls last would look almost right.
        maze = Maze.from_text("#####\n#...#\n#####", wall="#")
        frame = compose(state_on(maze, player=(1, 1), ghost=(3, 1)))
        # Column 0 is the border wall and must survive; column 1 is the
        # joiner, which the player's glyph takes.
        self.assertEqual("║", frame.cell(0, 1).character)
        self.assertEqual(PLAYER_GLYPH[0], frame.cell(1, 1).character)
        self.assertEqual(Colour.PLAYER, frame.cell(1, 1).colour)


class TheGhostDoesNotEatTest(unittest.TestCase):
    """SCORE-4 — a dot under the ghost is still there to be taken."""

    def test_composing_a_frame_does_not_change_the_state_at_all(self):
        state = new_game(17)
        before = (state.dots, state.score, state.player, state.ghost,
                  state.outcome)
        compose(state)
        compose(state)
        self.assertEqual(before, (state.dots, state.score, state.player,
                                  state.ghost, state.outcome))

    def test_the_dot_under_the_ghost_is_still_in_the_state(self):
        maze = generate_maze(19)
        square = maze.corridor_squares()[50]
        player = maze.corridor_squares()[0]
        state = state_on(maze, player=player, ghost=square)
        frame = compose(state)
        # Hidden in the picture...
        self.assertEqual(GHOST_GLYPH[1],
                         frame.cell(column_of(square[0]), square[1]).character)
        # ...and still there in the state.
        self.assertTrue(state.dot_at(square))

    def test_when_the_ghost_moves_on_the_dot_is_visible_again(self):
        # The proof that it was only ever covered. A builder that deleted the
        # dot would pass the test above and fail this one.
        maze = generate_maze(19)
        square = maze.corridor_squares()[50]
        elsewhere = maze.corridor_squares()[90]
        player = maze.corridor_squares()[0]
        on_it = compose(state_on(maze, player=player, ghost=square))
        moved = compose(state_on(maze, player=player, ghost=elsewhere))
        self.assertEqual(GHOST_GLYPH[1],
                         on_it.cell(column_of(square[0]), square[1]).character)
        self.assertEqual(DOT,
                         moved.cell(column_of(square[0]), square[1]).character)


class TheWholeFrameEachPassTest(unittest.TestCase):
    """SCRN-7 and caution C9 — rebuilt, never patched."""

    def test_each_call_returns_a_new_frame(self):
        state = new_game(23)
        first, second = compose(state), compose(state)
        self.assertIsNot(first, second)

    def test_the_same_state_composes_to_the_same_picture(self):
        state = new_game(23)
        self.assertEqual(compose(state).text_rows(), compose(state).text_rows())

    def test_every_cell_is_filled_rather_than_left_over(self):
        # "The whole frame is rebuilt each pass" means there is no cell whose
        # contents came from somewhere else. A fresh Frame starts blank, so
        # this checks the composition covers the picture area completely.
        frame = compose(new_game(23))
        for column, row, cell in frame.cells():
            self.assertEqual(1, len(cell.character), (column, row))
            self.assertIsNotNone(cell.colour, (column, row))

    def test_a_moved_ghost_gives_a_different_picture_with_no_debris(self):
        # The failure a dirty-cell optimisation would cause: a three-column
        # glyph leaves part of itself behind. Composing afresh cannot.
        maze = generate_maze(25)
        player = maze.corridor_squares()[0]
        here, there = maze.corridor_squares()[40], maze.corridor_squares()[41]
        moved = compose(state_on(maze, player, there))
        for offset in (-1, 0, 1):
            character = moved.cell(column_of(here[0]) + offset, here[1]).character
            self.assertNotIn(character, (GHOST_GLYPH[0], GHOST_GLYPH[2]),
                             "part of the ghost was left behind at {0}"
                             .format(here))


class TheStatusRowSeamTest(unittest.TestCase):
    """Row 29 belongs to WI-6, which has not landed."""

    def test_row_twenty_nine_is_blank_when_no_status_line_is_given(self):
        frame = compose(new_game(27))
        self.assertEqual(BLANK * WIDTH, frame.text_rows()[STATUS_ROW])

    def test_a_status_line_is_written_where_wi_six_asks_for_it(self):
        frame = compose(new_game(27), status_line=" score 0    arrows, q quits")
        self.assertTrue(frame.text_rows()[STATUS_ROW]
                        .startswith(" score 0    arrows, q quits"))

    def test_the_status_line_is_cyan(self):
        text = " score 0"
        frame = compose(new_game(27), status_line=text)
        for column in range(len(text)):
            self.assertEqual(Colour.STATUS,
                             frame.cell(column, STATUS_ROW).colour, column)

    def test_the_status_line_is_taken_exactly_as_given(self):
        # Including its leading space. What the line says, and whether it has
        # one, is STAT-1 to STAT-3's business and WI-6's decision.
        text = "  two leading spaces"
        frame = compose(new_game(27), status_line=text)
        self.assertEqual(text, frame.text_rows()[STATUS_ROW][:len(text)])

    def test_a_status_line_never_writes_above_its_own_row(self):
        without = compose(new_game(27))
        with_line = compose(new_game(27), status_line=" score 99")
        self.assertEqual(without.text_rows()[:MAZE_ROWS],
                         with_line.text_rows()[:MAZE_ROWS])

    def test_the_maze_never_writes_into_the_status_row(self):
        for seed in range(10):
            frame = compose(new_game(seed))
            self.assertEqual(BLANK * WIDTH, frame.text_rows()[STATUS_ROW], seed)

    def test_a_maze_too_big_for_the_window_is_refused_by_name(self):
        # `Frame.put` would have raised an IndexError about a cell coordinate:
        # true, but it names the symptom rather than the requirement, and a
        # reader has to work out which of the two is wrong. Plan §11.8.
        too_wide = Maze([[WALL] * 21 for _ in range(29)])
        state = GameState(maze=too_wide, player=(1, 1), ghost=(3, 1),
                          ghost_heading=NORTH, dots=frozenset())
        with self.assertRaises(MazeWillNotFit):
            compose(state)

    def test_a_maze_too_deep_for_the_window_is_refused_too(self):
        too_deep = Maze([[WALL] * 19 for _ in range(31)])
        state = GameState(maze=too_deep, player=(1, 1), ghost=(3, 1),
                          ghost_heading=NORTH, dots=frozenset())
        with self.assertRaises(MazeWillNotFit):
            compose(state)

    def test_the_maze_refusal_names_the_requirements_and_the_sizes(self):
        too_wide = Maze([[WALL] * 21 for _ in range(29)])
        state = GameState(maze=too_wide, player=(1, 1), ghost=(3, 1),
                          ghost_heading=NORTH, dots=frozenset())
        try:
            compose(state)
        except MazeWillNotFit as refused:
            said = str(refused)
            self.assertIn("MAZE-1", said)
            self.assertIn("SCRN-1", said)
            self.assertIn("21", said)
        else:
            self.fail("a maze the window cannot hold was drawn anyway")

    def test_the_maze_the_game_actually_makes_is_not_refused(self):
        # The boundary, so the refusal is off by nothing: 19 x 29 is exactly
        # what MAZE-1 asks for and must still compose.
        frame = compose(new_game(27))
        self.assertEqual(WIDTH, frame.width)

    def test_a_status_line_wider_than_the_window_is_refused(self):
        with self.assertRaises(StatusLineTooWide):
            compose(new_game(27), status_line="x" * (WIDTH + 1))

    def test_a_status_line_exactly_the_width_of_the_window_is_allowed(self):
        # The boundary, so the refusal is off by nothing.
        frame = compose(new_game(27), status_line="x" * WIDTH)
        self.assertEqual("x" * WIDTH, frame.text_rows()[STATUS_ROW])

    def test_the_refusal_names_the_requirement(self):
        try:
            compose(new_game(27), status_line="x" * 99)
        except StatusLineTooWide as refused:
            self.assertIn("SCRN-1", str(refused))
            self.assertEqual(99, len(refused.text))
        else:
            self.fail("a 99-column status line was accepted")


class ASmallMazeByHandTest(unittest.TestCase):
    """A picture small enough to write out and read."""

    def test_it_composes_to_exactly_this(self):
        # Worked through by hand rather than pasted from the output. Row 2 is
        # the interesting one: square 0 is the left border `║`, square 1 a
        # dotted corridor, square 2 a wall with no wall beside it — so it is
        # SCRN-3's "single blue block" — square 3 another dot, square 4 the
        # right border. The joiner columns between them are all blank,
        # because no two neighbouring squares on that row are both wall.
        state = state_on(SMALL, player=(1, 1), ghost=(3, 3))
        rows = [row[:9] for row in compose(state).text_rows()[:5]]
        self.assertEqual([
            u"╔═══════╗",
            u"║▐█▌▪ ▪ ║",
            u"║ ▪ ■ ▪ ║",
            u"║ ▪ ▪▗█▖║",
            u"╚═══════╝",
        ], rows)

    def test_the_lone_wall_square_in_the_middle_is_a_block(self):
        # I got this wrong first time and wrote `║`. The square at (2, 2) has
        # corridor on all four sides, so SCRN-3's lone-block case is exactly
        # what it is — the same case the specification's picture labels "a
        # lone wall square".
        state = state_on(SMALL, player=(1, 1), ghost=(3, 3))
        frame = compose(state)
        self.assertEqual(u"■", frame.cell(column_of(2), 2).character)
        self.assertEqual(WALL_COLOUR, frame.cell(column_of(2), 2).colour)


class EveryColourIsOneTheSpecificationNamesTest(unittest.TestCase):

    def test_no_cell_carries_a_colour_from_outside_the_palette(self):
        named = {Colour.DEFAULT, Colour.WALL, Colour.DOT, Colour.PLAYER,
                 Colour.GHOST, Colour.STATUS}
        frame = compose(new_game(29), status_line=" score 0")
        for column, row, cell in frame.cells():
            self.assertIn(cell.colour, named, (column, row))

    def test_all_five_of_the_specifications_colours_are_actually_used(self):
        # Otherwise the test above passes on a blank frame.
        frame = compose(new_game(29), status_line=" score 0")
        used = set(cell.colour for _, _, cell in frame.cells())
        self.assertEqual({Colour.DEFAULT, Colour.WALL, Colour.DOT,
                          Colour.PLAYER, Colour.GHOST, Colour.STATUS}, used)


class TheDomainIsNotDraggedIntoPresentationTest(unittest.TestCase):
    """The layer rule, for the module this item adds.

    `tests/test_layering.py` is **not** edited by this item — the presentation
    sweep there walks the whole sub-package, so `frame_builder.py` is covered
    automatically and an adjacent-line edit in that shared file is a
    predictable cross-lane conflict for nothing. Same choice DEV-A made for
    `player.py` and I made for `ghost_policy.py`.
    """

    def test_the_presentation_sweep_includes_the_frame_builder(self):
        import os
        from tests.test_layering import THE_PRESENTATION, presentation_files
        names = [name for name, _ in presentation_files()]
        self.assertIn(os.path.join(THE_PRESENTATION, "frame_builder.py"), names)

    def test_it_imports_only_the_domain_and_the_port(self):
        from tests.test_layering import (PRESENTATION_MAY_IMPORT,
                                         imported_game_modules, source_of)
        import terminalgame.presentation.frame_builder as module
        for imported in imported_game_modules(source_of(module.__file__)):
            self.assertTrue(
                any(imported == allowed or imported.startswith(allowed + ".")
                    for allowed in PRESENTATION_MAY_IMPORT),
                "frame_builder imported {0}".format(imported))


if __name__ == "__main__":
    unittest.main()
