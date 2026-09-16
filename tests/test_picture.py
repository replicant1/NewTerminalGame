# -*- coding: utf-8 -*-
"""WI-22 — the join, and only the join.

:func:`terminal_game.presentation.picture.frame_for` puts WI-12's rows 0–28
together with WI-13's row 29.  These tests own **that**, and nothing on
either side of it.

So there is no assertion here about which glyph a wall is drawn as, where a
dot goes, which of the two actors is painted second, or what row 29 says —
every one of those is already pinned by the tests of the module that owns
it, and repeating it through a bigger function would turn one defect into
several red files.  What is asserted is exactly the two things that are only
true because of this function: that the maze half is the composer's output
for this state, and that the bottom row is the status line built from *this*
state's score and outcome.

**No status-line literal appears in this file** (A7).  The expected row 29
is composed from WI-13's own function, so that if the user ever rules on
contradictions C-3 or C-4 these tests follow the ruling instead of
contradicting it.
"""

from __future__ import annotations

import unittest

from terminal_game.domain.dot_field import DotField
from terminal_game.domain.game_state import GameState, Outcome, Score
from terminal_game.domain.maze import Maze, Square
from terminal_game.presentation.frame import (
    BLANK,
    FRAME_COLUMNS,
    MAZE_ROWS,
    STATUS_ROW,
    Cell,
    Colour,
)
from terminal_game.presentation.frame_composer import compose_frame
from terminal_game.presentation.picture import frame_for
from terminal_game.presentation.status_line import status_row

#: A stand-in for row 29, handed to the composer when this file needs a
#: picture of the maze half alone.  Deliberately not a status line: what
#: goes on row 29 is WI-13's, and a literal here would be the very thing A7
#: forbids.
NOT_A_STATUS_ROW = tuple(
    [Cell(character, Colour.STATUS_CYAN) for character in "STAND-IN"]
    + [BLANK] * (FRAME_COLUMNS - 8)
)

#: A corridor running east–west between two walls: small enough to read,
#: wide enough to hold two actors whose three-column motifs do not touch.
SMALL = Maze.from_text(
    """
#######
#.....#
#######
"""
)


def a_state(score=0, outcome=Outcome.UNDECIDED, eaten=()):
    """A game state over :data:`SMALL`, with a score and an outcome of your
    choosing, so that a test can watch the bottom row follow the state."""
    player = Square(1, 1)
    dots = DotField.over_corridors_except(SMALL, player)
    for square in eaten:
        dots = dots.without_dot_at(square)
    return GameState(
        maze=SMALL,
        dots=dots,
        player=player,
        ghost=Square(5, 1),
        score=Score(score),
        outcome=outcome,
    )


class TheMazeHalfIsTheComposers(unittest.TestCase):
    """Rows 0–28 are WI-12's work, untouched on the way through."""

    def test_the_maze_rows_are_exactly_what_the_composer_produced(self):
        state = a_state()

        joined = frame_for(state)
        composed = compose_frame(state, NOT_A_STATUS_ROW)

        self.assertEqual(
            composed.rows[:MAZE_ROWS],
            joined.rows[:MAZE_ROWS],
            "rows 0-28 must be the composer's, cell for cell and colour for "
            "colour: this function places the status row and writes nothing "
            "above it",
        )

    def test_the_maze_rows_follow_the_state_they_were_asked_about(self):
        """Two different positions give two different pictures.

        Not an assertion about *where* the actors are drawn — that is WI-12's
        — but that this function passes the state it was handed down to the
        composer rather than composing some other one.
        """
        here = a_state()
        elsewhere = GameState(
            maze=SMALL,
            dots=DotField.over_corridors_except(SMALL, Square(3, 1)),
            player=Square(3, 1),
            ghost=Square(5, 1),
            score=Score(),
            outcome=Outcome.UNDECIDED,
        )

        self.assertEqual(
            compose_frame(here, NOT_A_STATUS_ROW).rows[:MAZE_ROWS],
            frame_for(here).rows[:MAZE_ROWS],
        )
        self.assertEqual(
            compose_frame(elsewhere, NOT_A_STATUS_ROW).rows[:MAZE_ROWS],
            frame_for(elsewhere).rows[:MAZE_ROWS],
        )


class TheBottomRowIsTheStatusLines(unittest.TestCase):
    """Row 29 is WI-13's row for this state, and is asked for as such."""

    def test_the_bottom_row_is_the_status_row_for_this_state(self):
        for score, outcome in (
            (0, Outcome.UNDECIDED),
            (37, Outcome.CAUGHT),
            (259, Outcome.CLEARED),
        ):
            with self.subTest(score=score, outcome=outcome):
                state = a_state(score=score, outcome=outcome)

                self.assertEqual(
                    status_row(state.score.points, state.outcome),
                    frame_for(state).rows[STATUS_ROW],
                    "the bottom row must be WI-13's row built from this "
                    "state's own score and outcome",
                )

    def test_the_score_on_the_bottom_row_is_the_state_s_score(self):
        """A different score gives a different bottom row.

        The join is what reads ``state.score.points``; without this, a
        function that always asked for a zero score would satisfy the test
        above for its first case alone.
        """
        self.assertNotEqual(
            frame_for(a_state(score=0)).rows[STATUS_ROW],
            frame_for(a_state(score=41)).rows[STATUS_ROW],
        )

    def test_the_ending_on_the_bottom_row_is_the_state_s_outcome(self):
        """A different outcome gives a different bottom row, for one score."""
        rows = {
            outcome: frame_for(a_state(score=37, outcome=outcome)).rows[
                STATUS_ROW
            ]
            for outcome in Outcome
        }

        self.assertEqual(
            len(Outcome),
            len(set(rows.values())),
            "each of the three outcomes must reach row 29 as its own row",
        )


class TheSeamIsOneFunction(unittest.TestCase):
    """What the callers get, and what they no longer have to know."""

    def test_a_state_in_and_a_whole_frame_out(self):
        """The signature is the seam amendment 10 specified: one argument."""
        frame = frame_for(a_state())

        self.assertEqual(MAZE_ROWS + 1, len(frame.rows))
        for index, row in enumerate(frame.rows):
            self.assertEqual(
                FRAME_COLUMNS, len(row), "row {0}".format(index)
            )

    def test_composing_a_picture_does_not_disturb_the_game(self):
        """Asking for a picture twice gives the same picture.

        A join that mutated the state on the way past — eating a dot,
        advancing a score — would show up here as two frames that differ.
        """
        state = a_state()

        self.assertEqual(frame_for(state), frame_for(state))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
