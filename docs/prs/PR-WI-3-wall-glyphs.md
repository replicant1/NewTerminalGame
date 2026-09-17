# WI-3 — wall glyph resolution

**Branch:** `r7/wi-3-wall-glyphs`, cut from `main` at `d033ff4`.
**Base:** `main`. Not stacked on anything.

**Adds:**

| File | What it is |
|---|---|
| `terminal_game/presentation/wall_glyphs.py` | `wall_glyph(north, south, east, west) -> str`, the twelve glyph constants, and all sixteen cases written out as an explicit table. |
| `tests/test_wall_glyphs.py` | 25 tests: the sixteen cases by name, the comparison against the specimen picture, and the guards that stop a file-reading test passing on nothing. |
| `docs/progress/r7-wi-3-wall-glyphs.md` | The progress log. |

**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**81 passed, 0 failed, 0 skipped**, nothing deselected. 56 were already there; WI-3 adds
25.

---

## The table was measured, not recalled

Fifteen of the sixteen cases come from **parsing the specimen picture in
`docs/FUNCTIONAL_REQUIREMENTS.md` square by square** — reading each maze square at screen
column `2c` (ruling C-2), classifying it by which of its four grid neighbours are walls,
and reading off the glyph the picture draws it with.

| N | S | E | W | glyph | seen in specimen |
|:-:|:-:|:-:|:-:|:-:|---|
| · | · | · | · | `■` | 2 × |
| · | · | · | W | `═` | 9 × |
| · | · | E | · | `═` | 10 × |
| · | · | E | W | `═` | 90 × |
| · | S | · | · | `║` | 7 × |
| · | S | · | W | `╗` | 7 × |
| · | S | E | · | `╔` | 8 × |
| · | S | E | W | `╦` | 2 × |
| N | · | · | · | `║` | 11 × |
| N | · | · | W | `╝` | 8 × |
| N | · | E | · | `╚` | 2 × |
| N | · | E | W | `╩` | 3 × |
| N | S | · | · | `║` | 118 × |
| N | S | · | W | `╣` | 3 × |
| N | S | E | · | `╠` | 7 × |
| N | S | E | W | `╬` | **0 — derived, see below** |

**Every combination that occurs is drawn exactly one way** across all 19 × 29 squares, so
SCRN-3 really is a function of the four booleans and of nothing else. That is asserted as a
test in its own right, because if it were false WI-3 would be the wrong shape.

### Two things the measurement settled that are easy to guess wrong

**A single wall neighbour draws the full line, not a stub.** North-only (11 squares) and
south-only (7) are both `║`, never `╨` or `╥`; east-only (10) and west-only (9) are both
`═`, never `╞` or `╡`. Thirty-seven squares, no exceptions. Reaching for the stub
characters is the obvious wrong guess and the picture rules it out.

**Outside the grid is not a wall.** The border corners prove it: the top-left square has no
northern and no western neighbour and the specimen draws it `╔`, which is the glyph for
*south and east only*. Had "outside" counted as a wall it would have had to be `╬`. All
four corners agree. So a caller at the edge passes `False` for the neighbours that do not
exist — and since MAZE-3 makes every border square a wall, that path is taken constantly.

### The one case that is not evidence

**The crossing `╬` (U+256C) does not occur in the specimen.** It is taken from the same
double-line family as the other fifteen, and it is labelled *derived, not observed* in the
module, in the constant's own comment, and in a test that asserts **exactly which case is
missing** — so that nobody later reads "the specimen test passes" as "all sixteen were
measured". If a future specimen contains a crossing that test fails, and the right response
is to measure it, not to delete the assertion.

## About the tests

**Both kinds are here because the plan asks for both**, and they are not duplicates:

- *By name* — sixteen cases a reader can check against SCRN-3 by eye. It is also the only
  place the crossing can be pinned at all.
- *Against the picture* — the resolver run over all 302 wall squares of the normative
  specimen (assumption P5). This is the test that catches a table transcribed one row out.

**Three guards stop the file-reading tests passing vacuously**, which is the way this kind
of test usually goes wrong:

1. the parse is asserted to yield 29 rows of exactly 37 columns before anything uses it,
   and raises a named error if the specimen cannot be located at all;
2. wall glyphs and corridor glyphs are asserted to *partition* the grid with neither set
   empty, so an unrecognised glyph cannot be silently filed as corridor;
3. the set of combinations the specimen covers is asserted **exactly**, not as a lower
   bound.

The specimen is classified by the **corridor** glyphs — blank, the dot, the actor's centre
cell — deliberately *not* by the wall glyph table, so that classifying the picture does not
assume the answer under test.

No code was broken to watch a test go red, here or anywhere.

## Contradiction found in the plan

**SCRN-3's colour has no owner.** Section 4 traces SCRN-3 to **WI-3 alone**, and SCRN-3
says the walls are *blue* double lines and the lone square a *blue* block. But WI-3's own
"tests must establish" clause in section 5 asks only about **glyphs** — "naming the expected
glyph for each of the sixteen neighbour combinations … and checking those glyphs against
the ones that actually appear in the specimen picture" — and section 7 gives WI-4 "the
whole 40 × 30 field of **glyph-and-colour**".

So WI-3 ships glyphs and names no colour, which leaves the blue half of SCRN-3 unrealised
by the item the trace table points at. **This needs a ruling:** either the trace row becomes
`SCRN-3 | WI-3 (glyph) + WI-4 (colour)`, or WI-3 is meant to export a wall-colour token too.
I have not guessed — adding a speculative colour constant here is exactly the kind of
surface WI-4 would then have to work around. The cost of the first reading is one edit to
the trace table; the cost of the second is one constant and one test.

## Deviation needing a ruling (additive)

`ALL_WALL_GLYPHS`, a frozenset of the twelve characters the resolver can return, is
exported although nothing in WI-3's brief asks for it. It exists because **WI-5's font
check needs exactly that alphabet** — S-1 measured every one of these twelve in Menlo — and
because the specimen test uses it to prove the wall/corridor partition. Additive, so
flagged.

## Notes for the items downstream

- **WI-4 (mine, next in lane A):** the resolver takes four plain booleans; an edge square
  passes `False` for the neighbours that do not exist.
- **WI-5:** `ALL_WALL_GLYPHS` is the set your font check wants. S-1's finding
  (`docs/findings/S-1-tk-headless.md`) records that all twelve measure exactly
  `measure("M")` in Menlo at every size, with no substitution.

## Window hygiene

Nothing in WI-3 opens a window, imports a toolkit or touches the desktop. It is a pure
function over four booleans. The `needs_window` exclusion in `pytest.ini` is untouched and
no test here needs it.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
