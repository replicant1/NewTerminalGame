# -*- coding: utf-8 -*-
"""The whole picture — SCRN-1..6, MAZE-1's margin, END-4, STAT-1..3.

The strongest test in this file, and in the project, is
:class:`TestTheGoldenFixture`: the specification's own picture, decoded into
a maze, rendered back, and compared **character for character** against the
30 rows the specification draws. It pins the renderer to the document rather
than to anybody's opinion of what the document meant.
"""

import ast
import io
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from termgame import maze as mazelib  # noqa: E402
from termgame import theme  # noqa: E402
from termgame import view  # noqa: E402
from termgame.model import (  # noqa: E402
    MAZE_COLS,
    MAZE_ROWS,
    RIGHT,
    SCREEN_COLS,
    SCREEN_ROWS,
    STYLE_DEFAULT,
    GameState,
    Outcome,
    Position,
)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

SEEDS = 60

#: In the mock-up an even picture column holds one of these when the maze
#: cell under it is corridor.
SPEC_CORRIDOR_CHARS = frozenset(u"▪█")

#: Where the specification's mock-up puts the player and the ghost.
SPEC_PLAYER = Position(13, 10)
SPEC_GHOST = Position(27, 1)


def read_lines(name):
    """One of the fixtures, as a list of lines with the trailing blank gone."""
    path = os.path.join(FIXTURES, name)
    with io.open(path, encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def spec_maze():
    """The specification's mock-up, decoded back into a maze."""
    lines = read_lines("spec_maze.txt")
    grid = "\n".join(
        "".join(
            "." if lines[r][2 * c] in SPEC_CORRIDOR_CHARS else "#"
            for c in range(MAZE_COLS)
        )
        for r in range(MAZE_ROWS)
    )
    return mazelib.from_text(grid)


def state_on(maze, player, ghost, dots=None, score=0, outcome=Outcome.PLAYING):
    """A game state on ``maze`` — every corridor holds a dot unless told."""
    if dots is None:
        dots = frozenset(maze.corridors() - {Position(*player)})
    return GameState(
        maze=maze,
        player=Position(*player),
        ghost=Position(*ghost),
        ghost_dir=RIGHT,
        dots=frozenset(dots),
        score=score,
        outcome=outcome,
    )


def a_generated_state(seed):
    """A state on a generated maze, with two well-separated entities."""
    maze = mazelib.generate(random.Random(seed))
    corridors = sorted(maze.corridors())
    player = corridors[len(corridors) // 2]
    ghost = corridors[0]
    return state_on(maze, player, ghost)


def entity_columns(state):
    """The picture cells the player and the ghost cover, spill included.

    A three-character entity sits on a two-column pitch, so it always covers
    the joiner column either side of its own. Any check on what the *maze*
    layer put somewhere has to step around these.
    """
    covered = set()
    for cell in (state.player, state.ghost):
        row = view.picture_row(cell[0])
        centre = view.picture_col(cell[1])
        for offset in (-1, 0, 1):
            covered.add((row, centre + offset))
    return covered


# --------------------------------------------------------------------------


class TestTheGoldenFixture(unittest.TestCase):
    """The specification's own picture, rendered back exactly.

    SCRN-1 through SCRN-6 at once, against the document itself.
    """

    @classmethod
    def setUpClass(cls):
        cls.expected = read_lines("spec_picture.txt")
        cls.maze = spec_maze()
        cls.state = state_on(cls.maze, SPEC_PLAYER, SPEC_GHOST)
        cls.actual = view.render_rows(cls.state)

    def test_the_fixture_is_thirty_rows_of_forty_columns(self):
        # The fixture carries trailing spaces on every row -- the blank
        # right-hand margin is part of the picture, and an editor that
        # stripped them would quietly weaken every assertion below.
        self.assertEqual(len(self.expected), SCREEN_ROWS)
        for index, row in enumerate(self.expected):
            self.assertEqual(len(row), SCREEN_COLS, "fixture row %d" % index)

    def test_the_rendered_picture_is_exactly_the_specifications_picture(self):
        self.assertEqual(len(self.actual), len(self.expected))
        for index, (got, want) in enumerate(zip(self.actual, self.expected)):
            self.assertEqual(got, want, "picture row %d" % index)
        self.assertEqual(list(self.actual), list(self.expected))

    def test_the_first_twenty_nine_rows_are_the_mock_up_verbatim(self):
        # SCRN-1: the top 29 rows show the maze.
        mock_up = read_lines("spec_maze.txt")
        self.assertEqual(len(mock_up), MAZE_ROWS)
        for index, line in enumerate(mock_up):
            self.assertEqual(self.actual[index][: len(line)], line, "row %d" % index)

    def test_the_bottom_row_is_the_status_line(self):
        # SCRN-1 again: the bottom row is the status line, and nothing else.
        self.assertEqual(
            self.actual[view.STATUS_ROW].rstrip(), " score 0    arrows, q quits"
        )

    def test_the_two_fixtures_do_not_drift_apart(self):
        # spec_picture.txt is spec_maze.txt plus the margin and the status
        # row. If somebody edits one, this says so rather than letting the
        # golden test be quietly rewritten to match a bug.
        mock_up = read_lines("spec_maze.txt")
        for index, line in enumerate(mock_up):
            self.assertEqual(self.expected[index], line + "   ", "row %d" % index)


class TestTheGeometry(unittest.TestCase):
    """SCRN-1 and MAZE-1's narrow blank margin."""

    def setUp(self):
        self.state = a_generated_state(7)
        self.frame = view.render(self.state)

    def test_the_picture_is_thirty_rows_by_forty_columns(self):
        # WIN-2 as the renderer sees it.
        self.assertEqual(self.frame.height, SCREEN_ROWS)
        self.assertEqual(self.frame.width, SCREEN_COLS)

    def test_maze_column_c_is_drawn_at_picture_column_two_c(self):
        self.assertEqual(view.picture_col(0), 0)
        self.assertEqual(view.picture_col(18), 36)
        self.assertEqual(view.picture_row(0), 0)
        self.assertEqual(view.picture_row(28), 28)

    def test_columns_thirty_seven_to_thirty_nine_are_always_blank(self):
        # MAZE-1: "a narrow blank margin down the right-hand edge".
        self.assertEqual(view.MARGIN_FIRST_COL, 37)
        self.assertEqual(view.margin_columns(self.state.maze), (37, 38, 39))
        for seed in range(SEEDS):
            frame = view.render(a_generated_state(seed))
            for row in range(SCREEN_ROWS):
                for col in (37, 38, 39):
                    self.assertEqual(
                        frame.char_at(row, col),
                        " ",
                        "seed %d, (%d, %d)" % (seed, row, col),
                    )
                    self.assertEqual(frame.style_at(row, col), STYLE_DEFAULT)

    def test_the_bottom_right_cell_is_never_written_to(self):
        # Architecture C1: addstr at (LINES-1, COLS-1) raises. WI-3 never
        # puts anything there, which is half of what makes C1 survivable.
        for seed in range(SEEDS):
            frame = view.render(a_generated_state(seed))
            self.assertEqual(frame.char_at(SCREEN_ROWS - 1, SCREEN_COLS - 1), " ")

    def test_the_status_row_is_the_last_row(self):
        self.assertEqual(view.STATUS_ROW, SCREEN_ROWS - 1)
        self.assertEqual(view.STATUS_ROW, 29)


class TestTheJoinerColumnInvariant(unittest.TestCase):
    """Architecture C9 — the whole entity scheme rests on this.

    A three-character entity spills into the joiner columns either side of
    its cell. That is only safe because a joiner beside a corridor cell is
    blank. Asserted over many seeds rather than reasoned about.
    """

    def test_the_columns_either_side_of_every_corridor_cell_are_blank(self):
        for seed in range(SEEDS):
            state = a_generated_state(seed)
            frame = view.render(state)
            covered = entity_columns(state)
            checked = 0
            for cell in sorted(state.maze.corridors()):
                row = view.picture_row(cell[0])
                centre = view.picture_col(cell[1])
                for col in (centre - 1, centre + 1):
                    if (row, col) in covered:
                        continue
                    checked += 1
                    self.assertEqual(
                        frame.char_at(row, col),
                        " ",
                        "seed %d: picture (%d, %d) beside corridor %r"
                        % (seed, row, col, cell),
                    )
            # Guard against the skip list swallowing the whole check.
            self.assertGreater(checked, 400, "seed %d checked almost nothing" % seed)

    def test_a_joiner_carries_a_bar_exactly_when_both_sides_are_wall(self):
        for seed in range(SEEDS):
            state = a_generated_state(seed)
            maze = state.maze
            frame = view.render(state)
            covered = entity_columns(state)
            for r in range(MAZE_ROWS):
                for c in range(MAZE_COLS - 1):
                    col = view.picture_col(c) + 1
                    if (r, col) in covered:
                        continue
                    both_wall = maze.is_wall((r, c)) and maze.is_wall((r, c + 1))
                    self.assertEqual(
                        frame.char_at(r, col),
                        u"═" if both_wall else u" ",
                        "seed %d: joiner at (%d, %d)" % (seed, r, col),
                    )


class TestTheEntitiesStayOnTheScreen(unittest.TestCase):
    """SCRN-5 — three characters wide, and never off either edge."""

    def test_the_player_and_ghost_never_spill_past_either_edge(self):
        # They only ever stand on corridor cells, and MAZE-3 makes column 0
        # and column 18 wall, so the spill is always in range. Asserted
        # rather than reasoned about: over many seeds, every corridor cell
        # in turn holds the player.
        for seed in range(SEEDS):
            maze = mazelib.generate(random.Random(seed))
            for cell in sorted(maze.corridors()):
                centre = view.picture_col(cell[1])
                self.assertGreaterEqual(
                    centre - 1, 0, "seed %d: %r spills off the left" % (seed, cell)
                )
                self.assertLess(
                    centre + 1,
                    SCREEN_COLS,
                    "seed %d: %r spills off the right" % (seed, cell),
                )
                self.assertTrue(1 <= cell[1] <= MAZE_COLS - 2)

    def test_every_corridor_cell_can_actually_hold_the_player(self):
        # The check above is arithmetic; this one renders. A frame builder
        # that went out of range would raise IndexError rather than fail an
        # assertion, so this would still catch it.
        maze = mazelib.generate(random.Random(3))
        corridors = sorted(maze.corridors())
        for cell in corridors:
            # Park the ghost far enough away that it cannot overwrite the
            # player -- see TestTwoEntitiesSideBySide for why that matters.
            ghost = corridors[-1] if cell[0] < 14 else corridors[0]
            frame = view.render(state_on(maze, cell, ghost))
            row = view.picture_row(cell[0])
            centre = view.picture_col(cell[1])
            self.assertEqual(
                (
                    frame.char_at(row, centre - 1),
                    frame.char_at(row, centre),
                    frame.char_at(row, centre + 1),
                ),
                theme.PLAYER_GLYPHS,
                "player at %r" % (cell,),
            )

    def test_the_player_is_three_characters_and_the_ghost_a_different_three(self):
        maze = spec_maze()
        frame = view.render(state_on(maze, SPEC_PLAYER, SPEC_GHOST))
        row = view.picture_row(SPEC_PLAYER[0])
        centre = view.picture_col(SPEC_PLAYER[1])
        self.assertEqual(
            "".join(frame.char_at(row, centre + d) for d in (-1, 0, 1)), u"▐█▌"
        )
        row = view.picture_row(SPEC_GHOST[0])
        centre = view.picture_col(SPEC_GHOST[1])
        self.assertEqual(
            "".join(frame.char_at(row, centre + d) for d in (-1, 0, 1)), u"▗█▖"
        )


class TestTheDrawOrder(unittest.TestCase):
    """END-4 — on a loss the ghost is drawn over the player."""

    def setUp(self):
        self.maze = spec_maze()

    def test_the_ghost_is_drawn_over_the_player_on_the_same_cell(self):
        cell = SPEC_PLAYER
        state = state_on(
            self.maze, cell, cell, score=12, outcome=Outcome.CAUGHT
        )
        frame = view.render(state)
        row = view.picture_row(cell[0])
        centre = view.picture_col(cell[1])
        got = tuple(frame.char_at(row, centre + d) for d in (-1, 0, 1))
        self.assertEqual(got, theme.GHOST_GLYPHS)
        self.assertNotEqual(got, theme.PLAYER_GLYPHS)
        for d in (-1, 0, 1):
            self.assertEqual(frame.style_at(row, centre + d), theme.STYLE_GHOST)

    def test_the_entities_are_drawn_over_the_dot_on_their_cell(self):
        # SCORE-4: a dot under the ghost is still there to be taken -- it is
        # simply not visible. The dot stays in the state.
        cell = SPEC_GHOST
        state = state_on(self.maze, SPEC_PLAYER, cell)
        self.assertIn(cell, state.dots)
        frame = view.render(state)
        self.assertEqual(
            frame.char_at(view.picture_row(cell[0]), view.picture_col(cell[1])),
            theme.GHOST_GLYPHS[1],
        )

    def test_the_entities_are_drawn_over_the_wall_layer_not_under_it(self):
        # A regression guard on the ordering itself: if the wall layer were
        # painted last, an entity beside a wall would lose the spill column
        # on that side.
        maze = mazelib.from_text("\n".join(["#######", "#.....#", "#######"]))
        state = state_on(maze, Position(1, 5), Position(1, 1))
        frame = view.render(state)
        # The ghost is at maze column 1, hard against the wall at column 0.
        self.assertEqual(frame.char_at(1, 1), theme.GHOST_GLYPHS[0])
        self.assertEqual(frame.char_at(1, 2), theme.GHOST_GLYPHS[1])
        self.assertEqual(frame.char_at(1, 3), theme.GHOST_GLYPHS[2])
        self.assertEqual(frame.char_at(1, 0), u"║")
        # And the player is still its own three characters.
        self.assertEqual(frame.char_at(1, 9), theme.PLAYER_GLYPHS[0])
        self.assertEqual(frame.char_at(1, 11), theme.PLAYER_GLYPHS[2])


class TestTwoEntitiesSideBySide(unittest.TestCase):
    """A consequence of SCRN-5 the specification does not address.

    Each entity is **three** characters wide on a **two**-column pitch, so
    two entities on horizontally adjacent corridor cells necessarily share
    one picture column. The later layer wins, and the ghost is the later
    layer (END-4), so the player loses its right-hand edge for that frame.

    This is not reachable in the mock-up — the specification draws the two
    far apart — and it is not avoidable while the glyphs stay three wide. It
    is recorded here so that it is a known, asserted behaviour rather than a
    surprise, and so that changing it is a deliberate act.
    """

    def setUp(self):
        self.maze = mazelib.from_text("\n".join(["#######", "#.....#", "#######"]))

    def test_the_ghost_wins_the_shared_column_when_it_is_to_the_right(self):
        state = state_on(self.maze, Position(1, 2), Position(1, 3))
        frame = view.render(state)
        # Player centre is column 4, ghost centre column 6; column 5 is
        # claimed by both and the ghost has it.
        self.assertEqual(frame.char_at(1, 3), theme.PLAYER_GLYPHS[0])
        self.assertEqual(frame.char_at(1, 4), theme.PLAYER_GLYPHS[1])
        self.assertEqual(frame.char_at(1, 5), theme.GHOST_GLYPHS[0])
        self.assertEqual(frame.style_at(1, 5), theme.STYLE_GHOST)
        self.assertEqual(frame.char_at(1, 6), theme.GHOST_GLYPHS[1])
        self.assertEqual(frame.char_at(1, 7), theme.GHOST_GLYPHS[2])

    def test_the_ghost_wins_the_shared_column_when_it_is_to_the_left(self):
        state = state_on(self.maze, Position(1, 3), Position(1, 2))
        frame = view.render(state)
        # Ghost centre is column 4, player centre column 6; column 5 is
        # claimed by both and the ghost still has it.
        self.assertEqual(frame.char_at(1, 5), theme.GHOST_GLYPHS[2])
        self.assertEqual(frame.style_at(1, 5), theme.STYLE_GHOST)
        self.assertEqual(frame.char_at(1, 6), theme.PLAYER_GLYPHS[1])
        self.assertEqual(frame.char_at(1, 7), theme.PLAYER_GLYPHS[2])

    def test_vertically_adjacent_entities_do_not_share_anything(self):
        # The pitch is only tight horizontally; rows are one apart.
        maze = mazelib.from_text("\n".join(["###", "#.#", "#.#", "###"]))
        frame = view.render(state_on(maze, Position(1, 1), Position(2, 1)))
        self.assertEqual(
            tuple(frame.char_at(1, c) for c in (1, 2, 3)), theme.PLAYER_GLYPHS
        )
        self.assertEqual(
            tuple(frame.char_at(2, c) for c in (1, 2, 3)), theme.GHOST_GLYPHS
        )

    def test_both_are_still_visible_and_still_told_apart(self):
        # SCRN-5's actual requirement survives the overlap: the two are
        # still distinguishable by colour and by outline.
        state = state_on(self.maze, Position(1, 2), Position(1, 3))
        frame = view.render(state)
        styles = [frame.style_at(1, c) for c in range(1, 9)]
        self.assertIn(theme.STYLE_PLAYER, styles)
        self.assertIn(theme.STYLE_GHOST, styles)


class TestTheLayersAndTheirStyles(unittest.TestCase):
    """SCRN-3, SCRN-4, SCRN-5, SCRN-6 — every layer carries its own style."""

    def setUp(self):
        self.maze = spec_maze()
        self.state = state_on(self.maze, SPEC_PLAYER, SPEC_GHOST, score=3)
        self.frame = view.render(self.state)

    def test_every_wall_character_carries_the_wall_style(self):
        for r in range(MAZE_ROWS):
            for c in range(MAZE_COLS):
                if not self.maze.is_wall((r, c)):
                    continue
                self.assertEqual(
                    self.frame.style_at(view.picture_row(r), view.picture_col(c)),
                    theme.STYLE_WALL,
                    "wall at (%d, %d)" % (r, c),
                )

    def test_every_wall_and_joiner_glyph_comes_from_the_wall_alphabet(self):
        for r in range(MAZE_ROWS):
            for c in range(SCREEN_COLS):
                if self.frame.style_at(r, c) != theme.STYLE_WALL:
                    continue
                self.assertIn(self.frame.char_at(r, c), theme.WALL_ALPHABET)

    def test_every_dot_is_drawn_once_in_the_dot_style(self):
        # SCRN-4: one to a corridor square.
        drawn = set()
        for r in range(MAZE_ROWS):
            for c in range(SCREEN_COLS):
                if self.frame.style_at(r, c) == theme.STYLE_DOT:
                    self.assertEqual(self.frame.char_at(r, c), theme.DOT_GLYPH)
                    self.assertEqual(c % 2, 0, "a dot landed in a joiner column")
                    drawn.add(Position(r, c // 2))
        # Every dot except the ones the entities are standing on.
        hidden = {self.state.player, self.state.ghost}
        self.assertEqual(drawn, set(self.state.dots) - hidden)

    def test_an_eaten_dot_is_gone_from_the_picture(self):
        # SCORE-1: the dot disappears from the maze for the rest of the game.
        eaten = Position(1, 1)
        self.assertIn(eaten, self.state.dots)
        after = state_on(
            self.maze,
            SPEC_PLAYER,
            SPEC_GHOST,
            dots=self.state.dots - {eaten},
            score=1,
        )
        frame = view.render(after)
        self.assertEqual(
            frame.char_at(view.picture_row(1), view.picture_col(1)), " "
        )
        self.assertEqual(
            frame.style_at(view.picture_row(1), view.picture_col(1)), STYLE_DEFAULT
        )

    def test_the_status_line_is_cyan_and_the_only_thing_on_its_row(self):
        # SCRN-6 and STAT-1.
        text = " score 3    arrows, q quits"
        row = view.STATUS_ROW
        self.assertEqual(self.frame.rows()[row].rstrip(), text)
        for col in range(SCREEN_COLS):
            char = self.frame.char_at(row, col)
            style = self.frame.style_at(row, col)
            if col == 0 or col >= len(text):
                self.assertEqual(char, " ", "column %d" % col)
                self.assertEqual(style, STYLE_DEFAULT, "column %d" % col)
            else:
                self.assertEqual(style, theme.STYLE_STATUS, "column %d" % col)

    def test_no_maze_row_carries_the_status_style(self):
        for r in range(MAZE_ROWS):
            for c in range(SCREEN_COLS):
                self.assertNotEqual(self.frame.style_at(r, c), theme.STYLE_STATUS)


class TestTheStatusLineInThePicture(unittest.TestCase):
    """STAT-1, STAT-2, STAT-3 — all three, character for character.

    Assumption **A3**, not a ruling: the specification's two end-of-game
    examples put ``q quits`` at different offsets and the mock-up shows a
    leading blank column neither quoted string has. We reproduce the three
    strings verbatim and indent each by one column. If the user answers A3
    otherwise, this class and ``theme.STATUS_INDENT`` are the whole change.
    """

    def setUp(self):
        self.maze = spec_maze()

    def _status_row(self, outcome, score):
        state = state_on(
            self.maze, SPEC_PLAYER, SPEC_GHOST, score=score, outcome=outcome
        )
        return view.render(state).rows()[view.STATUS_ROW]

    def test_during_play(self):
        self.assertEqual(
            self._status_row(Outcome.PLAYING, 0),
            " score 0    arrows, q quits".ljust(SCREEN_COLS),
        )

    def test_on_a_loss(self):
        self.assertEqual(
            self._status_row(Outcome.CAUGHT, 37),
            " CAUGHT  score 37   q quits".ljust(SCREEN_COLS),
        )

    def test_on_a_win(self):
        self.assertEqual(
            self._status_row(Outcome.CLEARED, 274),
            " CLEARED  score 274  q quits".ljust(SCREEN_COLS),
        )

    def test_the_score_shown_is_the_score_in_the_state(self):
        # SCORE-5: the score is shown in the status line.
        for score in (0, 1, 9, 10, 99, 100, 263):
            self.assertIn(
                "score %d" % score, self._status_row(Outcome.PLAYING, score)
            )

    def test_the_longest_reachable_line_still_fits_on_the_row(self):
        # 264 corridors in the spec's maze, one of which is the player's
        # empty start square, so 263 is the most that can ever be scored.
        row = self._status_row(Outcome.CLEARED, 263)
        self.assertEqual(len(row), SCREEN_COLS)
        self.assertEqual(len(row.rstrip()), 28)
        self.assertEqual(row[SCREEN_COLS - 1], " ")

    def test_every_outcome_produces_a_status_row(self):
        for outcome in Outcome:
            self.assertTrue(self._status_row(outcome, 5).strip())


class TestNothingCursesShapedCrossesTheSeam(unittest.TestCase):
    """SCRN-2, in the sense that matters — plan §2.4, architecture C6."""

    def test_every_cell_is_one_character_and_a_plain_string_style(self):
        for seed in range(SEEDS):
            frame = view.render(a_generated_state(seed))
            for r in range(frame.height):
                for c in range(frame.width):
                    cell = frame.cell(r, c)
                    self.assertIsInstance(cell.char, str)
                    self.assertEqual(len(cell.char), 1)
                    self.assertIsInstance(cell.style, str)
                    self.assertNotIsInstance(cell.style, int)

    def test_every_style_used_is_one_the_theme_declares(self):
        seen = set()
        for seed in range(SEEDS):
            frame = view.render(a_generated_state(seed))
            for row in frame.styles():
                seen.update(row)
        self.assertTrue(seen <= set(theme.STYLE_NAMES), "unknown styles: %r" % seen)
        # And the picture really does use all of them, or the check above
        # would pass on an empty frame.
        self.assertEqual(seen, set(theme.STYLE_NAMES))

    def test_the_view_module_uses_no_curses_identifier_anywhere(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "termgame",
            "view.py",
        )
        with io.open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        forbidden = {"curses", "A_BOLD", "A_DIM", "COLOR_PAIR", "color_pair"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, forbidden, "line %d" % node.lineno)
            elif isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, forbidden, "line %d" % node.lineno)

    def test_rendering_the_same_state_twice_gives_the_same_picture(self):
        # A frame is a value. Two renders of one state must be equal, or
        # comparing frames as text proves nothing.
        state = a_generated_state(11)
        self.assertEqual(view.render(state), view.render(state))
        self.assertEqual(view.render(state).text(), view.render(state).text())

    def test_rendering_does_not_touch_the_state(self):
        state = a_generated_state(12)
        before = (state.player, state.ghost, state.dots, state.score, state.outcome)
        view.render(state)
        self.assertEqual(
            (state.player, state.ghost, state.dots, state.score, state.outcome),
            before,
        )


class TestASmallHandWrittenBoard(unittest.TestCase):
    """A picture small enough to read in the failure message."""

    def test_a_three_by_seven_board_renders_as_drawn(self):
        maze = mazelib.from_text("\n".join(["#######", "#.....#", "#######"]))
        state = state_on(
            maze,
            Position(1, 3),
            Position(1, 5),
            dots=frozenset([Position(1, 1)]),
            score=1,
        )
        frame = view.render(state)
        self.assertEqual(frame.rows()[0][:13], u"╔═══════════╗")
        # col 0 wall, 2 the dot, 4 an empty corridor, 6 the player's centre,
        # 8 an empty corridor, 10 the ghost's centre, 12 wall.
        self.assertEqual(frame.rows()[1][:13], u"║ ▪  ▐█▌ ▗█▖║")
        self.assertEqual(frame.rows()[2][:13], u"╚═══════════╝")
        self.assertEqual(frame.rows()[1][13:], " " * (SCREEN_COLS - 13))

    def test_a_lone_wall_square_is_a_block(self):
        # SCRN-3's second sentence: "a wall square with no wall next to it is
        # drawn as a single blue block".
        maze = mazelib.from_text("\n".join([".....", "..#..", "....."]))
        state = state_on(maze, Position(0, 1), Position(2, 3), dots=frozenset())
        frame = view.render(state)
        self.assertEqual(frame.char_at(1, 4), u"■")
        self.assertEqual(frame.style_at(1, 4), theme.STYLE_WALL)
        self.assertEqual(frame.char_at(1, 3), u" ")
        self.assertEqual(frame.char_at(1, 5), u" ")

    def test_an_entity_on_column_zero_would_run_off_the_picture(self):
        # It cannot happen in a real maze -- MAZE-3 makes column 0 wall and
        # an entity only ever stands on corridor -- but if it ever did, the
        # frame builder raises rather than silently clipping the glyph.
        maze = mazelib.from_text("\n".join([".....", ".....", "....."]))
        state = state_on(maze, Position(1, 0), Position(1, 3), dots=frozenset())
        with self.assertRaises(IndexError):
            view.render(state)


if __name__ == "__main__":
    unittest.main()
