# -*- coding: utf-8 -*-
"""WI-13 — the status line.

**The literals in this file are the only status-line literals in the
project.**  The implementation plan confines assumption A7 to WI-13, and the
prohibition is about the item rather than the person: no other work item and
no other developer's tests may contain one.  Two consequences for whoever is
writing WI-12 or WI-19 — build an expected row 29 by calling
``status_text`` or ``status_row``, never by typing the line out; and if the
user rules on contradiction C-3 or C-4, only this file and
``terminal_game/presentation/status_line.py`` change.

The three literals below are transcribed from STAT-2 and STAT-3 in
``docs/FUNCTIONAL_REQUIREMENTS.md``, character for character, spacing and
all.  They look inconsistent because **they are** — that is contradiction
C-4, and reproducing it is what A7 asks for.
"""

from __future__ import annotations

import unittest

from terminal_game.domain.game_state import Outcome
from terminal_game.presentation.frame import (
    FRAME_COLUMNS,
    STATUS_ROW,
    Cell,
    Colour,
    FrameBuilder,
)
from terminal_game.presentation.status_line import (
    STATUS_COLOUR,
    status_row,
    status_text,
)


#: STAT-2, verbatim: what the line reads during play, at the opening score.
STAT_2_LITERAL = "score 0    arrows, q quits"

#: STAT-3's first example, verbatim: what the line reads on a loss.
STAT_3_LOSS_LITERAL = "CAUGHT  score 37   q quits"

#: STAT-3's second example, verbatim: what the line reads on a win.
#:
#: 274 is **not a score a game can reach** — a whole game is worth 259 to 271
#: points (``docs/findings/WI-6-start-squares.md``, over 200 mazes).  The
#: literal is still reproduced exactly, because A7 makes the specification's
#: literal normative; it is simply illustrative of a number rather than one.
STAT_3_WIN_LITERAL = "CLEARED  score 274  q quits"


class TheThreeLiterals(unittest.TestCase):
    """Each line reproduces its own example from the specification exactly."""

    def test_playing_at_score_zero_is_the_stat_2_literal(self):
        self.assertEqual(
            STAT_2_LITERAL, status_text(0, Outcome.UNDECIDED)
        )

    def test_a_loss_at_score_thirty_seven_is_the_stat_3_loss_literal(self):
        self.assertEqual(
            STAT_3_LOSS_LITERAL, status_text(37, Outcome.CAUGHT)
        )

    def test_a_win_at_score_two_hundred_and_seventy_four_is_the_stat_3_win_literal(self):
        self.assertEqual(
            STAT_3_WIN_LITERAL, status_text(274, Outcome.CLEARED)
        )

    def test_the_two_ending_literals_do_not_share_an_alignment(self):
        """Contradiction C-4, pinned so that "fixing" it cannot pass quietly.

        ``q quits`` sits at column 19 on the loss line and column 20 on the
        win line.  No single padding rule produces both, which is why these
        are per-ending templates.  A later change that made the two agree
        would be a change to the specification's own examples, and this says
        so out loud.
        """
        self.assertEqual(19, STAT_3_LOSS_LITERAL.index("q quits"))
        self.assertEqual(20, STAT_3_WIN_LITERAL.index("q quits"))

    def test_the_playing_line_has_no_leading_space(self):
        """Contradiction C-3, resolved towards STAT-2 rather than the picture.

        Row 29 of the specimen picture carries a leading space that the
        STAT-2 literal does not.  A7 takes the literal, so the text starts at
        column 0 of the row.
        """
        line = status_text(0, Outcome.UNDECIDED)

        self.assertEqual("s", line[0])
        self.assertEqual(26, len(line))


class TheScoreIsLive(unittest.TestCase):
    """The number on the line is the score it was handed, whatever it is."""

    def test_the_playing_line_shows_the_score_it_is_given(self):
        self.assertEqual(
            "score 1    arrows, q quits", status_text(1, Outcome.UNDECIDED)
        )

    def test_a_three_digit_score_does_not_corrupt_the_playing_line(self):
        self.assertEqual(
            "score 264    arrows, q quits",
            status_text(264, Outcome.UNDECIDED),
        )

    def test_a_three_digit_score_does_not_corrupt_the_loss_line(self):
        self.assertEqual(
            "CAUGHT  score 264   q quits", status_text(264, Outcome.CAUGHT)
        )

    def test_a_single_digit_score_does_not_corrupt_the_win_line(self):
        self.assertEqual(
            "CLEARED  score 7  q quits", status_text(7, Outcome.CLEARED)
        )

    def test_the_losing_turn_score_from_wi_11_reads_as_seven(self):
        """A8: the dot under the player is eaten on the losing turn.

        WI-11 measured the case — one dot left, on the ghost's square, score
        6 before the move — and it resolves to ``CAUGHT`` with score **7**.
        This is the last number a player ever sees, so it is worth having a
        line that shows what it looks like.  If the user reverses A8 the
        resolver changes, not this file: 6 would arrive here instead of 7.
        """
        self.assertEqual(
            "CAUGHT  score 7   q quits", status_text(7, Outcome.CAUGHT)
        )

    def test_a_three_digit_score_still_fits_a_forty_column_row(self):
        for outcome in Outcome:
            row = status_row(264, outcome)

            self.assertEqual(FRAME_COLUMNS, len(row))


