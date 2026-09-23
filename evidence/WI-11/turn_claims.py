"""WI-11 evidence harness: play the long runs and the ending scenarios, and print them.

Evidence, not a test: the suite never collects it. tests/test_turn_resolution.py
asserts the same things; this prints the counts and the before/after of each
ending scenario, so a reader can see what happened.

Run from the repository root:

    .venv/bin/python evidence/WI-11/turn_claims.py

Each line ends PASS or FAIL; the last line is ALL PASS or SOME FAIL, and the
exit status is 0 only for ALL PASS.
"""

from __future__ import annotations

import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from terminal_game.application.turn_resolution import move_player, step_ghost  # noqa: E402
from terminal_game.domain.game_setup import new_game  # noqa: E402
from terminal_game.domain.game_state import LOST, PLAYING, WON, GameState  # noqa: E402
from terminal_game.domain.maze import DIRECTIONS, Maze  # noqa: E402
from terminal_game.domain.maze_generator import generate_maze  # noqa: E402

E, W = (1, 0), (-1, 0)
CORRIDOR = Maze.from_rows(["#########", "#.......#", "#########"])


class NoDraws:
    def choice(self, seq):
        raise AssertionError("unexpected draw")


def st(player, ghost, dots, score=0, heading=None):
    return GameState(CORRIDOR, player, ghost, frozenset(dots), score, PLAYING, heading)


def show(s):
    return f"player {s.player} ghost {s.ghost} dots {sorted(s.dots)} score {s.score} outcome {s.outcome!r}"


def long_runs():
    drops = eaten = ghost_steps = 0
    lost = won = 0
    off = wall = jumps = moved = 0
    for seed in range(1000):
        maze = generate_maze(random.Random(seed))
        # C5: random moves and ghost steps
        g = new_game(maze)
        mv, gr = random.Random(10_000 + seed), random.Random(20_000 + seed)
        for _ in range(1000):
            for turn in ("move", "ghost"):
                before = g
                g = move_player(g, mv.choice(DIRECTIONS)) if turn == "move" else step_ghost(g, gr)
                drops += g.score < before.score
                eaten += g.score - before.score
                ghost_steps += turn == "ghost" and g.ghost != before.ghost
        lost += g.outcome == LOST
        won += g.outcome == WON
        # C11: random player moves only
        g = new_game(maze)
        mv = random.Random(10_000 + seed)
        for _ in range(1000):
            before = g
            g = move_player(g, mv.choice(DIRECTIONS))
            p = g.player
            off += not (0 <= p[0] < 19 and 0 <= p[1] < 29)
            wall += not maze.is_corridor(p)
            d = (p[0] - before.player[0], p[1] - before.player[1])
            jumps += d != (0, 0) and d not in DIRECTIONS
            moved += d != (0, 0)
    return [
        ("C5", f"1000 games x 1000 (move + ghost step): score decreases {drops}; dots eaten {eaten}; ghost moves {ghost_steps}; games lost {lost}, won {won}", drops == 0 and eaten > 0),
        ("C11", f"1000 games x 1000 random moves: squares changed {moved}; off the grid {off}; on a wall {wall}; jumps of more than one square {jumps}", off == wall == jumps == 0 and moved > 0),
    ]


def scenarios():
    out = []
    lines = []

    def case(code, label, before, after, ok):
        lines.append(f"  {code} {label}\n      before: {show(before)}\n      after:  {show(after)}")
        out.append((code, label, ok))

    b = st((2, 1), (7, 1), {(3, 1)}, 9); a = move_player(b, E)
    case("C8", "eat the last dot", b, a, a.outcome == WON and a.score == 10 and not a.dots)
    b = st((2, 1), (3, 1), {(3, 1)}, 41); a = move_player(b, E)
    case("C9", "walk onto the ghost, which stands on the last dot", b, a, a.outcome == LOST and a.dots == {(3, 1)} and a.score == 41)
    b = st((3, 1), (4, 1), {(5, 1)}, heading=W); a = move_player(b, E)
    case("C10", "adjacent, player moves towards the ghost", b, a, a.outcome == LOST and a.player == a.ghost == (4, 1))
    b = st((3, 1), (4, 1), {(5, 1)}, heading=W); a = step_ghost(b, NoDraws())
    case("C10", "adjacent, ghost steps towards the player", b, a, a.outcome == LOST and a.player == a.ghost == (3, 1))
    b = st((3, 1), (7, 1), {(4, 1)}, 3); a = move_player(b, (0, -1))
    case("C2", "move north into the wall", b, a, a == b)
    return out, lines


def main() -> int:
    results = long_runs()
    sc, lines = scenarios()
    print("WI-11 turn resolution")
    for code, text, ok in results:
        print(f"  {code}  {text}  {'PASS' if ok else 'FAIL'}")
    print("\nscenarios on the corridor #.......# (row 1, columns 1-7):")
    for line, (code, label, ok) in zip(lines, sc):
        print(line + f"\n      {'PASS' if ok else 'FAIL'}")
    all_ok = all(r[2] for r in results) and all(ok for _, _, ok in sc)
    print("\nALL PASS" if all_ok else "\nSOME FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
