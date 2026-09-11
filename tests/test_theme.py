# -*- coding: utf-8 -*-
"""The glyph and colour tables — SCRN-3..6, STAT-1..3.

The sixteen wall masks are asserted **exhaustively** against the table
decoded from the specification's own mock-up, and the decoding happens here,
in the test, from the fixture — so if anybody ever edits
:data:`termgame.theme.WALL_GLYPHS` to disagree with the specification, this
file says so.
"""

import ast
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from termgame import maze as mazelib  # noqa: E402
from termgame import theme  # noqa: E402
from termgame.model import MAZE_COLS, MAZE_ROWS, Outcome, Position  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

#: In the mock-up an even picture column holds one of these when the maze
#: cell under it is corridor: a dot, or the middle of a three-character
#: player/ghost glyph.
SPEC_CORRIDOR_CHARS = frozenset(u"▪█")


def read_mock_up():
    """The specification's picture, as its 29 lines of 37 characters."""
    path = os.path.join(FIXTURES, "spec_maze.txt")
    with io.open(path, encoding="utf-8") as handle:
        return [line for line in handle.read().split("\n") if line]


def decode_wall_table(lines):
    """Read the mask-to-glyph table straight off the mock-up.

    Returns ``{mask: {glyph: count}}``. A mask with more than one glyph would
    mean the rule is not a pure function of the mask at all.
    """
    grid = [
        [lines[r][2 * c] not in SPEC_CORRIDOR_CHARS for c in range(MAZE_COLS)]
        for r in range(MAZE_ROWS)
    ]

    def is_wall(r, c):
        if 0 <= r < MAZE_ROWS and 0 <= c < MAZE_COLS:
            return grid[r][c]
        return False

    table = {}
    for r in range(MAZE_ROWS):
        for c in range(MAZE_COLS):
            if not grid[r][c]:
                continue
            mask = 0
            if is_wall(r - 1, c):
                mask |= theme.NORTH
            if is_wall(r + 1, c):
                mask |= theme.SOUTH
            if is_wall(r, c + 1):
                mask |= theme.EAST
            if is_wall(r, c - 1):
                mask |= theme.WEST
            seen = table.setdefault(mask, {})
            glyph = lines[r][2 * c]
            seen[glyph] = seen.get(glyph, 0) + 1
    return table


class TestTheWallGlyphTableAgainstTheSpecification(unittest.TestCase):
    """SCRN-3 — all sixteen masks, exhaustively, not sampled."""

    @classmethod
    def setUpClass(cls):
        cls.decoded = decode_wall_table(read_mock_up())

    def test_the_mock_up_settles_fifteen_of_the_sixteen_masks(self):
        # If this ever stops being 15, the premise of the table has changed
        # and the inferred entry below is no longer the only inferred one.
        self.assertEqual(len(self.decoded), 15)
        self.assertNotIn(theme.INFERRED_MASK, self.decoded)

    def test_every_mask_the_mock_up_settles_settles_it_unambiguously(self):
        # A mask drawn with two different glyphs would mean the glyph is not
        # a function of the mask, and the whole rule would be wrong.
        for mask, glyphs in sorted(self.decoded.items()):
            self.assertEqual(
                len(glyphs),
                1,
                "mask %s (%d) is drawn as %s in the mock-up"
                % (theme.mask_name(mask), mask, sorted(glyphs)),
            )

    def test_all_sixteen_masks_match_the_mock_up(self):
        # The exhaustive assertion the plan asks for. Fifteen come from the
        # document; the sixteenth is named as inferred and asserted here so
        # that changing it is a deliberate act.
        expected = {}
        for mask, glyphs in self.decoded.items():
            expected[mask] = list(glyphs)[0]
        expected[theme.INFERRED_MASK] = u"╬"

        self.assertEqual(len(expected), 16)
        for mask in theme.ALL_MASKS:
            self.assertEqual(
                theme.glyph_for_mask(mask),
                expected[mask],
                "mask %s (%d)" % (theme.mask_name(mask), mask),
            )

    def test_the_named_cases_are_the_ones_the_specification_describes(self):
        # SCRN-3 calls out exactly two shapes in prose: a lone wall square,
        # and walls that join into corners, tees and crossings.
        self.assertEqual(theme.glyph_for_mask(0), u"■")
        self.assertEqual(theme.glyph_for_mask(theme.NORTH | theme.SOUTH), u"║")
        self.assertEqual(theme.glyph_for_mask(theme.EAST | theme.WEST), u"═")
        self.assertEqual(theme.glyph_for_mask(theme.SOUTH | theme.EAST), u"╔")
        self.assertEqual(theme.glyph_for_mask(theme.SOUTH | theme.WEST), u"╗")
        self.assertEqual(theme.glyph_for_mask(theme.NORTH | theme.EAST), u"╚")
        self.assertEqual(theme.glyph_for_mask(theme.NORTH | theme.WEST), u"╝")
        self.assertEqual(
            theme.glyph_for_mask(theme.NORTH | theme.SOUTH | theme.EAST), u"╠"
        )
        self.assertEqual(
            theme.glyph_for_mask(theme.NORTH | theme.SOUTH | theme.WEST), u"╣"
        )
        self.assertEqual(
            theme.glyph_for_mask(theme.SOUTH | theme.EAST | theme.WEST), u"╦"
        )
        self.assertEqual(
            theme.glyph_for_mask(theme.NORTH | theme.EAST | theme.WEST), u"╩"
        )
        self.assertEqual(theme.glyph_for_mask(15), u"╬")

    def test_a_mask_outside_four_bits_is_refused(self):
        for bad in (-1, 16, 99):
            with self.assertRaises(ValueError):
                theme.glyph_for_mask(bad)

    def test_the_table_has_exactly_sixteen_entries(self):
        self.assertEqual(len(theme.WALL_GLYPHS), 16)
        for glyph in theme.WALL_GLYPHS:
            self.assertEqual(len(glyph), 1)


