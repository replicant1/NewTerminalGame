# -*- coding: utf-8 -*-
"""WI-8 — the wall glyphs and the connector rule (SCRN-3).

Hand-built mazes and the specimen picture.  Nothing here needs a window, a
clock or a random source: the whole item is a pure function of a wall
square's four neighbours.

Two things these tests deliberately do **not** claim:

* They say nothing about whether the strokes of adjacent double-line glyphs
  **meet** on screen.  That is about glyph shapes rather than the characters
  chosen, only an eye can settle it, and it is WI-16's.  A green run here is
  not evidence for it.
* They name no dot glyph and no actor motif.  Those are WI-12's, and
  :class:`DeclaresNothingItDoesNotOwn` below pins that this module produces
  neither.
"""

from __future__ import annotations

import itertools
import unittest

from terminal_game.domain.maze import DIRECTIONS, Direction, Maze, Square
from terminal_game.presentation.frame import BLANK, Cell, Colour, MAZE_COLUMNS
from terminal_game.presentation.wall_glyphs import (
    BLANK_CONNECTOR_GLYPH,
    CROSSING_GLYPH,
    HORIZONTAL_GLYPH,
    LONE_WALL_GLYPH,
    NotAWallSquare,
    WALL_COLOUR,
    WALL_GLYPHS,
    connector_cell_east_of,
    connector_glyph_east_of,
    glyph_for_wall_neighbours,
    wall_cell_at,
    wall_glyph_at,
    wall_layer,
    wall_layer_text,
)
from tests.generated_mazes import maze_for
from terminal_game.presentation.specimen import SPECIMEN_MAZE_ROWS

N = Direction.NORTH
E = Direction.EAST
S = Direction.SOUTH
W = Direction.WEST


def a_wall_with_neighbours(*directions):
    """A 3 x 3 maze whose centre square is wall, with the named neighbours.

    Everything else is corridor, including the diagonals — which is the
    point: only the four orthogonal neighbours may influence the glyph.
    """

    def square(direction):
        return "#" if direction in directions else "."

    text = "\n".join(
        (
            "." + square(N) + ".",
            square(W) + "#" + square(E),
            "." + square(S) + ".",
        )
    )
    return Maze.from_text(text)


#: The centre of every fixture :func:`a_wall_with_neighbours` builds.
CENTRE = Square(1, 1)


class TheSixteenCombinations(unittest.TestCase):
    """SCRN-3 — every way a wall square's four neighbours can fall.

    Each case names the glyph it expects so a reader can hold this file next
    to the specimen picture in ``FUNCTIONAL_REQUIREMENTS.md`` and check them
    off.  Fifteen of the sixteen occur in that picture; the crossing does
    not, and its own test says so.
    """

    def assert_glyph(self, expected, *neighbours):
        maze = a_wall_with_neighbours(*neighbours)

        self.assertEqual(expected, wall_glyph_at(maze, CENTRE))

    # -- no neighbour at all ---------------------------------------------

    def test_no_wall_neighbour_is_the_lone_blue_block(self):
        self.assert_glyph("■")

    # -- one neighbour ----------------------------------------------------

    def test_north_only_is_the_double_vertical(self):
        self.assert_glyph("║", N)

    def test_south_only_is_the_double_vertical(self):
        self.assert_glyph("║", S)

    def test_east_only_is_the_double_horizontal(self):
        self.assert_glyph("═", E)

    def test_west_only_is_the_double_horizontal(self):
        self.assert_glyph("═", W)

    # -- two neighbours, in line ------------------------------------------

    def test_north_and_south_is_the_double_vertical(self):
        self.assert_glyph("║", N, S)

    def test_east_and_west_is_the_double_horizontal(self):
        self.assert_glyph("═", E, W)

    # -- two neighbours, at right angles: the four corners ----------------

    def test_south_and_east_is_the_top_left_corner(self):
        self.assert_glyph("╔", S, E)

    def test_south_and_west_is_the_top_right_corner(self):
        self.assert_glyph("╗", S, W)

    def test_north_and_east_is_the_bottom_left_corner(self):
        self.assert_glyph("╚", N, E)

    def test_north_and_west_is_the_bottom_right_corner(self):
        self.assert_glyph("╝", N, W)

    # -- three neighbours: the four tees ----------------------------------

    def test_north_east_and_south_is_the_tee_opening_east(self):
        self.assert_glyph("╠", N, E, S)

    def test_north_west_and_south_is_the_tee_opening_west(self):
        self.assert_glyph("╣", N, W, S)

    def test_east_south_and_west_is_the_tee_opening_south(self):
        self.assert_glyph("╦", E, S, W)

    def test_north_east_and_west_is_the_tee_opening_north(self):
        self.assert_glyph("╩", N, E, W)

    # -- four neighbours ---------------------------------------------------

    def test_all_four_is_the_crossing(self):
        """The one combination the specimen picture does not contain.

        Section 5 of the plan says so too.  It is reasoned from the set, not
        measured off the picture like the other fifteen, and that is worth
        knowing when reading a failure here.
        """
        self.assert_glyph("╬", N, E, S, W)


