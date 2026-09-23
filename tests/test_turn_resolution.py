"""WI-11: turn resolution (plan §4, WI-11/C1-C11).

Hand-built mazes and states give expected results that can be read off the
picture. The two long-run claims (C5, C11) play 1,000 generated games.
"""

from __future__ import annotations

import random

import pytest

from terminal_game.application.turn_resolution import move_player, step_ghost
from terminal_game.domain.game_setup import new_game
from terminal_game.domain.game_state import LOST, PLAYING, WON, GameState
from terminal_game.domain.ghost import ghost_step
from terminal_game.domain.maze import DIRECTIONS, Maze
from terminal_game.domain.maze_generator import generate_maze

N, S, E, W = (0, -1), (0, 1), (1, 0), (-1, 0)

# A crossroads, centre (2, 2), and a long corridor along row 1.
CROSS = Maze.from_rows(["#####", "##.##", "#...#", "##.##", "#####"])
CORRIDOR = Maze.from_rows(["#########", "#.......#", "#########"])


def state(maze, player, ghost, dots=None, score=0, outcome=PLAYING, heading=None):
    if dots is None:
        dots = set(maze.corridor_squares()) - {player}
    return GameState(maze=maze, player=player, ghost=ghost, dots=frozenset(dots),
                     score=score, outcome=outcome, ghost_heading=heading)


class NoDraws:
    """A random source that fails the test if the policy ever draws from it."""

    def choice(self, seq):
        raise AssertionError(f"unexpected random draw from {seq!r}")


# --- C1 ---------------------------------------------------------------------

@pytest.mark.parametrize("direction, expected", [(N, (2, 1)), (S, (2, 3)), (E, (3, 2)), (W, (1, 2))])
def test_c1_a_move_towards_a_corridor_square_moves_exactly_one_square_that_way(direction, expected):
    before = state(CROSS, (2, 2), ghost=(7, 7), dots=set())  # ghost parked off the grid, out of the way
    assert move_player(before, direction).player == expected


def test_c1_one_move_along_a_long_corridor_is_one_square_not_to_the_end():
    before = state(CORRIDOR, (1, 1), ghost=(7, 1), dots=set())
    assert move_player(before, E).player == (2, 1)


# --- C2 ---------------------------------------------------------------------

@pytest.mark.parametrize("player, direction", [((2, 1), N), ((2, 1), E), ((2, 1), W), ((1, 2), N), ((3, 2), S)])
def test_c2_a_move_towards_a_wall_changes_nothing_at_all(player, direction):
    before = state(CROSS, player, ghost=(2, 3), score=4)
    after = move_player(before, direction)
    assert (after.player, after.dots, after.score, after.outcome, after.ghost, after.ghost_heading) == (
        before.player, before.dots, before.score, before.outcome, before.ghost, before.ghost_heading)
    assert after == before


# --- C3, C4 -----------------------------------------------------------------

def test_c3_moving_onto_a_dot_removes_it_for_the_rest_of_the_game_and_adds_one():
    s0 = state(CORRIDOR, (1, 1), ghost=(7, 1), dots={(2, 1), (3, 1)}, score=5)
    s1 = move_player(s0, E)
    assert (s1.player, s1.dots, s1.score) == ((2, 1), {(3, 1)}, 6)
    s2 = move_player(move_player(s1, W), E)  # away and back again
    assert (s2.player, s2.dots, s2.score) == ((2, 1), {(3, 1)}, 6)
    assert (2, 1) not in s2.dots


def test_c4_a_square_already_eaten_including_the_start_square_adds_nothing():
    s0 = state(CORRIDOR, (1, 1), ghost=(7, 1), dots={(3, 1)}, score=2)  # (1, 1) start, (2, 1) eaten
    s1 = move_player(s0, E)
    assert (s1.player, s1.score, s1.dots) == ((2, 1), 2, {(3, 1)})
    s2 = move_player(s1, W)
    assert (s2.player, s2.score, s2.dots) == ((1, 1), 2, {(3, 1)})


def test_c4_the_real_start_square_holds_no_dot_and_returning_to_it_scores_nothing():
    game = new_game(generate_maze(random.Random(3)))
    step = next(d for d in DIRECTIONS if game.maze.is_corridor((game.player[0] + d[0], game.player[1] + d[1])))
    away = move_player(game, step)
    back = move_player(away, (-step[0], -step[1]))
    assert back.player == game.player
    assert back.score == away.score


# --- C5, C11: long runs -----------------------------------------------------

def play(seed, turns, ghost_moves):
    """Play one random game; return the maze and every (before, after) pair of states."""
    maze = generate_maze(random.Random(seed))
    game = new_game(maze)
    moves = random.Random(10_000 + seed)
    ghost_rng = random.Random(20_000 + seed)
    seen = []
    for _ in range(turns):
        before = game
        game = move_player(game, moves.choice(DIRECTIONS))
        seen.append((before, game))
        if ghost_moves:
            before = game
            game = step_ghost(game, ghost_rng)
            seen.append((before, game))
    return maze, seen


