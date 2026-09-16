# -*- coding: utf-8 -*-
"""WI-12 — the frame composer.

**The wall glyphs in these tests are deliberately fake.**  WI-8 owns which
glyph a wall square is drawn as and this item owns *where* it goes, so the
stub below answers with ``W`` for a wall and ``-`` for a connector.  A test
here that asserted ``╔`` would be re-asserting WI-8's job through a bigger
object — one defect, two tests red, in two files.  The real glyphs are joined
up in exactly one place, and that place is the integration test that lands
with WI-8.
"""

from __future__ import annotations

import random
import unittest

from terminal_game.domain.dot_field import DotField
from terminal_game.domain.maze_generator import generate_maze
from terminal_game.domain.opening_position import opening_position
from terminal_game.domain.game_state import GameState, Outcome, Score
from terminal_game.domain.maze import Maze, Square
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
)
from terminal_game.presentation.frame_composer import (
    DOT_GLYPH,
    GHOST_MOTIF,
    PLAYER_MOTIF,
    column_of_square,
    compose_frame,
)
from terminal_game.presentation.wall_glyphs import wall_layer, wall_layer_text

#: A stand-in for row 29.  WI-13 owns what actually goes there, and the
#: prohibition is explicit: no other item's tests may contain a status-line
#: literal.  This is deliberately not one.
STATUS_STAND_IN = tuple(
    [Cell(c, Colour.STATUS_CYAN) for c in "ROW-29"]
    + [BLANK] * (FRAME_COLUMNS - 6)
)


class FakeWalls:
    """A wall layer in a vocabulary that is obviously not the real one.

    Same shape as WI-8's ``wall_layer`` — one tuple per grid row, square *c*
    at index 2c and the connector at 2c+1 — but ``W`` for a wall square and
    ``-`` for a joining connector.  Using the real box-drawing glyphs here
    would make WI-12's tests fail when WI-8 changed something that is none of
    WI-12's business.
    """

    WALL = Cell("W", Colour.WALL_BLUE)
    CONNECTOR = Cell("-", Colour.WALL_BLUE)

    def __init__(self):
        self.mazes = []

    def __call__(self, maze):
        self.mazes.append(maze)
        rows = []
        for row in range(maze.height):
            cells = []
            for column in range(maze.width):
                square = Square(column, row)
                cells.append(self.WALL if maze.is_wall(square) else BLANK)
                if column < maze.width - 1:
                    east = Square(column + 1, row)
                    joins = maze.is_wall(square) and maze.is_wall(east)
                    cells.append(self.CONNECTOR if joins else BLANK)
            rows.append(tuple(cells))
        return tuple(rows)


# A seven-by-three maze: a corridor running east-west through the middle.
# Seven squares wide so that two actors can stand far enough apart for their
# three-column motifs not to overlap: squares 2 apart are columns 4 apart,
# and a motif is 3 wide.
SMALL = Maze.from_text(
    """
#######
#.....#
#######
"""
)


def bordered(width, height):
    """A maze of *width* x *height*: a solid border round open corridor."""
    lines = ["#" * width]
    lines += ["#" + "." * (width - 2) + "#" for _ in range(height - 2)]
    lines += ["#" * width]
    return Maze.from_text("\n".join(lines))


def a_state(maze=SMALL, player=None, ghost=None, eaten=(), outcome=None):
    """A game state over *maze*, with dots everywhere but the eaten squares."""
    player = Square(1, 1) if player is None else player
    ghost = Square(5, 1) if ghost is None else ghost
    dots = DotField.over_corridors_except(maze, player)
    for square in eaten:
        dots = dots.without_dot_at(square)
    return GameState(
        maze=maze,
        dots=dots,
        player=player,
        ghost=ghost,
        score=Score(),
        outcome=Outcome.UNDECIDED if outcome is None else outcome,
    )


def compose(state, walls=None):
    return compose_frame(state, STATUS_STAND_IN, walls or FakeWalls())


def maze_text(frame, rows):
    """The first *rows* rows of the picture, as full 40-column lines."""
    return [frame.row_text(row) for row in range(rows)]


def picture(*lines):
    """Expected rows, padded out to the full width of the frame."""
    return [line.ljust(FRAME_COLUMNS) for line in lines]


