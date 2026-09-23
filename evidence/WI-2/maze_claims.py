"""WI-2 evidence harness: measure every maze claim over many seeds and print the numbers.

Evidence, not a test: the suite never collects it. The suite's own tests
(tests/test_maze_generator.py) assert the same properties; this prints what was
counted, so a reader can see the checks were not vacuous.

Run from the repository root:

    .venv/bin/python evidence/WI-2/maze_claims.py            # seeds 0..999
    .venv/bin/python evidence/WI-2/maze_claims.py 10000      # seeds 0..9999

Every line ends in PASS or FAIL; the last line is ALL PASS or SOME FAIL, and the
exit status is 0 only for ALL PASS. It reads each maze only through to_rows(),
and works out neighbours, rings and blocks for itself.
"""

from __future__ import annotations

import pathlib
import random
import sys
import time
from collections import deque

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from terminal_game.domain.maze_generator import generate_maze  # noqa: E402

W, H = 19, 29


def nsew(c, r):
    return ((c, r - 1), (c, r + 1), (c + 1, r), (c - 1, r))


def main(n: int) -> int:
    ring = {(c, 0) for c in range(W)} | {(c, H - 1) for c in range(W)} | {(0, r) for r in range(H)} | {(W - 1, r) for r in range(H)}
    sized = bad_chars = 0
    ring_checked = ring_open = 0
    corridor_total = min_corridors = None
    min_nbrs = 4
    dead = 0
    connected = 0
    blocks_checked = blocks_open = 0
    reproduced = 0
    distinct = set()
    times = []
    bare_lines = 0

    for seed in range(n):
        t0 = time.perf_counter()
        maze = generate_maze(random.Random(seed))
        times.append(time.perf_counter() - t0)
        rows = maze.to_rows()

        # C1
        if len(rows) == H and all(len(line) == W for line in rows) and (maze.width, maze.height) == (W, H):
            sized += 1
        bad_chars += sum(ch not in "#." for line in rows for ch in line)

        corr = {(c, r) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch == "."}
        corridor_total = (corridor_total or 0) + len(corr)
        min_corridors = len(corr) if min_corridors is None else min(min_corridors, len(corr))

        # C2
        ring_checked += len(ring)
        ring_open += len(ring & corr)

        # C3
        for c, r in corr:
            k = sum(nb in corr for nb in nsew(c, r))
            min_nbrs = min(min_nbrs, k)
            dead += k < 2

        # C4
        start = min(corr)
        seen = {start}
        q = deque([start])
        while q:
            for nb in nsew(*q.popleft()):
                if nb in corr and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        connected += seen == corr

        # C5
        for r in range(H - 1):
            for c in range(W - 1):
                blocks_checked += 1
                blocks_open += {(c, r), (c + 1, r), (c, r + 1), (c + 1, r + 1)} <= corr

        # C6
        reproduced += generate_maze(random.Random(seed)) == maze
        distinct.add(rows)

        # A1
        bare_lines += sum(not any((c, r) in corr for c in range(W)) for r in range(1, H - 1))
        bare_lines += sum(not any((c, r) in corr for r in range(H)) for c in range(1, W - 1))

    results = [
        ("C1", f"{sized}/{n} mazes are 19 x 29; squares that are neither '#' nor '.': {bad_chars}", sized == n and bad_chars == 0),
        ("C2", f"outer-ring squares checked: {ring_checked}; corridor among them: {ring_open}", ring_open == 0 and ring_checked == n * len(ring)),
        ("C3", f"corridor squares checked: {corridor_total}; fewest corridor neighbours of any: {min_nbrs}; with fewer than 2: {dead}", dead == 0 and corridor_total > 0),
        ("C4", f"mazes whose every corridor square is reached from one: {connected}/{n}", connected == n),
        ("C5", f"2 x 2 blocks checked: {blocks_checked}; all-corridor: {blocks_open}", blocks_open == 0 and blocks_checked > 0),
        ("C6", f"seeds reproducing the same maze: {reproduced}/{n}; distinct mazes: {len(distinct)} of {n}", reproduced == n and len(distinct) == n),
        ("C7", f"slowest generation: {max(times) * 1000:.2f} ms (limit 1000 ms); mean {sum(times) / n * 1000:.2f} ms", max(times) < 1.0),
        ("A1", f"interior rows/columns with no corridor: {bare_lines}; fewest corridor squares in a maze: {min_corridors}", bare_lines == 0),
    ]
    print(f"WI-2 maze claims over seeds 0..{n - 1} ({n} mazes)")
    for code, text, ok in results:
        print(f"  {code}  {text}  {'PASS' if ok else 'FAIL'}")
    all_ok = all(ok for _, _, ok in results)
    print("\nseed 0, '#' wall '.' corridor:")
    print("\n".join("  " + line for line in generate_maze(random.Random(0)).to_rows()))
    print("\nALL PASS" if all_ok else "\nSOME FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000))
