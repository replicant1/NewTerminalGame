# WI-8 — which wall glyphs a real maze actually contains

**Measured by:** DEV-C, run 6, on this machine, with `/usr/bin/python3`
(3.9.6). Everything below was run, not reasoned about. No window was opened.

Two questions this answers, both of which a later item will want:

1. Is `╬`, the one entry in the glyph table the specimen picture does **not**
   contain, reachable in a real game — or is it dead code?
2. How often does each character appear, so that anybody looking at a screen
   knows what they should expect to see?

---

## 1. The specimen picture, inverted

The specimen in `FUNCTIONAL_REQUIREMENTS.md` was inverted back into a
19 × 29 grid of wall and corridor — square *c* of a row read at column `2c` —
and every wall square's glyph read off against the wall neighbours that
square actually has.

| Measured | Result |
| --- | --- |
| Maze rows in the specimen | **29** |
| Width of every maze row | **37 characters** (contradiction C-1 resolved as the plan says) |
| Border ring | solid on all four sides |
| Neighbour combinations occurring | **15 of 16** |
| The one absent | `NESW` → `╬`, the crossing |
| Disagreements with the table | **none** |

The connector column was checked separately, at all 29 × 18 positions:

| Connector at column `2c+1` | Characters found |
| --- | --- |
| squares *c* and *c+1* both wall | `═` — and nothing else, without exception |
| every other case | a space, or one of the actor motif's outer cells |

The actor cells in the "other case" row are the player's `▐`/`▌` and the
ghost's `▗`/`▖` overwriting a connector, which is WI-12's business and safe
for exactly the reason section 5 of the plan gives: a connector next to a
corridor square is always blank, because `═` appears only between two wall
squares.

---

## 2. The census, over 200 generated mazes

Every maze from `tests/generated_mazes.py`, seeds 0–199, from the real WI-5
generator.

| Glyph | Codepoint | Neighbours | Occurrences | Mazes containing it |
| --- | --- | --- | ---: | ---: |
| `║` | U+2551 | N, S, or either alone | 26 061 | 200 |
| `═` | U+2550 | E, W, or either alone | 21 888 | 200 |
| `╚` | U+255A | N E | 1 449 | 200 |
| `╗` | U+2557 | S W | 1 431 | 200 |
| `╔` | U+2554 | S E | 1 331 | 200 |
| `╝` | U+255D | N W | 1 329 | 200 |
| `╣` | U+2563 | N S W | 841 | 200 |
| `╠` | U+2560 | N E S | 839 | 200 |
| `╦` | U+2566 | E S W | 661 | 200 |
| `╩` | U+2569 | N E W | 653 | 200 |
| `■` | U+25A0 | none | 558 | **189** |
| `╬` | U+256C | N E S W | **61** | **55** |

Twelve distinct characters from sixteen combinations, because the four
single-neighbour cases collapse onto `║` and `═`.

| Measured | Result |
| --- | --- |
| Distinct glyphs per maze | min **10**, max **12** |
| Seeds needed for all twelve | **10** (seeds 0–9 suffice) |
| First seed containing a crossing | **1** |

---

## 3. What it means

**The crossing is not dead code.** It is the one table entry the specimen
could not confirm, and it occurs in better than a quarter of generated mazes.
If it were wrong, a player would see it — which is a better situation than a
correct-looking table with an unreachable branch, and it is why the test suite
asserts it on seed 1 by name rather than hoping.

**The lone block is common too**, in 189 of 200 mazes, which is worth knowing
because SCRN-3 names it explicitly and a human check will want to find one.

**Every entry in the table is reachable**, so `tests/test_wall_glyphs.py` can
and does assert that the first ten seeds produce all twelve.

---

## 4. What this does NOT establish

**Whether the strokes of adjacent double-line glyphs meet on screen.**

Nothing in this document bears on it. The advance widths are uniform — DEV-B
measured that for all 113 glyphs the picture uses, at 14, 16, 18 and 20pt, with
a control showing that glyphs Menlo lacks fall back to visibly different
advances — so the characters land in the right places. Whether the ink joins
at the cell boundary is a question about glyph shapes, not metrics, and **only
an eye can settle it.**

It is recorded as open in `docs/findings/WI-2-cell-metrics.md` §5 question 2,
it is open still, and **WI-16 asks it properly.** No test in WI-8 should be
read as evidence either way.

---

## 5. How to reproduce

From the repository root, with `/usr/bin/python3`:

```python
import collections, random
from tests.generated_mazes import maze_for
from terminal_game.presentation.wall_glyphs import wall_glyph_at

census = collections.Counter()
for seed in range(200):
    maze = maze_for(seed)
    for square in maze.squares():
        if maze.is_wall(square):
            census[wall_glyph_at(maze, square)] += 1
print(census.most_common())
```

The specimen inversion in section 1 is the `TheSpecimenPicture` test class in
`tests/test_wall_glyphs.py`, which runs it on every suite run.
