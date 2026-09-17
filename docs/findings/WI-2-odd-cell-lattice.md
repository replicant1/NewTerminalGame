# The specimen maze sits on an odd-coordinate cell lattice

**Measured by developer B on 17 Sep 2026 at 01:50Z**, from
`docs/FUNCTIONAL_REQUIREMENTS.md` in the worktree at `main` = `ddc250e`.
Recorded here rather than in WI-2's PR summary because two later items depend
on it and the PR summary will not be read again.

## What was measured

Ruling C-2 fixes the mapping: maze column `c` is screen column `2c`, with all
29 maze rows exactly 37 columns wide. Decoding all 29 rows of the specimen
picture on that basis and classifying each of the 19 × 29 squares as corridor
or wall gives:

> **Zero corridor squares have both coordinates even.** Not few — none, across
> all 551 squares.

Reproduce it with:

```sh
.venv/bin/python - <<'PY'
text = open('docs/FUNCTIONAL_REQUIREMENTS.md', encoding='utf-8').read().split('\n')
box = {chr(c) for c in range(0x2550, 0x2570)}
picture = [r for r in text if r and r[0] in box]
corridor = {'▪', '█', '▖', '▗', '▄', ' '}
both_even = [
    (c, y)
    for y, row in enumerate(picture)
    for c in range(19)
    if (row[2 * c] if 2 * c < len(row) else ' ') in corridor
    and c % 2 == 0 and y % 2 == 0
]
print('rows:', len(picture), '| corridor squares with both coordinates even:', len(both_even))
PY
```

It prints `rows: 29 | corridor squares with both coordinates even: 0`.

## What it means

The maze is carved on a lattice of **cells at odd coordinates**: cell
`(i, j)` is the grid square `(2i + 1, 2j + 1)`, and two adjacent cells are
joined by opening the one square between them. That gives **9 cells across
and 14 deep**, and the grid's dimensions are exactly what such a lattice
needs:

    19 = 2 × 9 + 1        29 = 2 × 14 + 1

MAZE-1's 19 × 29 is therefore not an arbitrary size. It is the smallest grid
holding a 9 × 14 cell maze with its surrounding wall.

## Why it is worth keeping

Two requirements stop being things to check and become things that cannot
happen, which is a much stronger position than repairing them after the fact.

**MAZE-2 — corridors one square wide.** Every 2 × 2 block of grid squares
contains one whose column *and* row are both even. Cells are odd-odd;
connectors have exactly one even coordinate; so a both-even square is never
carved, and no 2 × 2 block can be corridor throughout. A corridor two squares
wide is not unlikely — it is unrepresentable.

**MAZE-3 — the border ring is solid.** Cells occupy columns 1–17 and rows
1–27. A connector lies strictly between two cells, so columns 2–16 and rows
2–26. Nothing carveable reaches column 0 or 18, or row 0 or 28.

Both arguments are asserted exhaustively over the whole lattice in
`tests/test_generation.py`, not sampled over generated mazes, so they hold for
every maze the generator could produce rather than for the ones it happened to
produce on the day.

## What it says about caution C4

The architect called maze generation the biggest algorithmic risk in the
project, expecting carve-then-repair to be awkward to settle. On this lattice
it converges in a **single pass with no retry loop**, because the two
remaining requirements do not fight:

* A randomised depth-first carve spans every cell, so **MAZE-6** holds of the
  result and of anything made from it by adding more edges.
* The repair gives each cell a second way on by opening one more wall.
  **Adding an edge only raises degrees**, so it never creates a dead end while
  removing one and never disconnects what the carve joined. Every cell has at
  least two lattice neighbours, so a cell short of ways on always has a spare.

Measured over 500 seeds: **0 unsound, 0 with a 2 × 2 corridor block, 500
distinct mazes, 3.16 ms each** including the full structural check.

## What later items should take from it

* **WI-8** (START-1, START-2): the player and ghost start on corridor squares,
  and every corridor square is either an odd-odd cell or a connector with one
  even coordinate. START-1's "corridor square nearest the middle" has a parity
  trap in it worth knowing about before you go looking:

  > **The exact centre of the grid, `(9, 14)`, is _not_ always corridor.**
  > Its column is odd but **its row is even**, so it is a connector, and it is
  > carved only when that particular wall happens to be opened. Measured over
  > 200 seeds it is corridor in **109** of them — near enough a coin toss that
  > a search which assumed the centre was walkable would pass its own test on
  > roughly every other seed.
  >
  > The two nearest squares that *are* always corridor are the cells directly
  > above and below it, `(9, 13)` and `(9, 15)`: both corridor in **200 of
  > 200**. Every odd-odd square is a cell and every cell is always carved.

  So START-1 must search rather than compute, and its test must run over many
  seeds rather than one — a single-seed test has about even odds of picking a
  maze that hides the bug.
* **WI-4** (frame composition): wall squares are dense at even-even positions,
  which is where the lone-block glyph and the crossing glyphs will mostly
  appear. Nothing here changes C-2's mapping; it only explains the pattern.
* **Anyone tempted to change the grid size**: 19 × 29 cannot be altered by one
  without breaking the lattice. The next legal sizes are 17 × 27 and 21 × 31.
