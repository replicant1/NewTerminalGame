# -*- coding: utf-8 -*-
"""Wall-glyph selection — SCRN-3.

Three independent things are checked here, deliberately not one:

1. **The specification's own picture**, parsed out of
   `docs/FUNCTIONAL_REQUIREMENTS.md` and rendered back through the table —
   287 wall squares drawn by whoever wrote the specification, compared glyph
   for glyph. This is the authority for the table and so the test reads the
   authority rather than a copy of it: edit the picture and this says the
   table needs rechecking, which is exactly what should happen.

2. **The Unicode names of the glyphs**, which know nothing about this project.
   `╠` is `BOX DRAWINGS DOUBLE VERTICAL AND RIGHT`, so it has arms to the
   north, south and east and to nowhere else. Checking the table against that
   is checking it against the standard rather than against itself — and it is
   what catches an inverted axis, because `╚` is `UP AND RIGHT` and `up` is
   `y - 1`.

3. **Generated mazes**, where the border ring and the joining-up of adjacent
   walls are properties of the whole picture rather than of one square.

The thing to keep in mind for (2) and (3): a table test is the easiest kind of
test to write vacuously. Walking `BY_NEIGHBOURS` and asserting each entry
equals itself is green forever and says nothing. Every assertion below is
against something that was not derived from `BY_NEIGHBOURS`.
"""

from __future__ import annotations

import io
import os
import unicodedata
import unittest

import curses

import terminalgame
from terminalgame.domain.maze import CORRIDOR, WALL, Maze, solid
from terminalgame.domain.maze_generator import generate_maze
from terminalgame.screen.curses_adapter import _palette
from terminalgame.screen.port import Colour
from terminalgame.presentation.wall_glyphs import (
    BY_NEIGHBOURS,
    CROSSING,
    DOWN_AND_HORIZONTAL,
    DOWN_AND_LEFT,
    DOWN_AND_RIGHT,
    GLYPHS,
    HORIZONTAL,
    LONE_BLOCK,
    NotAWallSquare,
    UP_AND_HORIZONTAL,
    UP_AND_LEFT,
    UP_AND_RIGHT,
    VERTICAL,
    VERTICAL_AND_LEFT,
    VERTICAL_AND_RIGHT,
    WALL_COLOUR,
    glyph_for_neighbours,
    wall_glyph,
    wall_glyphs,
    wall_neighbours,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(terminalgame.__file__)))
SPECIFICATION = os.path.join(REPO_ROOT, "docs", "FUNCTIONAL_REQUIREMENTS.md")

#: The picture is 19 squares across drawn two terminal columns to a square,
#: with the columns between squares shared — so 2 x 19 - 1.
PICTURE_WIDTH = 37
PICTURE_HEIGHT = 29

ALL_PATTERNS = [(n, s, e, w)
                for n in (False, True) for s in (False, True)
                for e in (False, True) for w in (False, True)]


