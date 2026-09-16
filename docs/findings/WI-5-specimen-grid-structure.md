# WI-5 — What the specimen picture's maze is actually made of

**Measured by:** DEV-A, WI-5, run 6
**Source:** the specimen picture in `docs/FUNCTIONAL_REQUIREMENTS.md` (section 3)
**Why it is here:** it settles the maze's coordinate scheme against the only
normative picture we have, and WI-8 (wall glyphs), WI-12 (frame composer) and
WI-6 (opening position) all need these numbers.

---

## What was run

The fenced picture was parsed straight out of `FUNCTIONAL_REQUIREMENTS.md`
with `/usr/bin/python3`. The trailing `←` annotations were stripped, the
status line dropped, and each maze row read as 19 squares at text columns
0, 2, … 36 with connectors at the odd columns. Wall glyphs
(`═ ║ ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬ ■`) counted as wall; the dot `▪`, a space, and the
three columns of an actor counted as corridor.

## What came back

| Measured | Result |
| --- | --- |
| Maze rows in the picture | **29** |
| Width of every maze row | **37 characters**, with no row any other width |
| Odd (connector) columns | only a space, `═`, or the outer column of an actor — **never a square glyph** |
| Squares at **odd column and odd row** (126 of them) | **all 126 are corridor** — not one is wall |
| Squares at **even column and even row** (190 of them) | **all 190 are wall** — not one is corridor |
| Border ring | **solid**, all four sides |
| Corridor squares in total | **264** |
| Corridor squares with fewer than two corridor neighbours | **0** |
| Corridor squares unreachable from the rest | **0** |
| Two-by-two blocks of corridor | **0** |

## What it means

**The specimen maze is exactly an odd-coordinate cell grid.** With

```
19 = 2 * 9 + 1        29 = 2 * 14 + 1
```

the 19 × 29 grid is a 9 × 14 arrangement of **cells** at the odd coordinates,
every one of them corridor, joined by **connector** squares that are carved
when two cells are linked. Squares with two even coordinates are the pillars
between, and are never carved. The picture is not merely *compatible* with
that scheme — it satisfies it in all 551 squares with no exceptions.

Three consequences the rest of the project can rely on:

1. **MAZE-2, MAZE-3 and the no-diagonal rule are structural, not policed.** A
   two-by-two block of corridor would need an even/even square, which is never
   carved; the border ring is even in at least one axis everywhere; and two
   diagonally touching corridor squares always have a corridor cell square
   orthogonally between them.
2. **The generator built for WI-5 lays out mazes of the same shape.** Its
   output over 200 seeds has the same signature — all odd/odd corridor, all
   even/even wall, and **260 to 272 corridor squares, mean 265.5**, against
   the specimen's 264 — so what WI-8 and WI-12 see in tests is the same kind
   of maze the requirements drew.
3. **A dot count of about 265** is what START-3 implies for WI-6: one per
   corridor square, less the player's own. The score at a win (STAT-3's
   `CLEARED  score 274` is illustrative, not normative) will be that number.

## Corroboration of contradiction C-1

`docs/IMPLEMENTATION_PLAN.md` section 7 raises **C-1**: `ARCHITECTURE.md`'s
prose says the maze is 38 columns with a 2-column right-hand margin, while
its own measurement V8 and the technical lead's both say 37 and a 3-column
margin.

**Measured independently here: every one of the 29 maze rows is exactly 37
characters.** 19 squares × 2 columns, less the final connector column. In a
40-column window that leaves a **3-column** right-hand margin. The plan's
ruling — 37 and a 3-column margin — is what the picture says, and the
architecture's prose arithmetic is the only thing that disagrees.

## Reproducibility does not depend on hash ordering

**Why this was checked:** WI-19's scripted game plays a whole seeded game and
asserts the frames as text. If a seeded maze varied between runs, that test
would be flaky in a way that is very hard to read.

`/usr/bin/python3` was run five times over the same 50 seeds — with
`PYTHONHASHSEED` set to `0`, `1`, `12345`, and twice to `random` — taking a
SHA-256 over the 50 mazes each time. **All five runs gave the identical digest
`aed6cb3cea2af6ab…`.** The generator's draws all come from ordered lists, so
set iteration order never reaches a decision. A seed is enough to reproduce a
maze exactly.

## Timing, for whoever watches the suite

Also measured, on `/usr/bin/python3` 3.9.6:

| What | Time |
| --- | --- |
| `generate_maze` × 200 seeds, verification included | **0.94 s** |
| — of which carve, braid and build the grid | 0.18 s |
| — of which the structural verification before handing out | 0.78 s |

So verifying a maze costs about **4 ms**, paid once per game in production and
200 times in WI-5's property sweep. The whole of WI-5's share of the suite is
about 3 s, and roughly a third of that is the deliberate 200-seed sweep that
caution C4 asks for. If the shared suite ever needs to be faster, that sweep
is the knob — but it is the knob C4 warns against turning.
