"""WI-8: the ghost's movement policy (GHOST-2, GHOST-3, GHOST-4, SCORE-4)."""

from __future__ import annotations

import inspect
import random

import pytest

from terminal_game.domain.ghost import GhostMove, GhostStuck, ghost_step
from terminal_game.domain.maze import DIRECTIONS, Maze
from terminal_game.domain.maze_generator import generate_maze

NORTH, SOUTH, EAST, WEST = (0, -1), (0, 1), (1, 0), (-1, 0)

CROSSROADS = Maze.from_rows([
    "#####",
    "##.##",
    "#...#",
    "##.##",
    "#####",
])

# A T-junction at (2, 1): ahead of a ghost heading north is wall; west and east are open.
T_JUNCTION = Maze.from_rows([
    "#####",
    "#...#",
    "##.##",
    "##.##",
    "#####",
])

# An L-bend at (3, 1): the only way on, other than back, is south.
L_BEND = Maze.from_rows([
    "#####",
    "#...#",
    "###.#",
    "#####",
])

DEAD_END = Maze.from_rows([
    "######",
    "#....#",
    "######",
])

LONG_CORRIDOR = Maze.from_rows([
    "#########",
    "#.......#",
    "#########",
])


def _seeds(n=200):
    return [random.Random(seed) for seed in range(n)]


# --------------------------------------------------------------------------
# WI-8/C1: straight on while the square ahead is corridor, junctions included
# --------------------------------------------------------------------------


def test_c1_along_a_corridor_the_ghost_keeps_its_heading():
    for rng in _seeds():
        ghost = GhostMove((2, 1), EAST)
        for expected_col in range(3, 8):
            ghost = ghost_step(LONG_CORRIDOR, ghost.square, ghost.heading, rng)
            assert ghost == GhostMove((expected_col, 1), EAST)


@pytest.mark.parametrize("heading, ahead", [
    (NORTH, (2, 1)), (SOUTH, (2, 3)), (EAST, (3, 2)), (WEST, (1, 2)),
])
def test_c1_at_a_junction_the_ghost_goes_straight_through(heading, ahead):
    for rng in _seeds():
        assert ghost_step(CROSSROADS, (2, 2), heading, rng) == GhostMove(ahead, heading)


# --------------------------------------------------------------------------
# WI-8/C2: ahead is wall -> another open neighbour, not the way back, at random
# --------------------------------------------------------------------------


def test_c2_blocked_ahead_it_picks_one_of_the_other_exits_each_at_least_40_percent():
    rng = random.Random(8)
    counts = {(1, 1): 0, (3, 1): 0}
    for _ in range(10_000):
        nxt = ghost_step(T_JUNCTION, (2, 1), NORTH, rng)
        assert nxt.square in counts, "never back the way it came, never onto the wall ahead"
        counts[nxt.square] += 1
    assert min(counts.values()) >= 4_000, counts


def test_c2_the_new_heading_is_the_direction_it_turned():
    for rng in _seeds():
        nxt = ghost_step(T_JUNCTION, (2, 1), NORTH, rng)
        assert nxt.heading == (WEST if nxt.square == (1, 1) else EAST)


def test_c2_at_a_bend_it_takes_the_only_other_way_and_does_not_turn_back():
    for rng in _seeds():
        assert ghost_step(L_BEND, (3, 1), EAST, rng) == GhostMove((3, 2), SOUTH)


# --------------------------------------------------------------------------
# WI-8/C3: back the way it came only when nothing else is open
# --------------------------------------------------------------------------


def test_c3_at_a_dead_end_the_ghost_turns_back():
    for rng in _seeds():
        assert ghost_step(DEAD_END, (4, 1), EAST, rng) == GhostMove((3, 1), WEST)
        assert ghost_step(DEAD_END, (1, 1), WEST, rng) == GhostMove((2, 1), EAST)


def test_c3_driven_into_a_dead_end_it_bounces_and_walks_back_out():
    rng = random.Random(3)
    ghost = GhostMove((1, 1), EAST)
    path = []
    for _ in range(6):
        ghost = ghost_step(DEAD_END, ghost.square, ghost.heading, rng)
        path.append(ghost.square)
    assert path == [(2, 1), (3, 1), (4, 1), (3, 1), (2, 1), (1, 1)]


# --------------------------------------------------------------------------
# WI-8/C4: nothing about the player
# --------------------------------------------------------------------------