class TheEndingIsChosenByTheOutcome(unittest.TestCase):
    """Which line appears is decided by the outcome and by nothing else."""

    def test_the_same_score_reads_three_different_ways(self):
        lines = [status_text(37, outcome) for outcome in Outcome]

        self.assertEqual(len(Outcome), len(set(lines)))

    def test_every_outcome_the_domain_has_produces_a_line(self):
        """There is no ending this module has not been taught about.

        ``Outcome`` is the Domain's vocabulary, landed in WI-6; this item
        selects by it and does not define it.  If a fourth member were ever
        added there, this is where it would be noticed.
        """
        for outcome in Outcome:
            self.assertTrue(status_text(0, outcome))

    def test_while_playing_the_line_names_neither_ending(self):
        line = status_text(12, Outcome.UNDECIDED)

        self.assertNotIn("CAUGHT", line)
        self.assertNotIn("CLEARED", line)

    def test_a_loss_names_the_loss_and_offers_no_arrows(self):
        line = status_text(12, Outcome.CAUGHT)

        self.assertTrue(line.startswith("CAUGHT"))
        self.assertNotIn("arrows", line)

    def test_a_win_names_the_win_and_offers_no_arrows(self):
        line = status_text(12, Outcome.CLEARED)

        self.assertTrue(line.startswith("CLEARED"))
        self.assertNotIn("arrows", line)

    def test_every_line_says_how_to_quit(self):
        """CTRL-4 and END-6: ``q`` is offered in every state, ending or not."""
        for outcome in Outcome:
            self.assertIn("q quits", status_text(0, outcome))

    def test_something_that_is_not_an_outcome_is_refused(self):
        """Not silently drawn as the playing line, which would look right."""
        for not_an_outcome in (None, "caught", 0, Outcome.CAUGHT.value):
            with self.assertRaises(ValueError):
                status_text(0, not_an_outcome)


class TheRowAsAValue(unittest.TestCase):
    """Row 29 is 40 cells of cyan, blank past the text (STAT-1, SCRN-6)."""

    def test_the_row_is_forty_cells(self):
        self.assertEqual(FRAME_COLUMNS, len(status_row(0, Outcome.UNDECIDED)))

    def test_every_cell_of_the_row_is_cyan(self):
        for outcome in Outcome:
            for cell in status_row(37, outcome):
                self.assertEqual(Colour.STATUS_CYAN, cell.colour)

    def test_the_named_status_colour_is_the_one_the_requirements_name(self):
        """SCRN-6 — cyan, and it is the frame's cyan, not a second one."""
        self.assertIs(Colour.STATUS_CYAN, STATUS_COLOUR)

    def test_the_glyphs_of_the_row_are_the_text_then_blanks(self):
        row = status_row(0, Outcome.UNDECIDED)

        glyphs = "".join(cell.glyph for cell in row)
        self.assertEqual(STAT_2_LITERAL, glyphs[: len(STAT_2_LITERAL)])
        self.assertEqual(
            " " * (FRAME_COLUMNS - len(STAT_2_LITERAL)),
            glyphs[len(STAT_2_LITERAL):],
        )

    def test_every_cell_is_one_character(self):
        for cell in status_row(274, Outcome.CLEARED):
            self.assertIsInstance(cell, Cell)
            self.assertEqual(1, len(cell.glyph))

    def test_the_row_placed_in_a_frame_reads_back_as_the_line(self):
        """The shape WI-12 will use: place row 29, write nothing on it.

        This asserts that what this item hands over is acceptable to
        ``place_row`` and survives it unchanged — the join, not what the
        composer does with rows 0..28, which is WI-12's own.
        """
        builder = FrameBuilder()
        builder.place_row(STATUS_ROW, status_row(37, Outcome.CAUGHT))

        frame = builder.build()
        self.assertEqual(
            STAT_3_LOSS_LITERAL.ljust(FRAME_COLUMNS),
            frame.row_text(STATUS_ROW),
        )

    def test_the_status_row_is_the_bottom_row(self):
        """STAT-1 — the row this item owns is the last one on screen."""
        self.assertEqual(29, STATUS_ROW)


class ABadScoreIsRefused(unittest.TestCase):
    """A wrong score reaching the line would look plausible on screen."""

    def test_a_negative_score_is_refused(self):
        with self.assertRaises(ValueError):
            status_text(-1, Outcome.UNDECIDED)

    def test_a_score_that_is_not_a_whole_number_is_refused(self):
        for not_a_score in (1.5, "37", None):
            with self.assertRaises(TypeError):
                status_text(not_a_score, Outcome.UNDECIDED)

    def test_a_boolean_is_not_a_score(self):
        """``True`` is an ``int`` in Python and would read as ``score 1``."""
        with self.assertRaises(TypeError):
            status_text(True, Outcome.UNDECIDED)


if __name__ == "__main__":
    unittest.main()
