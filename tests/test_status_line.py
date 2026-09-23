"""WI-5: the status line (STAT-1, STAT-2, STAT-3, SCRN-6, SCORE-5 display)."""

from __future__ import annotations

import pytest

from terminal_game.presentation import roles
from terminal_game.presentation.status_line import (LOST, PLAYING, WON, status_row,
                                                    status_text)

# The three examples, exactly as the plan's claims write them.
EXAMPLES = {
    PLAYING: (0, " score 0    arrows, q quits"),
    LOST: (37, " CAUGHT  score 37   q quits"),
    WON: (274, " CLEARED  score 274  q quits"),
}


def _cells_after_score(example: str, score: int) -> int:
    """The cell the text after the score starts in, measured on an example."""
    start = example.index("score ") + len("score ")
    after = start + len(str(score))
    while example[after] == " ":
        after += 1
    return after


def test_c1_during_play_with_a_score_of_0():
    assert status_text(0) == " score 0    arrows, q quits" + " " * 13


def test_c2_on_a_loss_with_37_and_on_a_win_with_274():
    assert status_text(37, LOST) == " CAUGHT  score 37   q quits" + " " * 13
    assert status_text(274, WON) == " CLEARED  score 274  q quits" + " " * 12


@pytest.mark.parametrize("outcome", [PLAYING, LOST, WON], ids=["playing", "lost", "won"])
def test_c3_every_score_from_0_to_459_keeps_the_row_and_the_columns(outcome):
    example_score, example = EXAMPLES[outcome]
    score_cell = example.index("score ") + len("score ")
    tail_cell = _cells_after_score(example, example_score)
    tail = example[tail_cell:]
    for score in range(460):
        text = status_text(score, outcome)
        assert len(text) == 40, score
        assert len(status_row(score, outcome)) == 40, score
        digits = str(score)
        assert text[score_cell:score_cell + len(digits)] == digits, score
        assert text[score_cell + len(digits)] == " ", score
        assert text[tail_cell:tail_cell + len(tail)] == tail, score
        assert text[score_cell + len(digits):tail_cell].strip() == "", score


@pytest.mark.parametrize("outcome, words", [
    (PLAYING, ["score", "{n}", "arrows,", "q", "quits"]),
    (LOST, ["CAUGHT", "score", "{n}", "q", "quits"]),
    (WON, ["CLEARED", "score", "{n}", "q", "quits"]),
], ids=["playing", "lost", "won"])
def test_c4_the_row_holds_the_state_word_the_score_and_the_key_hints_and_nothing_else(outcome, words):
    for score in (0, 9, 10, 99, 100, 459):
        assert status_text(score, outcome).split() == [w.format(n=score) for w in words]


def test_c5_every_cell_of_the_row_is_in_the_status_colour():
    for outcome in (PLAYING, LOST, WON):
        for score in (0, 37, 274, 459):
            row = status_row(score, outcome)
            assert {role for _, role in row} == {roles.STATUS}
            assert "".join(character for character, _ in row) == status_text(score, outcome)


def test_the_status_role_is_the_string_the_shell_palette_uses():
    assert roles.STATUS == "status"
    assert roles.ROLES == ("wall", "dot", "player", "ghost", "status", "background")


@pytest.mark.parametrize("score", [-1, 1.5, "3", True, None])
def test_a_score_that_is_not_a_whole_number_from_0_is_refused(score):
    with pytest.raises(ValueError, match="the score is a whole number"):
        status_text(score)


def test_an_unknown_outcome_is_refused():
    with pytest.raises(ValueError, match="unknown outcome 'drawn'"):
        status_text(0, "drawn")


def test_a_score_too_long_for_its_field_is_refused_rather_than_shifting_the_text():
    assert status_text(9999)[12:].startswith("arrows")
    with pytest.raises(ValueError, match="does not fit"):
        status_text(10000)