class TestTheMaskItself(unittest.TestCase):
    """The mask is computed from *cell* neighbours, and off-grid is not wall."""

    def test_a_lone_wall_square_in_open_ground_has_mask_zero(self):
        maze = mazelib.from_text("\n".join([".....", ".....", "..#..", ".....", "....."]))
        self.assertEqual(theme.wall_mask(maze, Position(2, 2)), 0)
        self.assertEqual(theme.wall_glyph(maze, Position(2, 2)), u"■")

    def test_each_bit_is_set_by_exactly_the_neighbour_it_names(self):
        cases = (
            (["...", ".#.", "..."], 0),
            ([".#.", ".#.", "..."], theme.NORTH),
            (["...", ".#.", ".#."], theme.SOUTH),
            (["...", ".##", "..."], theme.EAST),
            (["...", "##.", "..."], theme.WEST),
            ([".#.", "###", ".#."], theme.NORTH | theme.SOUTH | theme.EAST | theme.WEST),
        )
        for rows, expected in cases:
            maze = mazelib.from_text("\n".join(rows))
            self.assertEqual(
                theme.wall_mask(maze, Position(1, 1)),
                expected,
                "%r should give %s" % (rows, theme.mask_name(expected)),
            )

    def test_the_outside_of_the_grid_does_not_count_as_wall(self):
        # This is the opposite of Maze.is_wall, and deliberately so: the
        # maze's border would otherwise draw itself joining on to nothing.
        # The mock-up's top-left corner is the witness.
        maze = mazelib.from_text("\n".join(["###", "#.#", "###"]))
        self.assertTrue(maze.is_wall((-1, 0)), "Maze.is_wall says off-grid is wall")
        self.assertFalse(theme.neighbour_is_wall(maze, -1, 0))
        self.assertEqual(theme.wall_mask(maze, Position(0, 0)), theme.SOUTH | theme.EAST)
        self.assertEqual(theme.wall_glyph(maze, Position(0, 0)), u"╔")
        self.assertEqual(theme.wall_glyph(maze, Position(0, 2)), u"╗")
        self.assertEqual(theme.wall_glyph(maze, Position(2, 0)), u"╚")
        self.assertEqual(theme.wall_glyph(maze, Position(2, 2)), u"╝")

    def test_the_mock_ups_own_four_corners_come_out_as_drawn(self):
        lines = read_mock_up()
        grid = "\n".join(
            "".join(
                "." if lines[r][2 * c] in SPEC_CORRIDOR_CHARS else "#"
                for c in range(MAZE_COLS)
            )
            for r in range(MAZE_ROWS)
        )
        maze = mazelib.from_text(grid)
        self.assertEqual(theme.wall_glyph(maze, Position(0, 0)), lines[0][0])
        self.assertEqual(theme.wall_glyph(maze, Position(0, 18)), lines[0][36])
        self.assertEqual(theme.wall_glyph(maze, Position(28, 0)), lines[28][0])
        self.assertEqual(theme.wall_glyph(maze, Position(28, 18)), lines[28][36])


