"""WI-2: the maze generator's structural claims, over 1,000 seeds (plan §4, WI-2/C1-C7).

Every check here reads the maze through ``to_rows()`` and nothing else, and
works out neighbours, rings and 2 x 2 blocks for itself, so the invariants are
not checked by the same query methods they would be relying on. Those methods
have their own tests in ``test_maze.py``.

The 1,000 mazes are generated once per module, timed as they are generated.
"""

from __future__ import annotations

import ast
import pathlib
import random
import time
from collections import deque

import pytest

from terminal_game.domain.maze import Maze
from terminal_game.domain.maze_generator import ensure_connected, generate_maze

SEEDS = range(1000)
WIDTH, HEIGHT = 19, 29


@pytest.fixture(scope="module")
def generated():
    """``(seed, maze, rows, seconds)`` for each of the 1,000 seeds."""
    out = []
    for seed in SEEDS:
        rng = random.Random(seed)
        started = time.perf_counter()
        maze = generate_maze(rng)
        seconds = time.perf_counter() - started
        out.append((seed, maze, maze.to_rows(), seconds))
    return out


def corridor_set(rows):
    return {(c, r) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch == "."}


def nsew(square):
    c, r = square
    return [(c, r - 1), (c, r + 1), (c + 1, r), (c - 1, r)]


def test_c1_every_maze_is_19_by_29_and_every_square_is_wall_or_corridor(generated):
    for seed, maze, rows, _ in generated:
        assert (maze.width, maze.height) == (WIDTH, HEIGHT), seed
        assert len(rows) == HEIGHT, seed
        for r, line in enumerate(rows):
            assert len(line) == WIDTH, (seed, r)
            assert set(line) <= {"#", "."}, (seed, r, line)
        for r in range(HEIGHT):
            for c in range(WIDTH):
                # exactly one of the two, never both, never neither
                assert maze.is_wall((c, r)) != maze.is_corridor((c, r)), (seed, c, r)


def test_c2_the_outer_ring_is_wall_in_every_maze(generated):
    ring = (
        [(c, 0) for c in range(WIDTH)]
        + [(c, HEIGHT - 1) for c in range(WIDTH)]
        + [(0, r) for r in range(HEIGHT)]
        + [(WIDTH - 1, r) for r in range(HEIGHT)]
    )
    for seed, _, rows, _ in generated:
        opened = [(c, r) for c, r in ring if rows[r][c] != "#"]
        assert opened == [], f"seed {seed}: corridor on the outer ring at {opened}"


def test_c3_no_corridor_square_has_fewer_than_two_corridor_neighbours(generated):
    for seed, _, rows, _ in generated:
        corridors = corridor_set(rows)
        dead_ends = [sq for sq in corridors if sum(n in corridors for n in nsew(sq)) < 2]
        assert dead_ends == [], f"seed {seed}: dead ends at {sorted(dead_ends)}"


def test_c4_every_corridor_square_reaches_every_other(generated):
    for seed, _, rows, _ in generated:
        corridors = corridor_set(rows)
        start = min(corridors)
        seen = {start}
        queue = deque([start])
        while queue:
            for n in nsew(queue.popleft()):
                if n in corridors and n not in seen:
                    seen.add(n)
                    queue.append(n)
        unreached = corridors - seen
        assert unreached == set(), f"seed {seed}: unreachable from {start}: {sorted(unreached)}"


def test_c5_no_two_by_two_block_is_all_corridor(generated):
    for seed, _, rows, _ in generated:
        blocks = [
            (c, r)
            for r in range(HEIGHT - 1)
            for c in range(WIDTH - 1)
            if rows[r][c] == rows[r][c + 1] == rows[r + 1][c] == rows[r + 1][c + 1] == "."
        ]
        assert blocks == [], f"seed {seed}: 2 x 2 corridor blocks with top-left at {blocks}"


def test_c6_the_same_seed_gives_the_same_maze(generated):
    for seed, maze, rows, _ in generated:
        again = generate_maze(random.Random(seed))
        assert again == maze, seed
        assert again.to_rows() == rows, seed


def test_c6_a_thousand_distinct_seeds_give_a_thousand_distinct_mazes(generated):
    distinct = {rows for _, _, rows, _ in generated}
    assert len(distinct) == len(SEEDS) == 1000


def test_c7_no_maze_takes_as_long_as_a_second(generated):
    slowest_seconds, slowest_seed = max((seconds, seed) for seed, _, _, seconds in generated)
    assert slowest_seconds < 1.0, f"seed {slowest_seed} took {slowest_seconds:.3f}s"


def test_a1_every_row_and_column_inside_the_ring_has_corridor(generated):
    """Guards C2-C5 against passing vacuously on an empty or partial maze."""
    for seed, _, rows, _ in generated:
        corridors = corridor_set(rows)
        bare_rows = [r for r in range(1, HEIGHT - 1) if not any((c, r) in corridors for c in range(WIDTH))]
        bare_cols = [c for c in range(1, WIDTH - 1) if not any((c, r) in corridors for r in range(HEIGHT))]
        assert (bare_rows, bare_cols) == ([], []), f"seed {seed}: no corridor in rows {bare_rows}, cols {bare_cols}"


def test_a2_the_global_random_state_has_no_effect():
    """The generator draws only on the source it is handed (plan §1.4)."""
    saved = random.getstate()
    try:
        random.seed(1)
        first = generate_maze(random.Random(42))
        random.seed(2)
        second = generate_maze(random.Random(42))
    finally:
        random.setstate(saved)
    assert first == second


def test_a2_the_maze_modules_import_no_clock_and_no_random_module():
    """No clock, and no randomness the domain was not handed (plan §1.4): the two
    modules import only ``__future__``, ``dataclasses``, ``typing`` and each other."""
    allowed = {"__future__", "dataclasses", "typing", "terminal_game.domain.maze"}
    package = pathlib.Path(__file__).resolve().parents[1] / "terminal_game" / "domain"
    found = {}
    for name in ("maze.py", "maze_generator.py"):
        tree = ast.parse((package / name).read_text())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module)
        found[name] = imported
    assert found["maze.py"] and found["maze_generator.py"], "scanned nothing"
    assert {name: sorted(mods - allowed) for name, mods in found.items()} == {
        "maze.py": [],
        "maze_generator.py": [],
    }


def test_a4_the_connectivity_check_refuses_a_maze_in_two_pockets():
    two_pockets = Maze.from_rows(
        [
            "#######",
            "#..#..#",
            "#..#..#",
            "#######",
        ]
    )
    with pytest.raises(ValueError, match=r"unreachable from \(1, 1\): \[\(4, 1\), \(5, 1\), \(4, 2\), \(5, 2\)\]"):
        ensure_connected(two_pockets)


def test_a4_the_connectivity_check_hands_back_a_connected_maze_unchanged():
    loop = Maze.from_rows(["#####", "#...#", "#.#.#", "#...#", "#####"])
    assert ensure_connected(loop) is loop
    no_corridor = Maze.from_rows(["###"])
    assert ensure_connected(no_corridor) is no_corridor