class WhereASquareIsDrawn(unittest.TestCase):
    """Square *c* at column 2c — plan section 5, assumption A6."""

    def test_the_first_square_is_at_column_zero(self):
        self.assertEqual(0, column_of_square(0))

    def test_each_square_is_two_columns_along_from_the_last(self):
        self.assertEqual([0, 2, 4, 6, 8], [column_of_square(c) for c in range(5)])

    def test_the_nineteenth_square_is_at_the_last_maze_column(self):
        self.assertEqual(MAZE_COLUMNS - 1, column_of_square(18))

    def test_a_twentieth_square_would_not_fit(self):
        with self.assertRaises(IndexError):
            column_of_square(19)

    def test_nineteen_squares_fill_exactly_the_thirty_seven_columns(self):
        # The architecture's MAZE-1 prose says 38 and a 2-column margin.
        # Its own measurement V8 and the plan both say 37 and 3.
        self.assertEqual(37, 2 * 19 - 1)
        self.assertEqual(MAZE_COLUMNS, 2 * 19 - 1)
        self.assertEqual(3, RIGHT_MARGIN_COLUMNS)


class AKnownPicture(unittest.TestCase):
    """A small hand-built maze composes to a picture, asserted as text."""

    def test_the_small_maze_composes_to_exactly_this(self):
        # Player on square 1 so it has no dot; ghost on square 5, over one.
        # W is a wall square and - the connector between two of them, both
        # from the fake resolver. Each actor's motif covers the connector on
        # either side of it, which is why there is no gap beside them.
        frame = compose(a_state())

        self.assertEqual(
            picture(
                "W-W-W-W-W-W-W",
                "W▐█▌▪ ▪ ▪▗█▖W",
                "W-W-W-W-W-W-W",
            ),
            maze_text(frame, 3),
        )

    def test_the_rows_below_the_maze_are_blank(self):
        frame = compose(a_state())

        for row in range(SMALL.height, MAZE_ROWS):
            self.assertEqual(" " * FRAME_COLUMNS, frame.row_text(row))

    def test_moving_the_player_one_square_moves_it_two_columns(self):
        # Square c is drawn at column 2c, so one square east is two columns
        # east — and the dot the player has left behind is not restored,
        # because the dot field is what says where dots are.
        before = compose(a_state(player=Square(1, 1)))
        after = compose(a_state(player=Square(2, 1)))

        self.assertEqual(picture("W▐█▌▪ ▪ ▪▗█▖W")[0], before.row_text(1))
        self.assertEqual(picture("W ▪▐█▌▪ ▪▗█▖W")[0], after.row_text(1))


class TheRightHandMargin(unittest.TestCase):
    """MAZE-1 — 37 columns of maze and three blank columns after it."""

    def test_every_maze_row_is_forty_cells_with_three_blank_at_the_end(self):
        frame = compose(a_state())

        for row in range(MAZE_ROWS):
            text = frame.row_text(row)
            self.assertEqual(FRAME_COLUMNS, len(text))
            self.assertEqual(" " * RIGHT_MARGIN_COLUMNS, text[MAZE_COLUMNS:])

    def test_the_margin_is_black_ground_and_not_merely_spaces(self):
        frame = compose(a_state())

        for row in range(MAZE_ROWS):
            for column in range(MAZE_COLUMNS, FRAME_COLUMNS):
                self.assertEqual(BLANK, frame.cell_at(row, column))

    def test_a_full_size_maze_fills_the_maze_rows_and_leaves_the_margin(self):
        wide = bordered(19, 29)
        state = a_state(maze=wide, player=Square(1, 1), ghost=Square(17, 1))

        frame = compose(state)

        for row in range(MAZE_ROWS):
            text = frame.row_text(row)
            self.assertEqual(MAZE_COLUMNS, len(text[:MAZE_COLUMNS].rstrip()))
            self.assertEqual(" " * RIGHT_MARGIN_COLUMNS, text[MAZE_COLUMNS:])

    def test_a_maze_too_wide_for_the_picture_is_refused(self):
        wide = bordered(20, 3)

        with self.assertRaises(ValueError):
            compose(a_state(maze=wide, player=Square(1, 1), ghost=Square(2, 1)))

    def test_a_maze_too_deep_for_the_picture_is_refused(self):
        deep = bordered(5, 30)

        with self.assertRaises(ValueError):
            compose(a_state(maze=deep, player=Square(1, 1), ghost=Square(2, 1)))