class TheTableIsTotalAndWellFormed(unittest.TestCase):
    """Whatever a maze hands over, there is an answer and it fits a cell."""

    def test_every_one_of_the_sixteen_subsets_has_a_glyph(self):
        subsets = [
            frozenset(combination)
            for size in range(len(DIRECTIONS) + 1)
            for combination in itertools.combinations(DIRECTIONS, size)
        ]

        self.assertEqual(16, len(set(subsets)))
        for subset in subsets:
            self.assertEqual(
                WALL_GLYPHS[subset], glyph_for_wall_neighbours(subset)
            )

    def test_every_glyph_is_exactly_one_character(self):
        for neighbours, glyph in WALL_GLYPHS.items():
            self.assertEqual(
                1,
                len(glyph),
                "{0} maps to {1!r}, which is not one character".format(
                    sorted(direction.name for direction in neighbours), glyph
                ),
            )

    def test_the_order_the_neighbours_arrive_in_makes_no_difference(self):
        self.assertEqual(
            glyph_for_wall_neighbours([N, E, S]),
            glyph_for_wall_neighbours([S, N, E]),
        )

    def test_something_that_is_not_a_direction_is_refused(self):
        with self.assertRaises(TypeError):
            glyph_for_wall_neighbours(["north"])


class AskingAboutASquare(unittest.TestCase):
    """The query surface: what a wall square is drawn as, and what is not."""

    def test_the_glyph_comes_back_in_wall_blue(self):
        maze = a_wall_with_neighbours(N, S)

        self.assertEqual(
            Cell("║", Colour.WALL_BLUE), wall_cell_at(maze, CENTRE)
        )

    def test_a_corridor_square_has_no_wall_glyph(self):
        maze = Maze.from_text("...\n...\n...")

        with self.assertRaises(NotAWallSquare):
            wall_glyph_at(maze, CENTRE)

    def test_a_square_outside_the_grid_is_refused(self):
        maze = a_wall_with_neighbours(N)

        with self.assertRaises(ValueError):
            wall_glyph_at(maze, Square(9, 9))


class TheConnectorColumn(unittest.TestCase):
    """The odd column between two square columns, and what it holds."""

    def test_between_two_horizontally_joined_walls_it_is_the_horizontal(self):
        maze = Maze.from_text("##")

        self.assertEqual(
            HORIZONTAL_GLYPH, connector_glyph_east_of(maze, Square(0, 0))
        )

    def test_between_two_corridors_it_is_blank(self):
        maze = Maze.from_text("..")

        self.assertEqual(
            BLANK_CONNECTOR_GLYPH, connector_glyph_east_of(maze, Square(0, 0))
        )

    def test_with_a_corridor_to_the_east_it_is_blank(self):
        maze = Maze.from_text("#.")

        self.assertEqual(
            BLANK_CONNECTOR_GLYPH, connector_glyph_east_of(maze, Square(0, 0))
        )

    def test_with_a_corridor_to_the_west_it_is_blank(self):
        maze = Maze.from_text(".#")

        self.assertEqual(
            BLANK_CONNECTOR_GLYPH, connector_glyph_east_of(maze, Square(0, 0))
        )

    def test_a_joining_connector_is_wall_blue(self):
        maze = Maze.from_text("##")

        self.assertEqual(
            Cell(HORIZONTAL_GLYPH, Colour.WALL_BLUE),
            connector_cell_east_of(maze, Square(0, 0)),
        )

    def test_a_blank_connector_is_the_frame_s_blank_on_black_ground(self):
        """Nothing is drawn there, so nothing there is coloured blue.

        A blue space would read the same on screen and differently in every
        colour assertion downstream, which is the sort of thing that is found
        three work items later.
        """
        maze = Maze.from_text("..")

        self.assertEqual(BLANK, connector_cell_east_of(maze, Square(0, 0)))
        self.assertEqual(
            Colour.GROUND_BLACK, connector_cell_east_of(maze, Square(0, 0)).colour
        )

    def test_there_is_no_connector_after_the_last_square_of_a_row(self):
        maze = Maze.from_text("##")

        with self.assertRaises(ValueError):
            connector_glyph_east_of(maze, Square(1, 0))