class TestTheJoinerRule(unittest.TestCase):
    """SCRN-3 — the odd columns, and the invariant the entities rely on."""

    def test_a_joiner_between_two_wall_cells_is_a_bar(self):
        maze = mazelib.from_text("\n".join(["###", "...", "..."]))
        self.assertTrue(theme.joins_horizontally(maze, 0, 0))
        self.assertEqual(theme.joiner_glyph(maze, 0, 0), u"═")

    def test_a_joiner_beside_a_corridor_cell_is_blank(self):
        maze = mazelib.from_text("\n".join(["#.#", "...", "..."]))
        self.assertFalse(theme.joins_horizontally(maze, 0, 0))
        self.assertFalse(theme.joins_horizontally(maze, 0, 1))
        self.assertEqual(theme.joiner_glyph(maze, 0, 0), u" ")
        self.assertEqual(theme.joiner_glyph(maze, 0, 1), u" ")

    def test_the_rule_reproduces_every_joiner_column_of_the_mock_up(self):
        lines = read_mock_up()
        grid = "\n".join(
            "".join(
                "." if lines[r][2 * c] in SPEC_CORRIDOR_CHARS else "#"
                for c in range(MAZE_COLS)
            )
            for r in range(MAZE_ROWS)
        )
        maze = mazelib.from_text(grid)
        # Everywhere except the four columns the player and the ghost spill
        # into -- which is the point of the spill, and is asserted in
        # test_view.py.
        spill = {(13, 19), (13, 21), (27, 1), (27, 3)}
        for r in range(MAZE_ROWS):
            for c in range(MAZE_COLS - 1):
                if (r, 2 * c + 1) in spill:
                    continue
                self.assertEqual(
                    theme.joiner_glyph(maze, r, c),
                    lines[r][2 * c + 1],
                    "joiner at picture (%d, %d)" % (r, 2 * c + 1),
                )


class TestTheStyleTable(unittest.TestCase):
    """SCRN-3..6 — a style identifier for each colour the spec names."""

    def test_there_is_a_style_for_every_colour_the_specification_names(self):
        for name in (
            theme.STYLE_WALL,
            theme.STYLE_DOT,
            theme.STYLE_PLAYER,
            theme.STYLE_GHOST,
            theme.STYLE_STATUS,
        ):
            self.assertIn(name, theme.STYLES)
            self.assertEqual(theme.STYLES[name].name, name)

    def test_the_names_tuple_and_the_table_agree(self):
        self.assertEqual(sorted(theme.STYLE_NAMES), sorted(theme.STYLES))
        self.assertEqual(len(theme.STYLE_NAMES), len(set(theme.STYLE_NAMES)))

    def test_the_dots_are_dim_and_the_player_is_bright(self):
        # SCRN-4 "dim gold", SCRN-5 "bright yellow".
        self.assertIn(theme.ATTR_DIM, theme.STYLES[theme.STYLE_DOT].attributes)
        self.assertIn(theme.ATTR_BOLD, theme.STYLES[theme.STYLE_PLAYER].attributes)

    def test_the_player_and_the_ghost_differ_in_colour_and_in_outline(self):
        # SCRN-5: "so the two can be told apart by colour and by outline".
        player = theme.STYLES[theme.STYLE_PLAYER]
        ghost = theme.STYLES[theme.STYLE_GHOST]
        self.assertNotEqual(player.colour, ghost.colour)
        self.assertNotEqual(theme.PLAYER_GLYPHS, theme.GHOST_GLYPHS)
        self.assertNotEqual(theme.PLAYER_GLYPHS[0], theme.GHOST_GLYPHS[0])
        self.assertNotEqual(theme.PLAYER_GLYPHS[2], theme.GHOST_GLYPHS[2])

    def test_every_style_has_a_distinct_colour(self):
        colours = [theme.STYLES[n].colour for n in theme.STYLE_NAMES]
        self.assertEqual(len(colours), len(set(colours)))

    def test_every_colour_is_a_256_colour_index(self):
        # The architecture measured COLORS = 256 on this machine.
        for name in theme.STYLE_NAMES:
            colour = theme.STYLES[name].colour
            self.assertIsInstance(colour, int)
            self.assertTrue(0 <= colour < 256, "%s -> %r" % (name, colour))

    def test_only_the_two_known_attribute_names_are_used(self):
        # The curses adapter has to understand every one of these, so the
        # list it must cover is closed.
        for name in theme.STYLE_NAMES:
            for attr in theme.STYLES[name].attributes:
                self.assertIn(attr, theme.ATTRIBUTE_NAMES)

    def test_a_style_identifier_is_a_plain_string_not_a_curses_constant(self):
        for name in theme.STYLE_NAMES:
            self.assertIsInstance(name, str)

    def test_the_module_uses_no_curses_identifier_anywhere(self):
        # A_BOLD / A_DIM / COLOR_PAIR used as *code* would mean the seam had
        # been crossed. The prose is allowed to name them -- it has to, to
        # say what the adapter is expected to do with "bold" and "dim" --
        # so this looks at identifiers, not at the text of the file.
        forbidden = {
            "A_BOLD",
            "A_DIM",
            "A_NORMAL",
            "COLOR_PAIR",
            "init_pair",
            "color_pair",
            "curses",
        }
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "termgame",
            "theme.py",
        )
        with io.open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, forbidden, "line %d" % node.lineno)
            elif isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, forbidden, "line %d" % node.lineno)