class TheActorsAreThreeColumnMotifs(unittest.TestCase):
    """Plan section 5 — centred on 2c, covering 2c-1 .. 2c+1."""

    def test_the_player_occupies_the_three_columns_round_its_square(self):
        frame = compose(a_state(player=Square(2, 1), ghost=Square(5, 1)))

        centre = column_of_square(2)
        self.assertEqual(
            PLAYER_MOTIF,
            "".join(
                frame.cell_at(1, column).glyph
                for column in (centre - 1, centre, centre + 1)
            ),
        )

    def test_the_ghost_occupies_the_three_columns_round_its_square(self):
        frame = compose(a_state(player=Square(5, 1), ghost=Square(2, 1)))

        centre = column_of_square(2)
        self.assertEqual(
            GHOST_MOTIF,
            "".join(
                frame.cell_at(1, column).glyph
                for column in (centre - 1, centre, centre + 1)
            ),
        )

    def test_an_actor_covers_the_connector_on_each_side(self):
        # The motif overwrites the odd columns either side, which is safe
        # because a connector next to a corridor square is always blank.
        frame = compose(a_state(player=Square(2, 1), ghost=Square(5, 1)))
        centre = column_of_square(2)

        self.assertNotEqual("-", frame.cell_at(1, centre - 1).glyph)
        self.assertNotEqual("-", frame.cell_at(1, centre + 1).glyph)

    def test_the_two_motifs_differ_in_shape_as_well_as_colour(self):
        # SCRN-5: told apart by colour *and* by outline.
        self.assertNotEqual(PLAYER_MOTIF, GHOST_MOTIF)
        self.assertEqual(3, len(PLAYER_MOTIF))
        self.assertEqual(3, len(GHOST_MOTIF))

    def test_the_motifs_are_the_ones_the_requirements_specify(self):
        self.assertEqual("▐█▌", PLAYER_MOTIF)
        self.assertEqual("▗█▖", GHOST_MOTIF)


class TheDrawOrder(unittest.TestCase):
    """END-4 — the player first and the ghost second."""

    def test_when_they_share_a_square_the_ghost_is_what_is_seen(self):
        together = Square(2, 1)
        frame = compose(a_state(player=together, ghost=together))

        centre = column_of_square(2)
        self.assertEqual(
            GHOST_MOTIF,
            "".join(
                frame.cell_at(1, column).glyph
                for column in (centre - 1, centre, centre + 1)
            ),
        )

    def test_when_they_share_a_square_the_colour_is_the_ghosts_too(self):
        together = Square(2, 1)
        frame = compose(a_state(player=together, ghost=together))

        self.assertEqual(
            Colour.GHOST_PINK, frame.colour_at(1, column_of_square(2))
        )

    def test_the_final_picture_of_a_loss_shows_the_ghost_over_the_player(self):
        together = Square(3, 1)
        frame = compose(
            a_state(player=together, ghost=together, outcome=Outcome.CAUGHT)
        )

        self.assertIn(GHOST_MOTIF, frame.row_text(1))
        self.assertNotIn(PLAYER_MOTIF, frame.row_text(1))


class TheDots(unittest.TestCase):
    """SCRN-4 and SCORE-4."""

    def test_a_corridor_square_with_a_dot_shows_the_dot(self):
        frame = compose(a_state(player=Square(1, 1), ghost=Square(1, 1)))

        self.assertEqual(DOT_GLYPH, frame.cell_at(1, column_of_square(2)).glyph)

    def test_the_dot_is_dim_gold(self):
        frame = compose(a_state(player=Square(1, 1), ghost=Square(1, 1)))

        self.assertEqual(
            Colour.DOT_GOLD, frame.colour_at(1, column_of_square(2))
        )

    def test_an_eaten_square_shows_blank_and_not_a_dot(self):
        state = a_state(
            player=Square(1, 1), ghost=Square(1, 1), eaten=[Square(2, 1)]
        )

        frame = compose(state)

        self.assertEqual(BLANK, frame.cell_at(1, column_of_square(2)))

    def test_the_players_own_square_has_no_dot_to_hide(self):
        # START-3: the player starts on the one corridor square without one.
        state = a_state(player=Square(1, 1), ghost=Square(3, 1))

        self.assertFalse(state.dots.has_dot(Square(1, 1)))

    def test_a_dot_under_the_ghost_is_still_in_the_dot_field_afterwards(self):
        # SCORE-4: the ghost neither eats a dot nor hides it away; composing
        # a picture is a question, not a move.
        state = a_state(player=Square(1, 1), ghost=Square(3, 1))
        self.assertTrue(state.dots.has_dot(Square(3, 1)))

        compose(state)

        self.assertTrue(state.dots.has_dot(Square(3, 1)))

    def test_composing_changes_nothing_about_the_state(self):
        state = a_state()
        before = (state.dots, state.player, state.ghost, state.outcome)

        compose(state)

        self.assertEqual(
            before, (state.dots, state.player, state.ghost, state.outcome)
        )

    def test_composing_the_same_state_twice_gives_the_same_picture(self):
        state = a_state()

        self.assertEqual(compose(state), compose(state))


