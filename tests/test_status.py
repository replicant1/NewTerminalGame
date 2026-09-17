"""Row 29: STAT-1, STAT-2, STAT-3 and SCRN-6.

The three strings the specification prints verbatim are pinned as exact
strings, and the specimen's own bottom row is read out of
``docs/FUNCTIONAL_REQUIREMENTS.md`` and compared — so the literals here cannot
drift away from the document they came from.

Not re-asserted here: that a field is 40 x 30 or that `write` puts one
character in each cell (``tests/test_field.py``), that cyan is cyan
(``tests/test_palette.py``), or what the painter does with the result
(``tests/test_surface.py``).
"""

from __future__ import annotations

import os
import re

import pytest

from terminal_game.application.turn import outcome_of
from terminal_game.domain.state import GameState, Outcome, new_game
from terminal_game.presentation import palette
from terminal_game.presentation.field import Field
from terminal_game.presentation.metrics import COLUMNS, ROWS
from terminal_game.presentation.status import (
    LEADING_SPACE,
    SCORE_FIELD_WIDTH,
    STATUS_COLOUR,
    STATUS_ROW,
    is_decided,
    status_for,
    status_text,
)


def specimen_status_row() -> str:
    """The bottom row of the specimen picture, read from the requirements.

    Raises rather than returning something empty: a fixture that silently
    finds nothing turns every test built on it green for the wrong reason.
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs",
        "FUNCTIONAL_REQUIREMENTS.md",
    )
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    marker = "A game in progress looks like this:"
    if marker not in text:
        raise AssertionError(
            "{} no longer contains {!r}; ruling C-4 makes the specimen "
            "normative for the status line, so fix the locator rather than "
            "deleting what depends on it".format(path, marker)
        )
    fenced = text.split(marker, 1)[1].split("```")[1]
    rows = [re.split(r"\s{3,}←", line)[0] for line in fenced.split("\n") if line.strip()]
    if len(rows) != ROWS:
        raise AssertionError(
            "the specimen parsed to {} rows, not {}".format(len(rows), ROWS)
        )
    return rows[-1]


class TestTheThreeStringsTheSpecificationPrints:
    """The only three fully worked examples there are. Pinned verbatim."""

    def test_the_playing_line_at_score_zero(self):
        assert status_text(Outcome.UNDECIDED, 0) == " score 0    arrows, q quits"

    def test_the_caught_line_at_score_thirty_seven(self):
        assert status_text(Outcome.CAUGHT, 37) == " CAUGHT  score 37   q quits"

    def test_the_cleared_line_at_score_two_seven_four(self):
        assert status_text(Outcome.CLEARED, 274) == " CLEARED  score 274  q quits"

    @pytest.mark.parametrize(
        "outcome, score, printed",
        [
            (Outcome.UNDECIDED, 0, "score 0    arrows, q quits"),
            (Outcome.CAUGHT, 37, "CAUGHT  score 37   q quits"),
            (Outcome.CLEARED, 274, "CLEARED  score 274  q quits"),
        ],
    )
    def test_each_is_the_requirement_text_with_one_leading_space(
        self, outcome, score, printed
    ):
        # Ruling C-4 in one assertion: the specimen's leading space, then the
        # requirement's own text, character for character.
        assert status_text(outcome, score) == LEADING_SPACE + printed


class TestAgainstTheSpecimenItself:
    """C-4 makes the specimen normative, so read it rather than quote it."""

    def test_the_specimen_bottom_row_is_the_playing_line(self):
        assert status_text(Outcome.UNDECIDED, 0) == specimen_status_row()

    def test_the_specimen_bottom_row_has_one_leading_space(self):
        row = specimen_status_row()
        assert row.startswith(" ")
        assert not row.startswith("  ")

    def test_the_specimen_bottom_row_is_twenty_seven_characters(self):
        assert len(specimen_status_row()) == 27


class TestStatTwoTheScoreIsKeptUpToDate:
    """STAT-2: the playing line, at every score the game can reach."""

    @pytest.mark.parametrize("score", [0, 1, 9, 10, 37, 99, 100, 274, 551])
    def test_the_score_appears_in_the_line(self, score):
        assert "score {}".format(score) in status_text(Outcome.UNDECIDED, score)

    @pytest.mark.parametrize("score", [0, 1, 9, 10, 99, 100, 551])
    def test_the_keys_are_named_whatever_the_score(self, score):
        assert status_text(Outcome.UNDECIDED, score).endswith("arrows, q quits")

    @pytest.mark.parametrize("score", [0, 9, 10, 99, 100, 551])
    def test_the_tail_stays_in_one_column_as_the_score_grows(self, score):
        # The reason the score sits in a field rather than after a fixed gap:
        # STAT-2 keeps the score up to date all game, and a tail that slides
        # right every time the score crosses a power of ten is something the
        # player watches happen.
        assert status_text(Outcome.UNDECIDED, score).index("arrows") == 12

    def test_a_score_wider_than_the_field_still_renders(self):
        # The field does not truncate.  No real game reaches this - a 19 x 29
        # grid holds at most 551 dots - but a line that silently lost digits
        # would be worse than a long one.
        assert "score 1234567" in status_text(Outcome.UNDECIDED, 1234567)

    def test_the_score_field_is_five_wide(self):
        # Uniquely determined by the three printed examples; 4 and 6 match
        # none of them. See the module docstring.
        assert SCORE_FIELD_WIDTH == 5


class TestStatThreeTheLineSaysWhichEndingHappened:
    """STAT-3: *"so the line says which of the two endings happened"*."""

    def test_a_loss_says_caught(self):
        assert status_text(Outcome.CAUGHT, 37).lstrip().startswith("CAUGHT")

    def test_a_win_says_cleared(self):
        assert status_text(Outcome.CLEARED, 274).lstrip().startswith("CLEARED")

    def test_the_two_endings_do_not_read_alike(self):
        assert status_text(Outcome.CAUGHT, 100) != status_text(Outcome.CLEARED, 100)

    def test_a_loss_never_reads_as_a_win(self):
        assert "CLEARED" not in status_text(Outcome.CAUGHT, 37)

    def test_a_win_never_reads_as_a_loss(self):
        assert "CAUGHT" not in status_text(Outcome.CLEARED, 274)

    @pytest.mark.parametrize("outcome", [Outcome.CAUGHT, Outcome.CLEARED])
    def test_an_ending_drops_the_arrows(self, outcome):
        # The arrows do nothing once the game is decided (END-5), so the line
        # stops offering them and only `q` is left (END-6).
        line = status_text(outcome, 42)
        assert "arrows" not in line
        assert line.endswith("q quits")

    @pytest.mark.parametrize("outcome", [Outcome.CAUGHT, Outcome.CLEARED])
    @pytest.mark.parametrize("score", [0, 1, 37, 274, 551])
    def test_the_final_score_is_shown(self, outcome, score):
        assert "score {}".format(score) in status_text(outcome, score)


class TestStatOneTheRowCarriesTheStatusAndNothingElse:
    """STAT-1, as the row a composer would actually write."""

    @pytest.mark.parametrize(
        "outcome, score",
        [
            (Outcome.UNDECIDED, 0),
            (Outcome.UNDECIDED, 551),
            (Outcome.CAUGHT, 37),
            (Outcome.CLEARED, 274),
        ],
    )
    def test_the_row_written_reads_back_as_the_status_and_then_blank(
        self, outcome, score
    ):
        # The whole interface, exercised the way WI-4b uses it.
        field = Field()
        text = status_text(outcome, score)
        field.write(0, STATUS_ROW, text, STATUS_COLOUR)
        assert field.row_text(STATUS_ROW) == text.ljust(COLUMNS)

    def test_nothing_of_the_status_lands_on_any_other_row(self):
        field = Field()
        field.write(0, STATUS_ROW, status_text(Outcome.CLEARED, 274), STATUS_COLOUR)
        assert [row for row in list(field.rows())[:-1] if row.strip()] == []

    @pytest.mark.parametrize(
        "outcome, score",
        [(Outcome.UNDECIDED, 551), (Outcome.CAUGHT, 551), (Outcome.CLEARED, 551)],
    )
    def test_every_form_fits_the_row(self, outcome, score):
        # A line longer than the row would raise when written; the longest
        # form at the highest reachable score is the worst case.
        assert len(status_text(outcome, score)) <= COLUMNS
        Field().write(0, STATUS_ROW, status_text(outcome, score), STATUS_COLOUR)

    def test_the_status_row_is_the_bottom_one(self):
        assert STATUS_ROW == ROWS - 1 == 29


class TestScrnSixCyan:

    def test_the_status_colour_is_cyan(self):
        assert STATUS_COLOUR == palette.STATUS

    def test_every_cell_of_the_written_row_is_cyan(self):
        field = Field()
        text = status_text(Outcome.UNDECIDED, 0)
        field.write(0, STATUS_ROW, text, STATUS_COLOUR)
        assert {field[c, STATUS_ROW].colour for c in range(len(text))} == {
            palette.STATUS
        }


class TestTheVocabularyIsTheWholeVocabulary:
    """Three outcomes, three forms, and no way to ask for a fourth."""

    @pytest.mark.parametrize("outcome", list(Outcome))
    def test_every_outcome_has_a_line(self, outcome):
        assert status_text(outcome, 0).strip()

    def test_there_are_exactly_three_outcomes(self):
        assert len(list(Outcome)) == 3

    @pytest.mark.parametrize("outcome", ["caught", None, 0, "UNDECIDED"])
    def test_something_that_is_not_an_outcome_is_refused(self, outcome):
        with pytest.raises(TypeError):
            status_text(outcome, 0)

    def test_a_game_in_play_is_not_decided(self):
        assert not is_decided(Outcome.UNDECIDED)

    @pytest.mark.parametrize("outcome", [Outcome.CAUGHT, Outcome.CLEARED])
    def test_an_ending_is_decided(self, outcome):
        assert is_decided(outcome)


class TestStatusForAGameState:
    """`status_for` asks the derived function, never the stored field.

    `GameState.outcome` is a cache the resolver stamps; `turn.outcome_of` is
    the derived total truth, and on a hand-built board the two can disagree.
    Lane A found that in WI-11. The same crack runs through the status line:
    if the session asks the function and the status line reads the field, the
    second source of truth has moved here instead of being removed — and it
    would show as a decided game still offering `arrows, q quits` while the
    picture sits frozen behind it.
    """

    def test_a_game_in_play_reads_as_a_game_in_play(self, sound_maze):
        state = new_game(sound_maze)
        assert status_for(state) == status_text(Outcome.UNDECIDED, 0)

    def test_the_score_shown_is_the_one_the_state_holds(self, sound_maze):
        started = new_game(sound_maze)
        state = GameState(
            sound_maze, started.dots, started.player, started.ghost, score=37
        )
        assert status_for(state) == status_text(Outcome.UNDECIDED, 37)

    def test_a_caught_board_reads_as_caught_even_when_stamped_undecided(
        self, sound_maze
    ):
        # The whole point. Both actors on one square, and the stored field
        # left saying the game is still on. `outcome_of` says CAUGHT; a
        # status line that read the field would still be offering the arrows.
        square = sorted(sound_maze.corridors())[0]
        state = GameState(
            sound_maze,
            dots=[],
            player=square,
            ghost=square,
            score=37,
            outcome=Outcome.UNDECIDED,
        )
        assert state.outcome is Outcome.UNDECIDED       # the stale stamp
        assert outcome_of(state) is Outcome.CAUGHT      # the truth
        assert status_for(state) == status_text(Outcome.CAUGHT, 37)
        assert "arrows" not in status_for(state)

    def test_a_cleared_board_reads_as_cleared_even_when_stamped_undecided(
        self, sound_maze
    ):
        corridors = sorted(sound_maze.corridors())
        state = GameState(
            sound_maze,
            dots=[],
            player=corridors[0],
            ghost=corridors[-1],
            score=274,
            outcome=Outcome.UNDECIDED,
        )
        assert state.outcome is Outcome.UNDECIDED
        assert outcome_of(state) is Outcome.CLEARED
        assert status_for(state) == status_text(Outcome.CLEARED, 274)

    def test_a_playing_board_reads_as_playing_even_when_stamped_caught(
        self, sound_maze
    ):
        # And the other way round, so the test is not simply "decided wins".
        corridors = sorted(sound_maze.corridors())
        state = GameState(
            sound_maze,
            dots=corridors[1:],
            player=corridors[0],
            ghost=corridors[-1],
            score=5,
            outcome=Outcome.CAUGHT,
        )
        assert state.outcome is Outcome.CAUGHT
        assert outcome_of(state) is Outcome.UNDECIDED
        assert status_for(state) == status_text(Outcome.UNDECIDED, 5)
        assert status_for(state).endswith("arrows, q quits")


class TestScoresThatAreNotScores:
    """SCORE-5: the score never goes down, and it starts at zero."""

    @pytest.mark.parametrize("score", [-1, -37])
    def test_a_negative_score_is_refused(self, score):
        with pytest.raises(ValueError):
            status_text(Outcome.UNDECIDED, score)

    @pytest.mark.parametrize("score", [1.0, "37", None, True])
    def test_a_score_that_is_not_a_whole_number_is_refused(self, score):
        # True is included deliberately: bool is an int in Python, and
        # `score True` would otherwise render as "score 1".
        with pytest.raises(TypeError):
            status_text(Outcome.UNDECIDED, score)
