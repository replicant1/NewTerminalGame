"""WI-4/C4: the wall glyphs redraw the specimen's walls.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-4/specimen_glyphs.py

It reads the specimen picture from docs/FUNCTIONAL_REQUIREMENTS.md section 3 and
decides which grid squares are wall: those whose cell 2n holds a wall character.
It then **redraws the walls only**, from nothing but that wall/corridor grid,
using ``square_glyph`` and ``joining_cell``, with the corridors left blank. It
prints the redrawn maze and compares every wall square and every joining cell
with the specimen. Only the joining cells that the player's and ghost's sprites
cover are left out, and the harness checks that those are blank underneath.

On success the last line reads ``WI-4/C4 HOLDS`` with 0 mismatches.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import specimen  # noqa: E402
from terminal_game.presentation.wall_glyphs import (WALL_CHARACTERS, joining_cell,  # noqa: E402
                                                    square_glyph)

SPRITE_PARTS = set("▐█▌▗▖")


def main() -> int:
    maze = specimen.maze_rows()
    w, h = specimen.MAZE_WIDTH, specimen.MAZE_HEIGHT
    walls = [[maze[r][2 * c] in WALL_CHARACTERS for c in range(w)] for r in range(h)]

    def is_wall(c, r):
        return walls[r][c]

    squares = joins = covered = 0
    mismatches = []
    redrawn = []
    for r in range(h):
        cells = []
        for c in range(w):
            if is_wall(c, r):
                squares += 1
                got = square_glyph(is_wall, w, h, c, r)
                if got != maze[r][2 * c]:
                    mismatches.append("square (%d,%d): specimen %r, drawn %r" % (c, r, maze[r][2 * c], got))
            else:
                got = " "
            cells.append(got)
            if c < w - 1:
                join = joining_cell(is_wall, w, h, c, r)
                shown = maze[r][2 * c + 1]
                if shown in SPRITE_PARTS:
                    covered += 1
                    if join != " ":
                        mismatches.append("joining cell under a sprite at (%d,%d) is %r" % (c, r, join))
                else:
                    joins += 1
                    if join != shown:
                        mismatches.append("join east of (%d,%d): specimen %r, drawn %r" % (c, r, shown, join))
                cells.append(join)
        redrawn.append("".join(cells))

    print("Walls redrawn from the wall/corridor grid alone (corridors blank):")
    for line in redrawn:
        print("    " + line)
    print()
    for m in mismatches:
        print("MISMATCH " + m)
    print("WI-4/C4 %s: %d wall squares and %d joining cells compared with the specimen, "
          "%d mismatches; %d joining cells under sprites, all blank underneath"
          % ("HOLDS" if not mismatches else "DOES NOT HOLD", squares, joins, len(mismatches), covered))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