class RowTwentyNineIsNotThisItems(unittest.TestCase):
    """STAT-1 — WI-13 owns row 29 and WI-12 places what it is given."""

    def test_the_status_row_is_exactly_what_was_handed_over(self):
        frame = compose(a_state())

        self.assertEqual(
            list(STATUS_STAND_IN),
            list(frame.rows[STATUS_ROW]),
        )

    def test_nothing_the_composer_draws_reaches_row_twenty_nine(self):
        # A maze as deep as the picture allows still stops at row 28.
        deep = bordered(5, 29)
        state = a_state(maze=deep, player=Square(1, 1), ghost=Square(3, 1))

        frame = compose(state)

        self.assertEqual(
            list(STATUS_STAND_IN), list(frame.rows[STATUS_ROW])
        )

    def test_the_composer_contains_no_status_line_literal(self):
        import inspect

        import terminal_game.presentation.frame_composer as composer

        source = inspect.getsource(composer)

        for literal in ("score", "CAUGHT", "CLEARED", "q quits", "arrows"):
            self.assertNotIn(
                literal,
                source,
                "a status-line literal has leaked into WI-12: {0!r}".format(
                    literal
                ),
            )


class TheWallsBelongToWiEight(unittest.TestCase):
    """WI-8 owns every wall glyph and the connector rule; WI-12 declares none."""

    def test_the_composer_declares_no_wall_glyph_of_its_own(self):
        import inspect

        import terminal_game.presentation.frame_composer as composer

        source = inspect.getsource(composer)
        executable = "".join(source.split('"""')[::2])

        for glyph in "═║╔╗╚╝╠╣" \
                     "╦╩╬■":
            self.assertNotIn(
                glyph,
                executable,
                "WI-12 has declared the wall glyph {0!r}, which is "
                "WI-8's".format(glyph),
            )

    def test_the_layer_is_asked_for_once_and_for_the_state_s_own_maze(self):
        walls = FakeWalls()
        state = a_state()

        compose(state, walls)

        self.assertEqual([state.maze], walls.mazes)

    def test_every_wall_square_of_the_layer_appears_at_its_own_column(self):
        frame = compose(a_state())

        for row in range(SMALL.height):
            for column_index in range(SMALL.width):
                square = Square(column_index, row)
                if not SMALL.is_wall(square):
                    continue
                cell = frame.cell_at(row, column_of_square(column_index))
                self.assertEqual(
                    FakeWalls.WALL,
                    cell,
                    "wall square {0!r}".format(tuple(square)),
                )

    def test_a_wall_layer_of_the_wrong_shape_is_refused(self):
        def too_short(maze):
            return FakeWalls()(maze)[:-1]

        with self.assertRaises(ValueError):
            compose(a_state(), too_short)

    def test_a_wall_layer_row_of_the_wrong_width_is_refused(self):
        def too_narrow(maze):
            return tuple(row[:-1] for row in FakeWalls()(maze))

        with self.assertRaises(ValueError):
            compose(a_state(), too_narrow)

    def test_the_cell_the_resolver_hands_back_is_what_appears(self):
        frame = compose(a_state())

        self.assertEqual(FakeWalls.WALL, frame.cell_at(0, 0))
        self.assertEqual(FakeWalls.CONNECTOR, frame.cell_at(0, 1))

    def test_a_blank_connector_leaves_the_ground_showing(self):
        # Column 7 is the connector between two corridor squares, where the
        # resolver answers None, and no motif reaches it.
        frame = compose(a_state(player=Square(1, 1), ghost=Square(5, 1)))

        self.assertEqual(BLANK, frame.cell_at(1, 7))