def test_c4_the_policy_is_handed_the_maze_the_ghost_and_a_random_source_only():
    assert list(inspect.signature(ghost_step).parameters) == ["maze", "square", "heading", "rng"]


def test_c4_the_ghosts_path_is_the_same_wherever_the_player_walks():
    """Two games on one maze with one random sequence, and players that walk
    different routes: the ghost's path is identical, square for square."""
    maze = generate_maze(random.Random(4))
    corridors = maze.corridor_squares()

    def run(player_route_seed):
        ghost_rng, player_rng = random.Random(99), random.Random(player_route_seed)
        ghost, player, path = GhostMove(corridors[-1], None), corridors[0], []
        for _ in range(500):
            player = player_rng.choice(maze.open_neighbours(player))
            ghost = ghost_step(maze, ghost.square, ghost.heading, ghost_rng)
            path.append(ghost.square)
        return path, player

    (path_a, end_a), (path_b, end_b) = run(1), run(2)
    assert end_a != end_b, "the two players did take different routes"
    assert path_a == path_b


# --------------------------------------------------------------------------
# WI-8/C5 and C8: one square N/S/E/W onto corridor, every move, never stuck
# --------------------------------------------------------------------------


def test_c5_c8_over_1000_mazes_and_1000_moves_each_the_ghost_always_moves_one_open_square():
    for seed in range(1000):
        maze = generate_maze(random.Random(seed))
        rng = random.Random(1_000_000 + seed)
        ghost = GhostMove(maze.corridor_squares()[seed % len(maze.corridors)], None)
        for move in range(1000):
            nxt = ghost_step(maze, ghost.square, ghost.heading, rng)
            step = (nxt.square[0] - ghost.square[0], nxt.square[1] - ghost.square[1])
            assert step in DIRECTIONS, (seed, move, ghost, nxt)
            assert maze.is_corridor(nxt.square), (seed, move, nxt)
            assert nxt.heading == step
            ghost = nxt


def test_a_ghost_with_no_open_neighbour_is_refused_loudly():
    walled_in = Maze.from_rows(["###", "#.#", "###"])
    with pytest.raises(GhostStuck, match=r"\(1, 1\) has no open neighbour"):
        ghost_step(walled_in, (1, 1), None, random.Random(0))


def test_a_heading_that_is_not_a_single_step_is_refused():
    with pytest.raises(ValueError, match="a heading is one of"):
        ghost_step(CROSSROADS, (2, 2), (1, 1), random.Random(0))


# --------------------------------------------------------------------------
# WI-8/C6: the first move, with no heading yet
# --------------------------------------------------------------------------


def test_c6_with_no_heading_the_first_move_is_to_an_open_neighbour_any_of_them():
    seen = set()
    for rng in _seeds(400):
        nxt = ghost_step(CROSSROADS, (2, 2), None, rng)
        assert nxt.square in CROSSROADS.open_neighbours((2, 2))
        seen.add(nxt.square)
    assert seen == {(2, 1), (2, 3), (3, 2), (1, 2)}


def test_c6_after_its_first_move_the_ghost_has_the_heading_it_moved_in():
    for rng in _seeds():
        nxt = ghost_step(CROSSROADS, (2, 2), None, rng)
        assert nxt.heading == (nxt.square[0] - 2, nxt.square[1] - 2)


# --------------------------------------------------------------------------
# WI-8/C7: a ghost move never changes the dots
# --------------------------------------------------------------------------


def test_c7_the_policy_takes_no_dots_and_returns_only_the_ghost():
    assert "dots" not in inspect.signature(ghost_step).parameters
    result = ghost_step(CROSSROADS, (2, 2), None, random.Random(0))
    assert type(result) is GhostMove
    assert result._fields == ("square", "heading")


def test_c7_every_dot_is_still_there_after_the_ghost_has_walked_over_them():
    maze = generate_maze(random.Random(7))
    start = maze.corridor_squares()[0]
    dots = frozenset(sq for sq in maze.corridors if sq != start)
    before = set(dots)
    ghost, rng, landed_on_dots = GhostMove(start, None), random.Random(70), 0
    for _ in range(2000):
        ghost = ghost_step(maze, ghost.square, ghost.heading, rng)
        landed_on_dots += ghost.square in dots
    assert landed_on_dots > 1000, "the ghost did walk onto dotted squares"
    assert dots == before