def specification_picture():
    """The 29 maze rows of the specification's worked example.

    Raises rather than skipping if the picture cannot be found: a skipped test
    here would quietly remove the only external authority the table has.
    """
    with io.open(SPECIFICATION, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "```" and lines[index + 1].startswith(VERTICAL_AND_RIGHT[0]):
            pass  # not the fence we want; keep the check below honest
    fences = [index for index, line in enumerate(lines)
              if line.strip() == "```" and index + 1 < len(lines)
              and lines[index + 1].startswith(DOWN_AND_RIGHT)]
    if not fences:
        raise AssertionError(
            "no maze picture found in {0} — it should be a fenced block whose "
            "first line starts with {1}. If the specification has been "
            "reformatted, the wall-glyph table needs rechecking against it."
            .format(SPECIFICATION, DOWN_AND_RIGHT))
    rows = []
    for line in lines[fences[0] + 1:]:
        if line.strip() == "```":
            break
        # The picture carries two annotations to its right, introduced by an
        # arrow; they are commentary and not part of the frame.
        rows.append(line.split(u"   ←")[0])
    return rows[:PICTURE_HEIGHT]


def picture_glyphs(rows):
    """The character drawn for each square: square x is at column 2x."""
    return [[row[2 * x] if 2 * x < len(row) else u" " for x in range(19)]
            for row in rows]


def maze_from_picture(drawn):
    """The maze the picture depicts — a square is wall if a wall glyph is on it."""
    return Maze([[WALL if drawn[y][x] in GLYPHS else CORRIDOR for x in range(19)]
                 for y in range(PICTURE_HEIGHT)])


def arms_of(glyph):
    """Which sides a glyph reaches towards, taken from its Unicode name.

    Independent of anything in this project: `unicodedata` is reporting the
    Unicode standard's own description of the character. `UP` is north because
    north is `y - 1`; if that were ever reversed, half the corners below would
    fail.
    """
    name = unicodedata.name(glyph)
    if name == "BLACK SQUARE":
        return frozenset()
    if not name.startswith("BOX DRAWINGS DOUBLE "):
        raise AssertionError("{0!r} is not a double-line box glyph: {1}"
                             .format(glyph, name))
    words = name[len("BOX DRAWINGS DOUBLE "):].split(" AND ")
    sides = set()
    for word in words:
        sides.update({"UP": ["north"], "DOWN": ["south"],
                      "RIGHT": ["east"], "LEFT": ["west"],
                      "VERTICAL": ["north", "south"],
                      "HORIZONTAL": ["east", "west"]}[word])
    return frozenset(sides)


def sides_of(pattern):
    """A `(north, south, east, west)` tuple as a set of side names."""
    return frozenset(name for name, present
                     in zip(("north", "south", "east", "west"), pattern)
                     if present)


class ThePictureInTheSpecificationTest(unittest.TestCase):
    """The table against 287 wall squares somebody else drew."""

    @classmethod
    def setUpClass(cls):
        cls.rows = specification_picture()
        cls.drawn = picture_glyphs(cls.rows)
        cls.maze = maze_from_picture(cls.drawn)

    def test_the_picture_is_the_shape_the_geometry_says_it_is(self):
        # If this fails, the parsing below is looking at the wrong thing and
        # every other result in this class is worthless.
        self.assertEqual(PICTURE_HEIGHT, len(self.rows))
        for index, row in enumerate(self.rows):
            self.assertEqual(PICTURE_WIDTH, len(row.rstrip("\n")),
                             "row {0} of the picture".format(index))

    def test_the_picture_is_a_nineteen_by_twenty_nine_maze(self):
        self.assertEqual((19, 29), (self.maze.width, self.maze.height))

    def test_the_picture_has_the_number_of_wall_squares_it_was_measured_to_have(self):
        # Guards the parse rather than the table: if a change to the document
        # silently halved what is read, every glyph comparison would still
        # pass on the squares that remained.
        walls = 19 * 29 - len(self.maze.corridor_squares())
        self.assertEqual(287, walls)
        self.assertEqual(264, len(self.maze.corridor_squares()))

    def test_every_wall_square_of_the_picture_is_drawn_as_the_table_says(self):
        wrong = []
        for (x, y) in self.maze.squares():
            if not self.maze.is_wall(x, y):
                continue
            drawn = self.drawn[y][x]
            computed = wall_glyph(self.maze, x, y)
            if drawn != computed:
                wrong.append((x, y, drawn, computed))
        self.assertEqual([], wrong,
                         u"the table disagrees with the specification's "
                         u"picture at {0} squares; first few: {1}"
                         .format(len(wrong), wrong[:8]))

    def test_the_picture_exercises_fifteen_of_the_sixteen_patterns(self):
        # Says how much of the table the picture actually vouches for. The
        # crossing is the one it does not, and SCRN-3's own word "crossings"
        # is the authority for that entry instead.
        seen = set()
        for (x, y) in self.maze.squares():
            if self.maze.is_wall(x, y):
                seen.add(wall_neighbours(self.maze, x, y))
        self.assertEqual(15, len(seen))
        self.assertNotIn((True, True, True, True), seen)

    def test_the_picture_never_draws_one_pattern_two_ways(self):
        # The property that makes the picture usable as an authority at all.
        by_pattern = {}
        for (x, y) in self.maze.squares():
            if not self.maze.is_wall(x, y):
                continue
            pattern = wall_neighbours(self.maze, x, y)
            by_pattern.setdefault(pattern, set()).add(self.drawn[y][x])
        ambiguous = {k: sorted(v) for k, v in by_pattern.items() if len(v) > 1}
        self.assertEqual({}, ambiguous)

    def test_the_illustrative_maze_obeys_the_maze_requirements(self):
        # Not strictly WI-5a's business, but it is free here and it is worth
        # knowing: the maze somebody drew by hand for the specification is one
        # WI-4's generator could have produced.
        from tests.test_maze_generator import (border_breaches, dead_ends,
                                               open_two_by_two_blocks,
                                               squares_off_the_lattice,
                                               unreachable_squares)
        self.assertEqual([], border_breaches(self.maze))
        self.assertEqual([], open_two_by_two_blocks(self.maze))
        self.assertEqual([], dead_ends(self.maze))
        self.assertEqual([], unreachable_squares(self.maze))
        self.assertEqual([], squares_off_the_lattice(self.maze))


class TheGlyphsAgreeWithUnicodeTest(unittest.TestCase):
    """The table against the Unicode standard, which never heard of this game."""

    def test_every_wall_neighbour_has_an_arm_pointing_at_it(self):
        # SCRN-3's "join up neatly with their neighbours", stated so that it
        # can fail. Nothing here reads BY_NEIGHBOURS to decide what is right.
        for pattern in ALL_PATTERNS:
            glyph = glyph_for_neighbours(*pattern)
            missing = sides_of(pattern) - arms_of(glyph)
            self.assertEqual(frozenset(), missing,
                             u"{0} has no arm towards {1} but the wall "
                             u"continues that way".format(glyph, sorted(missing)))

    def test_the_glyph_chosen_is_the_one_with_the_fewest_spare_arms(self):
        # Why a lone-north wall is ║ and not ╬: both have a north arm, and ║
        # has one spare arm where ╬ has three. This is the whole of the
        # "no half-lines exist" argument, checked rather than asserted.
        for pattern in ALL_PATTERNS:
            wanted = sides_of(pattern)
            chosen = glyph_for_neighbours(*pattern)
            candidates = [g for g in GLYPHS if wanted <= arms_of(g)]
            best = min(len(arms_of(g)) for g in candidates)
            self.assertEqual(best, len(arms_of(chosen)),
                             u"for {0} the table chose {1} with arms {2}, but "
                             u"{3} arms would do"
                             .format(sorted(wanted), chosen,
                                     sorted(arms_of(chosen)), best))

    def test_a_glyph_with_two_or_more_neighbours_has_exactly_those_arms(self):
        # Above two neighbours the double-line set has an exact character, so
        # "fewest spare arms" should mean none at all.
        for pattern in ALL_PATTERNS:
            wanted = sides_of(pattern)
            if len(wanted) < 2:
                continue
            self.assertEqual(wanted, arms_of(glyph_for_neighbours(*pattern)),
                             u"pattern {0}".format(sorted(wanted)))

    def test_north_is_up_and_south_is_down(self):
        # The inverted-axis trap, pinned on its own rather than left to be
        # inferred from a corner. y counts down from the top, so the glyph for
        # "wall above me and wall to my right" is UP AND RIGHT.
        self.assertEqual("BOX DRAWINGS DOUBLE UP AND RIGHT",
                         unicodedata.name(glyph_for_neighbours(
                             north=True, south=False, east=True, west=False)))
        self.assertEqual("BOX DRAWINGS DOUBLE DOWN AND LEFT",
                         unicodedata.name(glyph_for_neighbours(
                             north=False, south=True, east=False, west=True)))

    def test_the_lone_block_is_the_only_glyph_with_no_arms(self):
        # SCRN-3: "a wall square with no wall next to it is drawn as a single
        # blue block."
        armless = [g for g in GLYPHS if not arms_of(g)]
        self.assertEqual([LONE_BLOCK], armless)
        self.assertEqual(LONE_BLOCK, glyph_for_neighbours(False, False, False, False))


class TheTableItselfTest(unittest.TestCase):

    def test_all_sixteen_patterns_are_in_the_table(self):
        self.assertEqual(16, len(BY_NEIGHBOURS))
        for pattern in ALL_PATTERNS:
            self.assertIn(pattern, BY_NEIGHBOURS)

    def test_every_entry_is_one_of_the_named_glyphs(self):
        for pattern, glyph in BY_NEIGHBOURS.items():
            self.assertIn(glyph, GLYPHS, pattern)
            self.assertEqual(1, len(glyph), pattern)

    def test_the_named_glyphs_are_the_characters_they_say_they_are(self):
        # The names in the module are the only thing making the table
        # readable; if one were pasted wrong the table would still "work" and
        # nobody reviewing it could tell.
        self.assertEqual("BOX DRAWINGS DOUBLE HORIZONTAL", unicodedata.name(HORIZONTAL))
        self.assertEqual("BOX DRAWINGS DOUBLE VERTICAL", unicodedata.name(VERTICAL))
        self.assertEqual("BOX DRAWINGS DOUBLE DOWN AND RIGHT", unicodedata.name(DOWN_AND_RIGHT))
        self.assertEqual("BOX DRAWINGS DOUBLE DOWN AND LEFT", unicodedata.name(DOWN_AND_LEFT))
        self.assertEqual("BOX DRAWINGS DOUBLE UP AND RIGHT", unicodedata.name(UP_AND_RIGHT))
        self.assertEqual("BOX DRAWINGS DOUBLE UP AND LEFT", unicodedata.name(UP_AND_LEFT))
        self.assertEqual("BOX DRAWINGS DOUBLE VERTICAL AND RIGHT", unicodedata.name(VERTICAL_AND_RIGHT))
        self.assertEqual("BOX DRAWINGS DOUBLE VERTICAL AND LEFT", unicodedata.name(VERTICAL_AND_LEFT))
        self.assertEqual("BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL", unicodedata.name(DOWN_AND_HORIZONTAL))
        self.assertEqual("BOX DRAWINGS DOUBLE UP AND HORIZONTAL", unicodedata.name(UP_AND_HORIZONTAL))
        self.assertEqual("BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL", unicodedata.name(CROSSING))
        self.assertEqual("BLACK SQUARE", unicodedata.name(LONE_BLOCK))

    def test_the_twelve_named_glyphs_are_all_different(self):
        self.assertEqual(12, len(set(GLYPHS)))

    def test_the_mapping_depends_on_the_four_neighbours_and_nothing_else(self):
        # The plan's words. Two wall squares with the same neighbours are
        # drawn the same, whatever maze they are in and wherever they sit --
        # so the check is over squares from different mazes at different
        # coordinates, grouped by pattern.
        by_pattern = {}
        for seed in range(30):
            maze = generate_maze(seed)
            for (x, y) in maze.squares():
                if not maze.is_wall(x, y):
                    continue
                pattern = wall_neighbours(maze, x, y)
                glyph = wall_glyph(maze, x, y)
                by_pattern.setdefault(pattern, set()).add(glyph)
        self.assertGreater(len(by_pattern), 8)
        for pattern, glyphs in by_pattern.items():
            self.assertEqual(1, len(glyphs),
                             u"pattern {0} drawn as {1}".format(pattern, sorted(glyphs)))

    def test_the_arguments_are_read_in_the_order_north_south_east_west(self):
        # Positional callers are the normal case, so the order is part of the
        # interface. These four differ only by which single side is set.
        self.assertEqual(glyph_for_neighbours(north=True, south=False, east=True, west=False),
                         glyph_for_neighbours(True, False, True, False))
        self.assertEqual(UP_AND_RIGHT, glyph_for_neighbours(True, False, True, False))
        self.assertEqual(DOWN_AND_LEFT, glyph_for_neighbours(False, True, False, True))
        self.assertEqual(VERTICAL_AND_RIGHT, glyph_for_neighbours(True, True, True, False))
        self.assertEqual(DOWN_AND_HORIZONTAL, glyph_for_neighbours(False, True, True, True))


class TheColourTest(unittest.TestCase):

    def test_the_wall_colour_is_the_specification_s_wall_colour(self):
        self.assertEqual(Colour.WALL, WALL_COLOUR)

    def test_that_colour_reaches_the_terminal_as_blue(self):
        # SCRN-3 says blue, and "the colour is blue" is what the plan asks
        # this item to establish -- so follow it to the end rather than
        # stopping at a name. The adapter is the only thing that knows what a
        # colour means; this reads its palette.
        colour, attributes = _palette(curses)[WALL_COLOUR]
        self.assertEqual(curses.COLOR_BLUE, colour)
        self.assertEqual(0, attributes)

    def test_every_wall_square_is_the_same_colour(self):
        # SCRN-3 varies the character with the neighbours, never the colour.
        maze = generate_maze(3)
        self.assertEqual(Colour.WALL, WALL_COLOUR)
        self.assertNotIn(WALL_COLOUR, (Colour.DOT, Colour.PLAYER,
                                       Colour.GHOST, Colour.STATUS,
                                       Colour.DEFAULT))
        self.assertGreater(len(wall_glyphs(maze)), 0)


class AgainstGeneratedMazesTest(unittest.TestCase):
    """Properties of the whole picture rather than of one square."""

    SEEDS = range(40)

    def test_the_border_ring_is_drawn_as_a_rectangle(self):
        # This is the off-the-grid convention, seen from the outside. Get it
        # wrong and every corner becomes a crossing -- which still looks like
        # a maze, which is why it needs a test rather than an eye.
        for seed in self.SEEDS:
            maze = generate_maze(seed)
            last_x, last_y = maze.width - 1, maze.height - 1
            self.assertEqual(DOWN_AND_RIGHT, wall_glyph(maze, 0, 0), seed)
            self.assertEqual(DOWN_AND_LEFT, wall_glyph(maze, last_x, 0), seed)
            self.assertEqual(UP_AND_RIGHT, wall_glyph(maze, 0, last_y), seed)
            self.assertEqual(UP_AND_LEFT, wall_glyph(maze, last_x, last_y), seed)

    def test_the_border_edges_are_straights_or_tees_and_never_corners(self):
        for seed in self.SEEDS:
            maze = generate_maze(seed)
            last_x, last_y = maze.width - 1, maze.height - 1
            for x in range(1, last_x):
                self.assertIn(wall_glyph(maze, x, 0),
                              (HORIZONTAL, DOWN_AND_HORIZONTAL), (seed, x, "top"))
                self.assertIn(wall_glyph(maze, x, last_y),
                              (HORIZONTAL, UP_AND_HORIZONTAL), (seed, x, "bottom"))
            for y in range(1, last_y):
                self.assertIn(wall_glyph(maze, 0, y),
                              (VERTICAL, VERTICAL_AND_RIGHT), (seed, y, "left"))
                self.assertIn(wall_glyph(maze, last_x, y),
                              (VERTICAL, VERTICAL_AND_LEFT), (seed, y, "right"))

    def test_adjacent_wall_squares_agree_about_the_edge_between_them(self):
        # The joining-up property, over whole mazes: wherever two wall squares
        # touch, both glyphs reach towards each other. Neither side of this is
        # read from the table -- the arms come from Unicode.
        for seed in self.SEEDS:
            maze = generate_maze(seed)
            for (x, y) in maze.squares():
                if not maze.is_wall(x, y):
                    continue
                here = arms_of(wall_glyph(maze, x, y))
                for side, opposite, nx, ny in (
                        ("east", "west", x + 1, y),
                        ("south", "north", x, y + 1)):
                    if not (maze.contains(nx, ny) and maze.is_wall(nx, ny)):
                        continue
                    there = arms_of(wall_glyph(maze, nx, ny))
                    self.assertIn(side, here, (seed, x, y, side))
                    self.assertIn(opposite, there, (seed, nx, ny, opposite))

    def test_an_arm_may_point_at_a_corridor_and_only_in_the_documented_case(self):
        # The double-line set has no half-lines, so a wall with a single wall
        # neighbour is a straight and one of its arms points at a corridor.
        # The specification's picture does this too (`════ ▪`). What must
        # never happen is a *corner or tee* with a spare arm.
        for seed in self.SEEDS:
            maze = generate_maze(seed)
            for (x, y) in maze.squares():
                if not maze.is_wall(x, y):
                    continue
                pattern = wall_neighbours(maze, x, y)
                spare = arms_of(wall_glyph(maze, x, y)) - sides_of(pattern)
                if len(sides_of(pattern)) == 1:
                    self.assertEqual(1, len(spare), (seed, x, y))
                else:
                    self.assertEqual(frozenset(), spare, (seed, x, y))

    def test_every_wall_square_gets_a_glyph_and_no_corridor_square_does(self):
        for seed in self.SEEDS:
            maze = generate_maze(seed)
            listed = wall_glyphs(maze)
            walls = [(x, y) for (x, y) in maze.squares() if maze.is_wall(x, y)]
            self.assertEqual(walls, [(x, y) for x, y, _ in listed], seed)
            for _, _, glyph in listed:
                self.assertIn(glyph, GLYPHS)

    def test_wall_glyphs_comes_back_in_reading_order(self):
        listed = wall_glyphs(generate_maze(11))
        coordinates = [(x, y) for x, y, _ in listed]
        self.assertEqual(sorted(coordinates, key=lambda c: (c[1], c[0])),
                         coordinates)


class RefusingTheQuestionTest(unittest.TestCase):
    """Plan §11.8 — refuse where the argument makes the requirement impossible."""

    def test_a_corridor_square_has_no_wall_glyph(self):
        maze = generate_maze(5)
        corridor = maze.corridor_squares()[0]
        with self.assertRaises(NotAWallSquare):
            wall_glyph(maze, *corridor)

    def test_the_refusal_names_the_square(self):
        maze = generate_maze(5)
        x, y = maze.corridor_squares()[0]
        try:
            wall_glyph(maze, x, y)
        except NotAWallSquare as refused:
            self.assertEqual((x, y), (refused.x, refused.y))
            self.assertIn(str(x), str(refused))
            self.assertIn("SCRN-3", str(refused))
        else:
            self.fail("a corridor square was given a wall glyph")

    def test_a_square_off_the_grid_has_no_wall_glyph(self):
        # Even though `square_at` would call it wall. The two questions differ
        # and this is the one place the difference is visible from outside.
        maze = generate_maze(5)
        self.assertTrue(maze.is_wall(-1, -1))
        with self.assertRaises(NotAWallSquare):
            wall_glyph(maze, -1, -1)
        with self.assertRaises(NotAWallSquare):
            wall_glyph(maze, maze.width, 0)


class NeighbourQueryTest(unittest.TestCase):
    """`wall_neighbours` is where the off-the-grid rule actually lives."""

    def test_a_lone_wall_square_has_no_wall_neighbours(self):
        maze = Maze.from_text(u"...\n.#.\n...", wall="#")
        self.assertEqual((False, False, False, False), wall_neighbours(maze, 1, 1))
        self.assertEqual(LONE_BLOCK, wall_glyph(maze, 1, 1))

    def test_off_the_grid_does_not_count_as_a_wall_neighbour(self):
        # A single wall square filling a 1 x 1 maze: `square_at` says every
        # side is wall, `wall_neighbours` says none is.
        maze = Maze(solid(1, 1))
        self.assertTrue(maze.is_wall(0, -1))
        self.assertEqual((False, False, False, False), wall_neighbours(maze, 0, 0))
        self.assertEqual(LONE_BLOCK, wall_glyph(maze, 0, 0))

    def test_the_four_sides_are_read_from_the_right_squares(self):
        # A cross of wall with one arm removed, so each side is distinguishable
        # rather than symmetric.
        maze = Maze.from_text(u".#.\n###\n...", wall="#")
        self.assertEqual((True, False, True, True), wall_neighbours(maze, 1, 1))
        self.assertEqual((False, True, False, False), wall_neighbours(maze, 1, 0))
        self.assertEqual((False, False, True, False), wall_neighbours(maze, 0, 1))
        self.assertEqual((False, False, False, True), wall_neighbours(maze, 2, 1))

    def test_that_cross_is_drawn_as_the_picture_would_draw_it(self):
        maze = Maze.from_text(u".#.\n###\n...", wall="#")
        self.assertEqual(UP_AND_HORIZONTAL, wall_glyph(maze, 1, 1))
        self.assertEqual(VERTICAL, wall_glyph(maze, 1, 0))
        self.assertEqual(HORIZONTAL, wall_glyph(maze, 0, 1))
        self.assertEqual(HORIZONTAL, wall_glyph(maze, 2, 1))

    def test_a_full_cross_is_the_crossing(self):
        # The one pattern the specification's picture never shows.
        maze = Maze.from_text(u".#.\n###\n.#.", wall="#")
        self.assertEqual((True, True, True, True), wall_neighbours(maze, 1, 1))
        self.assertEqual(CROSSING, wall_glyph(maze, 1, 1))


if __name__ == "__main__":
    unittest.main()
