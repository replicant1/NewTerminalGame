"""WI-6 — the status line. STAT-1, STAT-2, STAT-3, SCRN-6.

**The three literal strings below are transcribed from the specification**, not
built by the code under test. That is what makes the tests that use them worth
anything: a status line asserted equal to a string the test itself assembled
from the same parts would agree with the implementation however wrong both
were.

Two green results would otherwise be meaningless, so each is guarded by a test
that answers differently:

* **if the score were never updated** — several tests use two different scores
  and assert the lines differ, and one plays a real game and follows the score
  up through the moves that raise it;
* **if the ending were never distinguished** — the loss and win lines are
  asserted to differ from each other, and each is asserted *not* to contain the
  other's word, so a line that said the same thing either way would fail.
"""

from __future__ import annotations

import random
import unittest

from terminalgame.domain.game_state import GameState, Outcome, new_game
from terminalgame.domain.maze import DIRECTIONS, EAST, Maze
from terminalgame.domain.rules import advance_player
from terminalgame.presentation.status_line import (
    ENDED_KEYS,
    PLAYING_KEYS,
    SCORE_FIELD_WIDTH,
    STATUS_COLOUR,
    StatusLineWillNotFit,
    score_field,
    status_row,
    status_text,
)
from terminalgame.screen.port import REQUIRED_WIDTH, Colour

# --- transcribed from docs/FUNCTIONAL_REQUIREMENTS.md ---------------------
#
# The play line is line 71 of that file, inside the picture's code block, and
# is 27 characters including the leading space. The two ending lines are quoted
# in STAT-3. Nothing here is generated; if the specification changes, these
# change by hand.
DURING_PLAY = " score 0    arrows, q quits"
ON_A_LOSS = "CAUGHT  score 37   q quits"
ON_A_WIN = "CLEARED  score 274  q quits"

SMALL = [
    "#####",
    "#   #",
    "# # #",
    "#   #",
    "#####",
]


def a_state(score=0, outcome=Outcome.PLAYING):
    maze = Maze.from_text("\n".join(SMALL))
    return GameState(maze=maze, player=(1, 1), ghost=(3, 3),
                     ghost_heading=EAST,
                     dots=set(maze.corridor_squares()) - {(1, 1)},
                     score=score, outcome=outcome)


class TheLinesTheSpecificationQuotes(unittest.TestCase):
    """Each of the three, character for character."""

    def test_during_play(self):
        self.assertEqual(DURING_PLAY, status_text(a_state(score=0)))

    def test_on_a_loss(self):
        self.assertEqual(
            ON_A_LOSS, status_text(a_state(score=37, outcome=Outcome.CAUGHT)))

    def test_on_a_win(self):
        self.assertEqual(
            ON_A_WIN, status_text(a_state(score=274, outcome=Outcome.CLEARED)))


class TheLeadingSpace(unittest.TestCase):
    """The question §6 of the plan records, decided and pinned here.

    The picture shows the play line with a leading space; STAT-2 quotes it
    without one. This keeps the space — an assumption, not a ruling.
    """

    def test_the_play_line_begins_with_one_space(self):
        line = status_text(a_state(score=0))
        self.assertTrue(line.startswith(" "))
        self.assertFalse(line.startswith("  "), "one space, not two")
        self.assertEqual("score", line.lstrip()[:5])

    def test_it_is_the_twenty_seven_characters_the_picture_shows(self):
        self.assertEqual(27, len(status_text(a_state(score=0))))

    def test_the_ending_lines_are_not_indented(self):
        # STAT-3 is the only evidence for those two and shows no leading
        # space, so they follow their own quote rather than the picture's.
        self.assertFalse(status_text(a_state(1, Outcome.CAUGHT)).startswith(" "))
        self.assertFalse(status_text(a_state(1, Outcome.CLEARED)).startswith(" "))


class TheScoreIsKeptUpToDate(unittest.TestCase):
    """STAT-2. Green against a line that ignored the score, without these."""

    def test_a_different_score_gives_a_different_line(self):
        self.assertNotEqual(status_text(a_state(score=0)),
                            status_text(a_state(score=1)))

    def test_the_score_appears_in_the_line(self):
        for score in (0, 1, 9, 10, 99, 100, 268):
            self.assertIn("score {0}".format(score),
                          status_text(a_state(score=score)))

    def test_it_follows_a_real_game_up(self):
        """Played rather than constructed, so the two halves are joined.

        The score must both rise and be shown rising; asserting only that the
        line matches the state would pass if neither ever changed.
        """
        state = new_game(4)
        walker = random.Random(4)
        seen = set()
        for _ in range(200):
            state = advance_player(state, walker.choice(DIRECTIONS))
            self.assertIn("score {0}".format(state.score), status_text(state))
            seen.add(state.score)
        self.assertGreater(state.score, 0, "the walk never ate a dot")
        self.assertGreater(len(seen), 1, "the score never changed")

    def test_the_line_grows_by_a_column_when_the_score_needs_a_fourth_digit(self):
        # The field is nine wide because three digits is enough for this maze.
        # A wider number is not refused, it just makes the line one longer.
        self.assertEqual(len(status_text(a_state(score=999))) + 1,
                         len(status_text(a_state(score=1000))))