class TheJoinToTheRealWallGlyphs(unittest.TestCase):
    """The seam to WI-8, and nothing either side of it.

    Every other test in this file stands the walls in with a fake
    vocabulary, because which glyph a wall is drawn as belongs to WI-8's
    tests. This class owns the one thing neither of us can assert alone:
    that the composer really does lay its dots and actors over the real
    layer, at the columns the real layer puts walls in.
    """

    def test_by_default_the_composer_uses_the_real_wall_layer(self):
        # No stub: the walls are whatever WI-8 says they are.
        frame = compose_frame(a_state(), STATUS_STAND_IN)

        self.assertEqual(
            wall_layer_text(SMALL).split("\n")[0],
            frame.row_text(0)[:MAZE_COLUMNS].rstrip().ljust(
                2 * SMALL.width - 1
            ),
        )

    def test_the_dots_and_actors_go_over_the_real_layer_untouched(self):
        # Take the real wall layer, overlay what WI-12 owns, and check the
        # composed picture is exactly that. It fails if either the walls
        # move or the overlay lands in the wrong column, and for no other
        # reason — WI-8's glyph choices are read from WI-8, not retyped.
        state = a_state()
        expected = [list(row) for row in wall_layer(SMALL)]
        for square in state.dots.squares():
            expected[square.row][column_of_square(square.column)] = Cell(
                DOT_GLYPH, Colour.DOT_GOLD
            )
        for square, motif, colour in (
            (state.player, PLAYER_MOTIF, Colour.PLAYER_YELLOW),
            (state.ghost, GHOST_MOTIF, Colour.GHOST_PINK),
        ):
            centre = column_of_square(square.column)
            for offset, glyph in zip((-1, 0, 1), motif):
                expected[square.row][centre + offset] = Cell(glyph, colour)

        frame = compose_frame(state, STATUS_STAND_IN)

        for row, cells in enumerate(expected):
            self.assertEqual(
                cells,
                list(frame.rows[row][: len(cells)]),
                "row {0}".format(row),
            )

    def test_an_actor_motif_never_covers_a_wall_glyph(self):
        """The load-bearing safety claim behind three-column motifs.

        Section 5 says the actors overwrite the connector on each side and
        that this is safe, *because* a connector next to a corridor square
        is always blank — the horizontal glyph appears only between two
        joined wall squares, and an actor only ever stands on corridor.
        If that were ever wrong the picture would silently lose a wall.
        Checked over real generated mazes rather than argued about.
        """
        for seed in range(12):
            maze = generate_maze(random.Random(seed))
            state = opening_position(maze)
            layer = wall_layer(maze)

            frame = compose_frame(state, STATUS_STAND_IN)

            for row, cells in enumerate(layer):
                for column, cell in enumerate(cells):
                    if cell == BLANK:
                        continue
                    self.assertEqual(
                        cell,
                        frame.cell_at(row, column),
                        "seed {0}: the wall at ({1}, {2}) was covered "
                        "over".format(seed, row, column),
                    )

    def test_a_real_game_composes_to_a_full_and_well_formed_picture(self):
        maze = generate_maze(random.Random(4))
        state = opening_position(maze)

        frame = compose_frame(state, STATUS_STAND_IN)

        lines = frame.to_text().split("\n")
        self.assertEqual(FRAME_ROWS, len(lines))
        self.assertEqual({FRAME_COLUMNS}, {len(line) for line in lines})
        for row in range(MAZE_ROWS):
            self.assertEqual(
                " " * RIGHT_MARGIN_COLUMNS, lines[row][MAZE_COLUMNS:]
            )
        # The actors are both on screen, exactly once each.
        picture_text = "\n".join(lines[:MAZE_ROWS])
        self.assertEqual(1, picture_text.count(PLAYER_MOTIF))
        self.assertEqual(1, picture_text.count(GHOST_MOTIF))
        # Every dot the field holds is drawn, except the one the ghost is
        # standing on — the ghost is painted over it and the dot is still
        # in the field to be taken (SCORE-4). The player is never on a dot:
        # its start square has none (START-3) and moving onto one eats it.
        self.assertTrue(
            state.dots.has_dot(state.ghost),
            "this seed was chosen because the ghost starts on a dot; "
            "without that the next assertion proves nothing",
        )
        self.assertFalse(state.dots.has_dot(state.player))
        self.assertEqual(
            state.dots.remaining - 1, picture_text.count(DOT_GLYPH)
        )
        # ...and the hidden one really is still there afterwards.
        self.assertTrue(state.dots.has_dot(state.ghost))

    def test_the_real_layer_is_as_wide_as_this_item_expects(self):
        # Both items derive "square c at column 2c" and they must agree.
        full = bordered(19, 29)

        layer = wall_layer(full)

        self.assertEqual(MAZE_ROWS, len(layer))
        self.assertEqual(MAZE_COLUMNS, len(layer[0]))
        self.assertEqual(MAZE_COLUMNS - 1, column_of_square(full.width - 1))


if __name__ == "__main__":
    unittest.main()