class TheWallLayer(unittest.TestCase):
    """Every wall of a maze laid out, with blanks where the walls are not."""

    def test_a_bordered_ring_reads_as_a_ring(self):
        """The border-ring case the plan asks for: corners, edges, connectors.

        Small enough to check by eye, which the specimen is not.  It reads as
        a ring rather than as a row of crossings because a neighbour off the
        edge of the grid is not a wall — which is ``Maze.wall_neighbours``'s
        behaviour and ``tests/test_maze.py``'s to assert.  What is asserted
        here is the join: that a corner square really comes out as the corner
        glyph and not as something that merely has the right neighbours.
        """
        ring = Maze.from_text("#####\n#...#\n#...#\n#...#\n#####")

        self.assertEqual(
            "\n".join(
                (
                    "╔═══════╗",
                    "║       ║",
                    "║       ║",
                    "║       ║",
                    "╚═══════╝",
                )
            ),
            wall_layer_text(ring),
        )

    def test_a_lone_wall_inside_a_room_stands_alone(self):
        room = Maze.from_text(".....\n.....\n..#..\n.....\n.....")

        self.assertEqual(
            "\n".join(
                (
                    "         ",
                    "         ",
                    "    ■    ",
                    "         ",
                    "         ",
                )
            ),
            wall_layer_text(room),
        )

    def test_a_row_is_two_columns_per_square_less_the_last_connector(self):
        ring = Maze.from_text("#####\n#...#\n#####")

        for row in wall_layer(ring):
            self.assertEqual(2 * ring.width - 1, len(row))

    def test_a_nineteen_square_maze_is_the_frame_s_maze_width(self):
        """Ties the layout to the frame constant rather than to a literal.

        19 squares at two columns each, less the final connector, is the 37
        the frame reserves — contradiction C-1 resolved the same way in both
        places.
        """
        maze = maze_for(0)

        self.assertEqual(19, maze.width)
        for row in wall_layer(maze):
            self.assertEqual(MAZE_COLUMNS, len(row))


class TheSpecimenPicture(unittest.TestCase):
    """The normative picture (assumption A6), reproduced character for character.

    The specimen's maze rows are inverted back into a grid of wall and
    corridor, and the resolver is asked to draw that grid.  What it produces
    must be the specimen's own wall characters, in their own places.

    The inversion classifies a square as wall by **Unicode block** — the Box
    Drawing block, plus the lone block this item owns — and not by looking
    anything up in the glyph table, so the table is not permitted to decide
    the question it is being asked.
    """

    #: The Unicode Box Drawing block, U+2500 .. U+257F.
    BOX_DRAWING = (0x2500, 0x257F)

    @classmethod
    def is_wall_glyph(cls, character):
        low, high = cls.BOX_DRAWING
        return low <= ord(character) <= high or character == LONE_WALL_GLYPH

    @classmethod
    def setUpClass(cls):
        cls.maze = Maze.from_text(
            "\n".join(
                "".join(
                    "#" if cls.is_wall_glyph(row[2 * column]) else "."
                    for column in range(19)
                )
                for row in SPECIMEN_MAZE_ROWS
            )
        )
        cls.expected = "\n".join(
            "".join(
                character if cls.is_wall_glyph(character) else " "
                for character in row
            )
            for row in SPECIMEN_MAZE_ROWS
        )

    def test_the_inverted_grid_is_the_nineteen_by_twenty_nine_of_maze_1(self):
        self.assertEqual(19, self.maze.width)
        self.assertEqual(29, self.maze.height)

    def test_the_inverted_grid_has_the_solid_border_of_maze_3(self):
        """A cheap check that the inversion above is not nonsense."""
        border = [Square(column, 0) for column in range(self.maze.width)]
        border += [
            Square(column, self.maze.height - 1)
            for column in range(self.maze.width)
        ]
        border += [Square(0, row) for row in range(self.maze.height)]
        border += [
            Square(self.maze.width - 1, row) for row in range(self.maze.height)
        ]

        for square in border:
            self.assertTrue(
                self.maze.is_wall(square), "%r is not wall" % (square,)
            )

    def test_the_resolver_reproduces_the_specimen_s_walls_exactly(self):
        self.assertEqual(self.expected, wall_layer_text(self.maze))

    def test_the_specimen_exercises_fifteen_of_the_sixteen_combinations(self):
        """And the one it does not is the crossing, which is why it is reasoned.

        This is the measurement the module's docstring rests on, kept where
        it can go stale rather than in prose nobody re-runs.
        """
        seen = {
            wall_glyph_at(self.maze, square)
            for square in self.maze.squares()
            if self.maze.is_wall(square)
        }

        self.assertEqual(set(WALL_GLYPHS.values()) - {CROSSING_GLYPH}, seen)


