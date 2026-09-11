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


def xterm_rgb_levels(index):
    """The 256-colour index ``index`` as ``(red, green, blue)`` on 0..5.

    The xterm-256 palette is three ranges: 0..15 are the system colours,
    16..231 are a 6 x 6 x 6 cube ordered red-major, and 232..255 are a grey
    ramp. The cube is the only part this project uses, and it is the only
    part that can be decoded into hue — a grey has no hue and a system colour
    is whatever the terminal's own scheme says it is. Both are rejected here
    rather than guessed at, because a colour the game cannot name is a colour
    human check H6 cannot be asked about.

    Written out here rather than imported from anywhere: this is the table
    that turns the *number* the code asks for back into the *word* the
    specification uses, which is the whole point of the class below.
    """
    if not 16 <= index <= 231:
        raise ValueError(
            "%r is not in the 6x6x6 colour cube, so it has no hue to check"
            % (index,)
        )
    offset = index - 16
    return (offset // 36, (offset // 6) % 6, offset % 6)


class TestTheColoursTheSpecificationNames(unittest.TestCase):
    """SCRN-3, SCRN-4, SCRN-5, SCRN-6 — **the colours themselves**.

    Until WI-13 no test in this project asserted a colour at all. The suite
    asserted that the six styles' colours were distinct from one another,
    that each was an ``int`` in ``0..255``, and that the player's differed
    from the ghost's — all of which a table of six arbitrary numbers would
    satisfy. The numbers `33`, `178` and `51` appeared nowhere in ``tests/``,
    so **SCRN-6, "the status line is written in cyan", had nothing behind it
    but the word "cyan" in a test title**.

    Two assertions per style, and they fail for different reasons:

    1. **the exact index the code asks for**, so that a change to the table
       is a change somebody has to make here on purpose; and
    2. **the hue that index actually is**, decoded from the xterm colour cube
       by :func:`xterm_rgb_levels`, so that the number is tied to the word
       the specification uses. Swapping cyan for blue keeps the first kind of
       assertion honest only if somebody remembers to update it; the second
       kind says *"that is not cyan"* whatever the number.

    What a test cannot do is say whether it **looks** cyan on a real screen
    in a real Terminal profile. That stays with the user, under human check
    H6. This class is the half a machine can check, and it does not pretend
    to be the other half.
    """

    #: What the code asks curses for, style by style.
    EXPECTED = (
        (theme.STYLE_WALL, 33, "blue (SCRN-3)"),
        (theme.STYLE_DOT, 178, "gold (SCRN-4)"),
        (theme.STYLE_PLAYER, 226, "bright yellow (SCRN-5)"),
        (theme.STYLE_GHOST, 213, "pink (SCRN-5)"),
        (theme.STYLE_STATUS, 51, "cyan (SCRN-6)"),
    )

    def colour_of(self, style):
        return theme.STYLES[style].colour

    def levels(self, style):
        return xterm_rgb_levels(self.colour_of(style))

    def test_each_style_asks_for_the_colour_index_it_is_documented_to_ask_for(self):
        for style, index, description in self.EXPECTED:
            self.assertEqual(
                index,
                self.colour_of(style),
                "the %s style no longer asks for colour %d, %s"
                % (style, index, description),
            )

    def test_the_status_line_is_cyan(self):
        """SCRN-6, which nothing in the project asserted before WI-13.

        Cyan is green and blue together with no red: on the cube that is
        ``(0, 5, 5)``. Blue alone, or white, or the gold of the dots, each
        fails a different one of these three.
        """
        red, green, blue = self.levels(theme.STYLE_STATUS)
        self.assertEqual(0, red, "the status line has red in it, so it is not cyan")
        self.assertEqual(5, green, "the status line is not full green, so not cyan")
        self.assertEqual(5, blue, "the status line is not full blue, so not cyan")

    def test_the_walls_are_blue(self):
        """SCRN-3 "blue double lines"."""
        red, green, blue = self.levels(theme.STYLE_WALL)
        self.assertEqual(0, red, "the walls have red in them, so they are not blue")
        self.assertGreater(
            blue, green, "the walls are not more blue than green, so not blue"
        )
        self.assertGreater(blue, red)

    def test_the_dots_are_gold(self):
        """SCRN-4 "dim gold" — warm, and with no blue in it at all."""
        red, green, blue = self.levels(theme.STYLE_DOT)
        self.assertEqual(0, blue, "the dots have blue in them, so they are not gold")
        self.assertGreater(red, 0)
        self.assertGreater(green, 0)
        self.assertGreater(
            red, green, "the dots are not warmer than they are green, so not gold"
        )

    def test_the_player_is_bright_yellow(self):
        """SCRN-5 "bright yellow" — red and green at full, no blue."""
        red, green, blue = self.levels(theme.STYLE_PLAYER)
        self.assertEqual(5, red)
        self.assertEqual(5, green)
        self.assertEqual(
            0, blue, "the player has blue in it, so it is not bright yellow"
        )

    def test_the_ghost_is_pink(self):
        """SCRN-5 "pink" — red and blue at full, and lighter than pure magenta."""
        red, green, blue = self.levels(theme.STYLE_GHOST)
        self.assertEqual(5, red)
        self.assertEqual(5, blue)
        self.assertGreater(
            green, 0, "the ghost has no green at all, so it is magenta and not pink"
        )
        self.assertLess(green, red, "the ghost is washing out towards white")

    def test_the_player_and_the_ghost_are_different_hues_and_not_merely_different(self):
        """SCRN-5's "told apart by colour" is about hue, not about inequality.

        Two adjacent indices differ without being tellable apart at a glance.
        These two differ in the blue channel by the whole width of the cube.
        """
        player = self.levels(theme.STYLE_PLAYER)
        ghost = self.levels(theme.STYLE_GHOST)
        self.assertEqual(5, abs(player[2] - ghost[2]))

    def test_the_decoder_rejects_an_index_that_carries_no_hue(self):
        """The guard on the guard: the helper is not silently forgiving.

        A grey or a system colour would sail through a decoder that merely
        did the arithmetic, and every hue assertion above would then be
        measuring nonsense.
        """
        for index in (0, 7, 15, 232, 255, 256, -1):
            with self.assertRaises(ValueError):
                xterm_rgb_levels(index)

    def test_the_default_style_is_the_one_style_with_no_hue_to_check(self):
        """It is the terminal's own foreground, deliberately, and is excluded.

        Named here so that its absence from :data:`EXPECTED` reads as a
        decision rather than an oversight.
        """
        self.assertNotIn(
            theme.STYLE_DEFAULT, [style for style, _index, _why in self.EXPECTED]
        )
        with self.assertRaises(ValueError):
            xterm_rgb_levels(theme.STYLES[theme.STYLE_DEFAULT].colour)


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
