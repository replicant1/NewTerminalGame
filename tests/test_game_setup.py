"""WI-7: the starting position of a game (plan §4, WI-7/C1-C7).

Hand-built mazes give expected squares that can be read off the picture. The
claims over generated mazes recompute nearest and furthest here, from the
maze's rows, rather than trusting the code under test.
"""

from __future__ import annotations

import random
from collections import deque

import pytest

from terminal_game.domain.game_setup import new_game
from terminal_game.domain.game_state import LOST, PLAYING, WON
from terminal_game.domain.maze import Maze
from terminal_game.domain.maze_generator import generate_maze

SEEDS = range(1000)
CENTRE = (9, 14)


@pytest.fixture(scope="module")
def generated():
    """``(seed, maze, state)`` for 1,000 generated mazes."""
    out = []
    for seed in SEEDS:
        maze = generate_maze(random.Random(seed))
        out.append((seed, maze, new_game(maze)))
    return out


def corridors_of(maze):
    return [(c, r) for r, line in enumerate(maze.to_rows()) for c, ch in enumerate(line) if ch == "."]


def sq(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


# A 9 x 13 maze, centre (4, 6), which is wall. Nearest corridor: (4, 5), at 1.
# Straight-line furthest from (4, 5): (7, 11), squared distance 9 + 36 = 45, 15 steps away.
# Furthest along the corridors: (7, 1), 19 steps away but squared distance only 9 + 16 = 25.
TWO_MEASURES = (
    "#########",  # 0
    "#.......#",  # 1
    "#.#######",  # 2
    "#.......#",  # 3
    "#######.#",  # 4
    "#.......#",  # 5   player (4, 5)
    "#.#######",  # 6   centre (4, 6) is wall
    "#...#####",  # 7
    "###.#####",  # 8
    "###.#####",  # 9
    "###.#####",  # 10
    "###.....#",  # 11  ghost (7, 11)
    "#########",  # 12
)


# --- C1 -------------------------------------------------------------------

def test_c1_the_player_starts_on_the_corridor_square_nearest_the_centre_over_1000_mazes(generated):
    for seed, maze, state in generated:
        corridors = corridors_of(maze)
        nearest = min(sq(c, CENTRE) for c in corridors)
        assert sq(state.player, CENTRE) == nearest, seed
        assert state.player in corridors, seed


def test_c1_on_a_hand_built_maze_the_player_starts_at_the_nearest_square():
    assert new_game(Maze.from_rows(TWO_MEASURES)).player == (4, 5)


def test_c1_when_several_are_equally_near_the_same_maze_always_gives_the_same_one():
    # 19 x 29, centre (9, 14) is wall, and its four neighbours are corridor, all at distance 1.
    rows = ["#" * 19 for _ in range(29)]

    def open_(c, r):
        rows[r] = rows[r][:c] + "." + rows[r][c + 1:]

    for c, r in [(9, 13), (8, 14), (10, 14), (9, 15), (2, 2)]:
        open_(c, r)
    maze = Maze.from_rows(rows)
    starts = {new_game(maze).player for _ in range(20)}
    starts |= {new_game(Maze.from_rows(list(rows))).player for _ in range(20)}
    assert starts == {(9, 13)}


def test_c1_the_same_generated_maze_always_gives_the_same_start(generated):
    for seed, maze, state in generated[:100]:
        again = new_game(generate_maze(random.Random(seed)))
        assert (again.player, again.ghost) == (state.player, state.ghost), seed


# --- C2 -------------------------------------------------------------------

def test_c2_the_ghost_starts_furthest_by_straight_line_not_along_the_corridors():
    maze = Maze.from_rows(TWO_MEASURES)
    state = new_game(maze)
    # What each measure picks, worked out here from the rows:
    corridors = corridors_of(maze)
    steps = {state.player: 0}
    queue = deque([state.player])
    while queue:
        c, r = queue.popleft()
        for n in [(c, r - 1), (c, r + 1), (c + 1, r), (c - 1, r)]:
            if n in corridors and n not in steps:
                steps[n] = steps[(c, r)] + 1
                queue.append(n)
    by_corridor = max(steps, key=steps.get)
    by_straight_line = max(corridors, key=lambda s: sq(s, state.player))
    assert (by_straight_line, by_corridor) == ((7, 11), (7, 1)), "the maze no longer separates the measures"
    assert state.ghost == (7, 11)


def test_c2_over_1000_mazes_the_ghost_is_at_the_greatest_straight_line_distance(generated):
    for seed, maze, state in generated:
        furthest = max(sq(c, state.player) for c in corridors_of(maze))
        assert sq(state.ghost, state.player) == furthest, seed


# --- C3 -------------------------------------------------------------------

def test_c3_when_the_centre_is_corridor_the_player_starts_on_it():
    rows = ["#" * 19 for _ in range(29)]
    rows[14] = "#" + "." * 17 + "#"
    state = new_game(Maze.from_rows(rows))
    assert state.player == CENTRE


def test_c3_over_generated_mazes_whose_centre_is_corridor(generated):
    with_open_centre = [(seed, state) for seed, maze, state in generated if maze.is_corridor(CENTRE)]
    assert len(with_open_centre) >= 100, "fewer than 100 generated mazes had an open centre"
    for seed, state in with_open_centre:
        assert state.player == CENTRE, seed


# --- C4, C5 ----------------------------------------------------------------

def test_c4_every_corridor_square_but_the_players_holds_a_dot_and_no_wall_does(generated):
    for seed, maze, state in generated:
        assert state.dots == set(corridors_of(maze)) - {state.player}, seed


def test_c4_on_a_hand_built_maze():
    state = new_game(Maze.from_rows(["#####", "#...#", "#####"]))
    assert state.player == (2, 1)
    assert state.dots == {(1, 1), (3, 1)}


def test_c5_the_ghosts_start_square_holds_a_dot(generated):
    for seed, _, state in generated:
        assert state.ghost in state.dots, seed


# --- C6 -------------------------------------------------------------------

def test_c6_the_score_starts_at_zero_and_no_outcome_is_decided():
    state = new_game(Maze.from_rows(TWO_MEASURES))
    assert state.score == 0
    assert state.outcome is PLAYING
    assert state.outcome not in (LOST, WON)


# --- C7 -------------------------------------------------------------------

def test_c7_over_1000_mazes_player_and_ghost_start_apart_and_on_corridor(generated):
    for seed, maze, state in generated:
        assert state.player != state.ghost, seed
        assert maze.is_corridor(state.player) and maze.is_corridor(state.ghost), seed


# --- A claims ----------------------------------------------------------------

def test_a1_the_ghost_starts_with_no_heading():
    assert new_game(Maze.from_rows(TWO_MEASURES)).ghost_heading is None


def test_a1_setup_hands_back_the_maze_it_was_given():
    maze = Maze.from_rows(TWO_MEASURES)
    assert new_game(maze).maze is maze


@pytest.mark.parametrize("rows, count", [(["###", "###"], 0), (["###", "#.#", "###"], 1)])
def test_a2_a_maze_with_fewer_than_two_corridor_squares_is_refused(rows, count):
    with pytest.raises(ValueError, match=f"at least two corridor squares, this maze has {count}"):
        new_game(Maze.from_rows(rows))


def test_a2_ties_for_the_ghost_go_to_the_first_in_row_by_row_order():
    # Centre (2, 1) is corridor, so the player starts there; (1, 1) and (3, 1)
    # are equally far from it, and (1, 1) comes first.
    state = new_game(Maze.from_rows(["#####", "#...#", "#####"]))
    assert state.player == (2, 1)
    assert state.ghost == (1, 1)


def test_a3_setup_uses_no_randomness():
    """No random source is taken, and the global random state has no effect."""
    maze = Maze.from_rows(TWO_MEASURES)
    saved = random.getstate()
    try:
        random.seed(1)
        first = new_game(maze)
        random.seed(2)
        second = new_game(maze)
    finally:
        random.setstate(saved)
    assert first == second