class TestTheThreeStatusStrings(unittest.TestCase):
    """STAT-1, STAT-2, STAT-3 — character for character.

    Assumption **A3**, not a ruling: the specification's two end-of-game
    examples disagree with each other about where ``q quits`` starts, and the
    mock-up shows a leading blank column neither quoted string has. We
    reproduce all three verbatim and indent each by one column.
    """

    def test_during_play_it_is_the_specifications_string(self):
        # STAT-2, quoted in the spec as "score 0    arrows, q quits".
        self.assertEqual(
            theme.status_text(Outcome.PLAYING, 0), "score 0    arrows, q quits"
        )

    def test_on_a_loss_it_is_the_specifications_string(self):
        # STAT-3, quoted in the spec as "CAUGHT  score 37   q quits".
        self.assertEqual(
            theme.status_text(Outcome.CAUGHT, 37), "CAUGHT  score 37   q quits"
        )

    def test_on_a_win_it_is_the_specifications_string(self):
        # STAT-3, quoted in the spec as "CLEARED  score 274  q quits".
        self.assertEqual(
            theme.status_text(Outcome.CLEARED, 274), "CLEARED  score 274  q quits"
        )

    def test_the_score_is_the_only_thing_substituted(self):
        # SCORE-5: the score is shown, and kept up to date.
        self.assertEqual(
            theme.status_text(Outcome.PLAYING, 41), "score 41    arrows, q quits"
        )
        self.assertEqual(
            theme.status_text(Outcome.CAUGHT, 0), "CAUGHT  score 0   q quits"
        )
        self.assertEqual(
            theme.status_text(Outcome.CLEARED, 5), "CLEARED  score 5  q quits"
        )

    def test_each_outcome_names_itself_so_the_line_says_which_ending(self):
        self.assertTrue(theme.status_text(Outcome.CAUGHT, 1).startswith("CAUGHT"))
        self.assertTrue(theme.status_text(Outcome.CLEARED, 1).startswith("CLEARED"))
        self.assertFalse(theme.status_text(Outcome.PLAYING, 1).startswith("C"))

    def test_the_three_outcomes_are_the_only_three(self):
        self.assertEqual(set(theme.STATUS_TEMPLATES), set(Outcome))

    def test_an_unknown_outcome_is_refused_rather_than_drawn_blank(self):
        with self.assertRaises(ValueError):
            theme.status_text("HALTED", 0)

    def test_the_indent_is_one_column_as_the_mock_up_shows(self):
        self.assertEqual(theme.STATUS_INDENT, 1)


if __name__ == "__main__":
    unittest.main()