def test_c5_over_1000_games_of_random_moves_and_ghost_steps_the_score_never_goes_down():
    eaten = 0
    for seed in range(1000):
        _, seen = play(seed, 1000, ghost_moves=True)
        for before, after in seen:
            assert after.score >= before.score, seed
            eaten += after.score - before.score
    assert eaten > 1000, "hardly anything was eaten, so the check said little"


def test_c11_over_1000_games_of_1000_random_moves_the_player_never_stands_on_a_wall_or_leaves():
    moved = 0
    for seed in range(1000):
        maze, seen = play(seed, 1000, ghost_moves=False)
        for before, after in seen:
            p = after.player
            assert 0 <= p[0] < 19 and 0 <= p[1] < 29, (seed, p)
            assert maze.is_corridor(p), (seed, p)
            d = (p[0] - before.player[0], p[1] - before.player[1])
            assert d == (0, 0) or d in DIRECTIONS, (seed, d)
            moved += d != (0, 0)
    assert moved > 100_000, f"only {moved} moves changed square, so the walk said little"


# --- C6, C7, C10 -------------------------------------------------------------

def test_c6_the_player_walking_onto_the_ghosts_square_loses():
    after = move_player(state(CORRIDOR, (3, 1), ghost=(4, 1)), E)
    assert (after.player, after.outcome) == ((4, 1), LOST)


def test_c7_the_ghost_stepping_onto_the_players_square_loses():
    # The ghost at (5, 1) heading west along the corridor: straight on is (4, 1), where the player is.
    before = state(CORRIDOR, (4, 1), ghost=(5, 1), heading=W)
    after = step_ghost(before, NoDraws())
    assert (after.ghost, after.outcome) == ((4, 1), LOST)


def test_c10_from_adjacent_squares_a_player_move_towards_the_ghost_loses_on_that_step():
    after = move_player(state(CORRIDOR, (3, 1), ghost=(4, 1), heading=W), E)
    assert after.outcome == LOST
    assert after.player == after.ghost == (4, 1)  # met, not swapped


def test_c10_from_adjacent_squares_a_ghost_step_towards_the_player_loses_on_that_step():
    after = step_ghost(state(CORRIDOR, (3, 1), ghost=(4, 1), heading=W), NoDraws())
    assert after.outcome == LOST
    assert after.player == after.ghost == (3, 1)  # met, not swapped


def test_c10_the_ghost_turning_back_onto_an_adjacent_player_also_meets_them():
    # Dead end at (7, 1): the ghost heading east must turn back west onto the player at (6, 1).
    after = step_ghost(state(CORRIDOR, (6, 1), ghost=(7, 1), heading=E), NoDraws())
    assert (after.ghost, after.outcome) == ((6, 1), LOST)


# --- C8, C9 -----------------------------------------------------------------

def test_c8_eating_the_last_dot_wins():
    after = move_player(state(CORRIDOR, (2, 1), ghost=(7, 1), dots={(3, 1)}, score=9), E)
    assert (after.player, after.dots, after.score, after.outcome) == ((3, 1), frozenset(), 10, WON)


def test_c8_eating_a_dot_that_is_not_the_last_does_not_win():
    after = move_player(state(CORRIDOR, (2, 1), ghost=(7, 1), dots={(3, 1), (5, 1)}), E)
    assert after.outcome is PLAYING


def test_c9_walking_onto_the_ghosts_square_when_it_holds_the_last_dot_loses_and_the_dot_is_not_eaten():
    before = state(CORRIDOR, (2, 1), ghost=(3, 1), dots={(3, 1)}, score=41)
    after = move_player(before, E)
    assert after.outcome == LOST
    assert after.outcome != WON
    assert after.dots == {(3, 1)}
    assert after.score == 41
    assert after.player == (3, 1)


# --- A claims ------------------------------------------------------------------

@pytest.mark.parametrize("outcome", [LOST, WON])
def test_a1_once_decided_neither_a_move_nor_a_ghost_step_changes_anything(outcome):
    decided = state(CORRIDOR, (3, 1), ghost=(5, 1), heading=W, outcome=outcome, score=7)
    for d in DIRECTIONS:
        assert move_player(decided, d) is decided
    assert step_ghost(decided, NoDraws()) is decided


@pytest.mark.parametrize("bad", [(1, 1), (0, 0), (2, 0), None, "up"])
def test_a2_a_direction_that_is_not_one_square_north_south_east_or_west_is_refused(bad):
    with pytest.raises(ValueError, match="a direction is one of"):
        move_player(state(CROSS, (2, 2), ghost=(2, 1)), bad)


def test_a3_a_ghost_step_applies_exactly_what_the_policy_returns_and_leaves_dots_and_score_alone():
    """The seam with WI-8: square and heading are the policy's, for the same inputs and random state."""
    game = new_game(generate_maze(random.Random(8)))
    rng_a, rng_b = random.Random(99), random.Random(99)
    for _ in range(200):
        if game.outcome is not PLAYING:
            break
        expected = ghost_step(game.maze, game.ghost, game.ghost_heading, rng_b)
        after = step_ghost(game, rng_a)
        assert (after.ghost, after.ghost_heading) == (expected.square, expected.heading)
        assert (after.dots, after.score, after.player) == (game.dots, game.score, game.player)
        game = after
