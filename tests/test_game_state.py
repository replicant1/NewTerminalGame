"""WI-7: the GameState value that setup makes, turns change, and the composer reads."""

from __future__ import annotations

import dataclasses

import pytest

from terminal_game.domain import game_state
from terminal_game.domain.game_state import GameState
from terminal_game.domain.maze import Maze
from terminal_game.presentation import status_line

MAZE = Maze.from_rows(["#####", "#...#", "#####"])


def test_a4_the_outcome_values_are_the_status_lines_own():
    """The seam with WI-5: the composer can pass state.outcome to status_text unchanged."""
    assert (game_state.PLAYING, game_state.LOST, game_state.WON) == (
        status_line.PLAYING,
        status_line.LOST,
        status_line.WON,
    )
    assert status_line.status_text(3, game_state.LOST).startswith(" CAUGHT  score 3")


def test_a4_a_state_cannot_be_changed_in_place():
    state = GameState(maze=MAZE, player=(1, 1), ghost=(3, 1), dots=frozenset({(2, 1), (3, 1)}))
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.score = 1
    assert state.score == 0


def test_a4_a_state_does_not_share_the_set_of_dots_it_was_built_from():
    handed_in = {(2, 1), (3, 1)}
    state = GameState(maze=MAZE, player=(1, 1), ghost=(3, 1), dots=handed_in)
    handed_in.clear()
    assert state.dots == {(2, 1), (3, 1)}
    assert isinstance(state.dots, frozenset)


def test_a4_the_next_state_is_made_by_replace_and_the_old_one_is_untouched():
    before = GameState(maze=MAZE, player=(1, 1), ghost=(3, 1), dots={(2, 1), (3, 1)})
    after = dataclasses.replace(before, player=(2, 1), dots=before.dots - {(2, 1)}, score=1)
    assert (after.player, after.dots, after.score) == ((2, 1), {(3, 1)}, 1)
    assert (before.player, before.dots, before.score) == ((1, 1), {(2, 1), (3, 1)}, 0)
    assert after != before
    assert dataclasses.replace(before) == before
