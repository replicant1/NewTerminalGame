"""WI-10: the composed frame, printed so you can read it against the specimen.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-10/compose_probe.py

1. It turns the specimen picture in docs/FUNCTIONAL_REQUIREMENTS.md section 3
   back into a state. Walls come from the plan's twelve wall characters, dots
   from the ``▪`` squares, and the player and ghost from their sprites. It
   composes that state and prints the frame's characters beside a map of each
   cell's colour role (W wall, d dot, P player, G ghost, s status, . background).
   It then compares every character of all 30 rows with the specimen, padded to
   40 cells.
2. It composes three small situations on a generated maze and prints the cells
   around the player and ghost: the two on one square (C6), the ghost on a dot
   and then moved off it (C7), and the two side by side (C8).

Each part ends with a verdict line.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import specimen  # noqa: E402
from terminal_game.domain.maze import Maze  # noqa: E402
from terminal_game.domain.maze_generator import generate_maze  # noqa: E402
from terminal_game.presentation.frame_composer import compose  # noqa: E402

WALL_CHARACTERS = set("■═║╔╗╚╝╠╣╦╩╬")
ROLE_LETTER = {"wall": "W", "dot": "d", "player": "P", "ghost": "G", "status": "s", "background": "."}


@dataclass(frozen=True)
class State:
    maze: Maze
    player: tuple
    ghost: tuple
    dots: frozenset
    score: int = 0
    outcome: Optional[str] = None


def specimen_state():
    walls, dots, player, ghost = [], set(), None, None
    for r, line in enumerate(specimen.maze_rows()):
        row = []
        for c in range(specimen.MAZE_WIDTH):
            ch = line[2 * c]
            row.append("#" if ch in WALL_CHARACTERS else ".")
            if ch == "▪":
                dots.add((c, r))
            elif ch == "█":
                sprite = line[2 * c - 1:2 * c + 2]
                player = (c, r) if sprite == "▐█▌" else player
                ghost = (c, r) if sprite == "▗█▖" else ghost
        walls.append("".join(row))
    return State(Maze.from_rows(walls), player, ghost, frozenset(dots))


def around(frame, square):
    col, row = square
    cells = frame[row][max(0, 2 * col - 3):2 * col + 4]
    return "".join(c for c, _ in cells) + "   " + "".join(ROLE_LETTER[r] for _, r in cells)


def main() -> int:
    state = specimen_state()
    frame = compose(state)
    want = [row.ljust(40) for row in specimen.rows()]
    print("1. The specimen's state (player %s, ghost %s, %d dots, score 0), composed:"
          % (state.player, state.ghost, len(state.dots)))
    mismatched_rows = 0
    for r, line in enumerate(frame):
        text = "".join(c for c, _ in line)
        role_map = "".join(ROLE_LETTER[role] for _, role in line)
        mark = "  " if text == want[r] else "!="
        mismatched_rows += text != want[r]
        print("   %2d |%s| %s |%s|" % (r, text, mark, role_map))
    cells_differ = sum(a != b for g, w in zip(frame, want) for a, b in zip("".join(c for c, _ in g), w))
    c1 = mismatched_rows == 0 and len(frame) == 30
    print("WI-10/C1 %s: %d of 30 rows differ from the specimen, %d cells in all"
          % ("HOLDS" if c1 else "DOES NOT HOLD", mismatched_rows, cells_differ))
    print()

    maze = generate_maze(random.Random(7))
    corridors = maze.corridor_squares()
    print("2. Situations on generated maze 7 (characters, then roles, around the square):")
    same = corridors[40]
    f6 = compose(State(maze, same, same, frozenset()))
    print("   C6 both on %s:           %s" % (same, around(f6, same)))
    c6 = around(f6, same).split()[0].strip().find("▗█▖") >= 0 and not any(
        r == "player" for line in f6 for _, r in line)
    under, off = corridors[30], corridors[60]
    f7a = compose(State(maze, corridors[0], under, frozenset({under})))
    f7b = compose(State(maze, corridors[0], off, frozenset({under})))
    print("   C7 ghost on the dot at %s: %s" % (under, around(f7a, under)))
    print("   C7 ghost moved off:        %s" % around(f7b, under))
    c7 = f7a[under[1]][2 * under[0]] == ("█", "ghost") and f7b[under[1]][2 * under[0]] == ("▪", "dot")
    left = next(sq for sq in corridors if maze.is_corridor((sq[0] + 1, sq[1])))
    right = (left[0] + 1, left[1])
    f8 = compose(State(maze, left, right, frozenset()))
    print("   C8 player %s, ghost %s: %s" % (left, right, around(f8, left)))
    c8 = f8[left[1]][2 * left[0]] == ("█", "player") and f8[right[1]][2 * right[0]] == ("█", "ghost")
    print("WI-10/C6 %s; WI-10/C7 %s; WI-10/C8 %s" % tuple("HOLDS" if ok else "DOES NOT HOLD" for ok in (c6, c7, c8)))
    return 0 if (c1 and c6 and c7 and c8) else 1


if __name__ == "__main__":
    sys.exit(main())