class DeclaresNothingItDoesNotOwn(unittest.TestCase):
    """The ownership boundary with WI-12, asserted rather than promised.

    WI-8 owns every wall glyph and the connector rule; WI-12 owns the dot and
    the two actor motifs.  The way to pin that from this side is to show that
    everything this module ever puts on screen is a wall character or a
    blank — so there is nowhere for a dot or a motif to have been smuggled
    in, and no need for this file to name one in order to say so.
    """

    def test_over_many_mazes_it_emits_only_wall_characters_and_blanks(self):
        allowed = set(WALL_GLYPHS.values()) | {BLANK_CONNECTOR_GLYPH}

        emitted = set()
        for seed in range(40):
            for row in wall_layer(maze_for(seed)):
                emitted.update(cell.glyph for cell in row)

        self.assertTrue(
            emitted <= allowed,
            "unexpected glyphs {0!r}".format(sorted(emitted - allowed)),
        )

    def test_over_many_mazes_blue_marks_ink_and_black_marks_nothing(self):
        """Every cell blue is a wall character; every blank is black ground.

        Stronger than "only two colours appear", and it is the form that
        matters: a blue blank would read the same on screen and differently
        in every colour assertion downstream.
        """
        for seed in range(40):
            for row in wall_layer(maze_for(seed)):
                for cell in row:
                    if cell.glyph == BLANK_CONNECTOR_GLYPH:
                        self.assertEqual(Colour.GROUND_BLACK, cell.colour)
                    else:
                        self.assertEqual(WALL_COLOUR, cell.colour)


class TheWallsOfARealMaze(unittest.TestCase):
    """Properties that must hold over generated mazes, not just fixtures."""

    def test_every_corridor_square_is_blank_and_every_wall_square_is_not(self):
        maze = maze_for(11)
        layer = wall_layer(maze)

        for square in maze.squares():
            cell = layer[square.row][2 * square.column]
            if maze.is_wall(square):
                self.assertNotEqual(BLANK_CONNECTOR_GLYPH, cell.glyph)
            else:
                self.assertEqual(BLANK, cell)

    def test_the_crossing_the_specimen_lacks_really_does_happen_in_play(self):
        """The one reasoned entry in the table is reachable, and often.

        Measured over the 200 shared seeds: the crossing appears 61 times, in
        55 of the 200 mazes, the first of them at seed 1 — see
        ``docs/findings/WI-8-glyph-census.md``.  So the entry the specimen
        picture could not confirm is not a theoretical corner: a player will
        see crossings, and if it were wrong they would see it.
        """
        maze = maze_for(1)

        crossings = [
            square
            for square in maze.squares()
            if maze.is_wall(square)
            and wall_glyph_at(maze, square) == CROSSING_GLYPH
        ]

        self.assertTrue(crossings, "seed 1 was measured to contain a crossing")

    def test_every_glyph_in_the_table_is_produced_by_some_real_maze(self):
        """No entry is dead code, and none is silently unreachable.

        Measured: the first ten shared seeds are enough for all twelve
        distinct characters.
        """
        glyphs = set()
        for seed in range(10):
            maze = maze_for(seed)
            glyphs.update(
                wall_glyph_at(maze, square)
                for square in maze.squares()
                if maze.is_wall(square)
            )

        self.assertEqual(set(WALL_GLYPHS.values()), glyphs)


if __name__ == "__main__":
    unittest.main()