class TheTwoEndingsAreDistinguished(unittest.TestCase):
    """STAT-3. Green against a line that said the same thing either way."""

    def test_a_loss_and_a_win_do_not_read_the_same(self):
        self.assertNotEqual(status_text(a_state(5, Outcome.CAUGHT)),
                            status_text(a_state(5, Outcome.CLEARED)))

    def test_a_loss_says_caught_and_not_cleared(self):
        line = status_text(a_state(37, Outcome.CAUGHT))
        self.assertIn("CAUGHT", line)
        self.assertNotIn("CLEARED", line)

    def test_a_win_says_cleared_and_not_caught(self):
        line = status_text(a_state(274, Outcome.CLEARED))
        self.assertIn("CLEARED", line)
        self.assertNotIn("CAUGHT", line)

    def test_both_endings_still_show_the_final_score(self):
        self.assertIn("score 42", status_text(a_state(42, Outcome.CAUGHT)))
        self.assertIn("score 42", status_text(a_state(42, Outcome.CLEARED)))

    def test_neither_ending_line_offers_the_arrow_keys(self):
        # END-5: the arrow keys do nothing once the game is over, so the line
        # must stop advertising them.
        for outcome in (Outcome.CAUGHT, Outcome.CLEARED):
            line = status_text(a_state(3, outcome))
            self.assertIn(ENDED_KEYS, line)
            self.assertNotIn("arrows", line)

    def test_the_playing_line_does_offer_them(self):
        # Without this, the test above passes against a line that never
        # mentions the arrow keys at all.
        self.assertIn(PLAYING_KEYS, status_text(a_state(3)))
        self.assertIn("arrows", status_text(a_state(3)))


class TheAlignmentBetweenTheTwoEndings(unittest.TestCase):
    """Checked rather than assumed, and judged incidental.

    `q quits` begins one column later on a win than on a loss. That falls out
    of CAUGHT being six letters and CLEARED seven, and it is unobservable: a
    game ends one way, so a player never sees both lines.
    """

    def test_the_two_quoted_lines_really_do_disagree(self):
        self.assertEqual(19, ON_A_LOSS.index("q quits"))
        self.assertEqual(20, ON_A_WIN.index("q quits"))

    def test_one_rule_still_produces_both_of_them(self):
        # The difference is in the words, not in the spacing: the score field
        # is the same width in both, and so are the gaps around it.
        self.assertEqual(ON_A_LOSS.index("q quits") - ON_A_WIN.index("q quits"),
                         len("CAUGHT") - len("CLEARED"))

    def test_the_score_field_is_one_fixed_width_in_both(self):
        self.assertEqual(SCORE_FIELD_WIDTH, len(score_field(37)))
        self.assertEqual(SCORE_FIELD_WIDTH, len(score_field(274)))


class TheBottomRow(unittest.TestCase):
    """STAT-1 — the score and the keys, and nothing else."""

    def test_the_row_is_exactly_as_wide_as_the_window(self):
        self.assertEqual(REQUIRED_WIDTH, len(status_row(a_state(score=0))))

    def test_the_row_is_the_line_and_then_blanks(self):
        row = status_row(a_state(score=0))
        self.assertTrue(row.startswith(DURING_PLAY))
        self.assertEqual("", row[len(DURING_PLAY):].strip())

    def test_a_shorter_line_still_covers_the_whole_row(self):
        """Otherwise the tail of the previous frame's line stays on screen.

        The loss line is shorter than the play line, so this is the case that
        would actually leave something behind.
        """
        self.assertLess(len(ON_A_LOSS), len(DURING_PLAY))
        row = status_row(a_state(37, Outcome.CAUGHT))
        self.assertEqual(REQUIRED_WIDTH, len(row))

    def test_it_carries_nothing_but_the_score_and_the_keys(self):
        row = status_row(a_state(score=7))
        self.assertEqual("score 7    arrows, q quits", row.strip())

    def test_a_row_too_narrow_to_say_it_is_refused_rather_than_truncated(self):
        # Losing the end of the line would lose `q quits`, which END-6 makes
        # the only way out of a finished game.
        with self.assertRaises(StatusLineWillNotFit) as caught:
            status_row(a_state(score=0), width=10)
        self.assertIn("STAT-1", str(caught.exception))

    def test_a_row_exactly_wide_enough_is_not_refused(self):
        text = status_text(a_state(score=0))
        self.assertEqual(text, status_row(a_state(score=0), width=len(text)))


class TheColour(unittest.TestCase):
    """SCRN-6 — the status line is written in cyan."""

    def test_it_asks_for_the_status_colour(self):
        self.assertEqual(Colour.STATUS, STATUS_COLOUR)

    def test_it_is_not_any_of_the_others(self):
        for other in (Colour.WALL, Colour.DOT, Colour.PLAYER, Colour.GHOST,
                      Colour.DEFAULT):
            self.assertNotEqual(other, STATUS_COLOUR)


class ItIsPresentationAndNothingMore(unittest.TestCase):

    def test_reading_the_line_does_not_change_the_state(self):
        state = a_state(score=3)
        snapshot = {field: getattr(state, field) for field in GameState.FIELDS}
        status_text(state)
        status_row(state)
        for field, value in snapshot.items():
            self.assertEqual(value, getattr(state, field))

    def test_the_same_state_always_gives_the_same_line(self):
        state = a_state(score=11)
        self.assertEqual(status_text(state), status_text(state))


if __name__ == "__main__":
    unittest.main()
