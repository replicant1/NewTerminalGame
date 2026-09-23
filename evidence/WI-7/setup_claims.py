"""WI-7 evidence harness: measure the setup claims and print the numbers.

Evidence, not a test: the suite never collects it. tests/test_game_setup.py
asserts the same things; this prints what was counted, and draws the
hand-built maze on which the two distance measures disagree (C2).

Run from the repository root:

    .venv/bin/python evidence/WI-7/setup_claims.py          # seeds 0..999
    .venv/bin/python evidence/WI-7/setup_claims.py 10000

Each line ends PASS or FAIL; the last line is ALL PASS or SOME FAIL, and the
exit status is 0 only for ALL PASS. Nearest, furthest and step counts are
worked out here from the maze's rows, not taken from the code under test.
"""

from __future__ import annotations

import pathlib
import random
import sys
from collections import deque

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from terminal_game.domain.game_setup import new_game  # noqa: E402
from terminal_game.domain.game_state import PLAYING  # noqa: E402
from terminal_game.domain.maze import Maze  # noqa: E402
from terminal_game.domain.maze_generator import generate_maze  # noqa: E402

CENTRE = (9, 14)
TWO_MEASURES = (
    "#########", "#.......#", "#.#######", "#.......#", "#######.#", "#.......#", "#.#######",
    "#...#####", "###.#####", "###.#####", "###.#####", "###.....#", "#########",
)


def sq(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def corridors_of(maze):
    return [(c, r) for r, line in enumerate(maze.to_rows()) for c, ch in enumerate(line) if ch == "."]


def steps_from(maze, start):
    corr = set(corridors_of(maze))
    steps = {start: 0}
    q = deque([start])
    while q:
        c, r = q.popleft()
        for n in ((c, r - 1), (c, r + 1), (c + 1, r), (c - 1, r)):
            if n in corr and n not in steps:
                steps[n] = steps[(c, r)] + 1
                q.append(n)
    return steps


def main(n: int) -> int:
    not_nearest = not_furthest = open_centre = open_centre_missed = 0
    dots_wrong = ghost_dotless = together = on_wall = not_fresh = unrepeatable = 0
    for seed in range(n):
        maze = generate_maze(random.Random(seed))
        s = new_game(maze)
        corr = corridors_of(maze)
        not_nearest += sq(s.player, CENTRE) != min(sq(c, CENTRE) for c in corr)
        not_furthest += sq(s.ghost, s.player) != max(sq(c, s.player) for c in corr)
        if CENTRE in corr:
            open_centre += 1
            open_centre_missed += s.player != CENTRE
        dots_wrong += s.dots != set(corr) - {s.player}
        ghost_dotless += s.ghost not in s.dots
        together += s.player == s.ghost
        on_wall += maze.is_wall(s.player) or maze.is_wall(s.ghost)
        not_fresh += (s.score, s.outcome, s.ghost_heading) != (0, PLAYING, None)
        unrepeatable += new_game(maze) != s

    hand = Maze.from_rows(TWO_MEASURES)
    hs = new_game(hand)
    steps = steps_from(hand, hs.player)
    by_steps = max(steps, key=steps.get)
    by_line = max(corridors_of(hand), key=lambda c: sq(c, hs.player))

    results = [
        ("C1", f"players not on a nearest-to-centre square: {not_nearest}/{n}; same maze, different start: {unrepeatable}", not_nearest == 0 and unrepeatable == 0),
        ("C2", f"ghosts not at the greatest straight-line distance: {not_furthest}/{n}; hand-built maze: straight-line picks {by_line} ({steps[by_line]} steps), corridors pick {by_steps} ({steps[by_steps]} steps), ghost at {hs.ghost}", not_furthest == 0 and hs.ghost == by_line != by_steps),
        ("C3", f"mazes with an open centre: {open_centre}; player not on it: {open_centre_missed}", open_centre > 0 and open_centre_missed == 0),
        ("C4", f"mazes whose dots are not exactly the corridor squares minus the player's: {dots_wrong}/{n}", dots_wrong == 0),
        ("C5", f"ghost start squares without a dot: {ghost_dotless}/{n}", ghost_dotless == 0),
        ("C6", f"starts not at score 0, undecided, no ghost heading: {not_fresh}/{n}", not_fresh == 0),
        ("C7", f"player and ghost on the same square: {together}/{n}; either on a wall: {on_wall}/{n}", together == 0 and on_wall == 0),
    ]
    print(f"WI-7 setup claims over seeds 0..{n - 1} ({n} mazes)")
    for code, text, ok in results:
        print(f"  {code}  {text}  {'PASS' if ok else 'FAIL'}")
    print("\nhand-built maze for C2 (P player, G ghost, x furthest along the corridors, + centre):")
    for r, line in enumerate(TWO_MEASURES):
        cells = []
        for c, ch in enumerate(line):
            cells.append("P" if (c, r) == hs.player else "G" if (c, r) == hs.ghost else "x" if (c, r) == by_steps
                         else "+" if (c, r) == (hand.width // 2, hand.height // 2) else ch)
        print("  " + "".join(cells))
    ok = all(r[2] for r in results)
    print("\nALL PASS" if ok else "\nSOME FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000))
