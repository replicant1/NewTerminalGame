# WI-3 — Glyph and colour tables, and the whole picture

**Branch** `wi-3-glyphs-picture` · **Base** `main` · **Lane** Dev A, round 2 ·
**Depends on** WI-1 (merged)

A pure function from a game state to the picture, and the tables it draws
from. Nothing here imports `curses`, and nothing here is impure at all.

**Lands** SCRN-1, SCRN-2, SCRN-3, SCRN-4, SCRN-5, SCRN-6, MAZE-1 (the margin),
SCORE-5 (the score is shown), END-4 (the draw order), STAT-1, STAT-2, STAT-3.

---

## What is in it

### `termgame/theme.py` — new, pure

The drawing vocabulary, and nothing that knows a terminal exists.

- **The wall glyph rule.** A four-bit mask of which of a wall cell's
  north / south / east / west **cell**-neighbours are wall, and a 16-entry
  table from mask to glyph. Fifteen entries were decoded directly off the
  specification's mock-up; `N|S|E|W → ╬` is the one inferred entry and is
  named as such in the source (`INFERRED_MASK`) so that changing it is a
  deliberate act.
- **Off-grid is not wall.** `theme.neighbour_is_wall` deliberately answers
  the opposite of `Maze.is_wall` for a cell outside the grid. This is the
  difference between the mock-up's top-left corner being `╔` and it being a
  crossing joining on to nothing, and it has a named test.
- **The joiner-column rule.** Odd picture column `2c + 1` carries `═` if and
  only if the cells on both sides of it are wall, and is blank otherwise.
- **The glyphs** — dot `▪`, player `▐█▌`, ghost `▗█▖`, lone wall square `■`.
- **Five style identifiers** — `"wall"`, `"dot"`, `"player"`, `"ghost"`,
  `"status"`, alongside WI-1's `"default"`. Each maps to a `Style` carrying a
  256-colour index and a tuple of plain attribute names (`"bold"`, `"dim"`).
  **Style identifiers, not curses constants** (plan §2.4, architecture C6).
- **The three status strings**, the specification's quotes verbatim, with the
  score as the only substitution.

### `termgame/view.py` — new, pure

`render(state) -> Frame` — the 30 × 40 picture, comparable as text with no
terminal attached.

- Geometry: picture column `2c` carries maze column `c`; picture row = maze
  row; row 29 is the status line; columns 37–39 are MAZE-1's narrow blank
  margin.
- Draw order: **walls, then dots, then the player, then the ghost last.**
  That single ordering is the whole of END-4 and costs nothing.
- The status row is written at column 1 — assumption **A3**, see below.

### `tests/fixtures/spec_picture.txt` — new, data

The golden fixture: the specification's own picture as **30 rows of exactly
40 columns**. Rows 0–28 are WI-1's `spec_maze.txt` (the mock-up verbatim)
padded with the three-column margin; row 29 is the status line. Trailing
spaces are part of the data, and a test fails loudly if anything strips them.

### `tests/test_theme.py`, `tests/test_view.py` — new

72 tests. See below.

---

## What the tests establish

Each bullet in WI-3's "tests must establish" list, and where it is:

| Required | Where |
|---|---|
| **All sixteen wall masks**, exhaustive, against the table decoded from the mock-up | `TestTheWallGlyphTableAgainstTheSpecification`. The test decodes the table from `spec_maze.txt` at run time rather than hard-coding it, asserts that the mock-up settles exactly 15 of the 16, asserts that **every one of those 15 is unambiguous** (no mask is drawn two ways), and then checks all 16 entries of `theme.WALL_GLYPHS` against it |
| **The golden fixture** — the spec's picture back as exactly those 30 rows | `TestTheGoldenFixture`. Also asserts the fixture is 30 × 40 and that the two fixtures have not drifted apart, so nobody can quietly rewrite the golden file to match a bug |
| **The joiner-column invariant** over many seeds | `TestTheJoinerColumnInvariant`, 60 generated mazes. Both halves: the columns either side of every corridor cell are blank, and a joiner carries a bar exactly when both sides are wall. The entity-spill columns are skipped, and the test asserts it still checked more than 400 cells per seed so the skip list cannot swallow the check |
| **The player and ghost never spill off either edge** — asserted, not reasoned about | `TestTheEntitiesStayOnTheScreen`, over 60 seeds × every corridor cell. Plus a render of every corridor cell in turn, and a test that an entity on column 0 would *raise* rather than clip silently |
| **Draw order** — same cell renders the ghost | `TestTheDrawOrder` |
| **All three status strings**, character for character, with the score substituted | `TestTheThreeStatusStrings` (the text) and `TestTheStatusLineInThePicture` (the row as rendered, padded to 40) |
| **Only characters and style identifiers, no curses types** | `TestNothingCursesShapedCrossesTheSeam`. Every cell is a one-character `str` with a `str` style; every style used is one `theme.STYLE_NAMES` declares — and the picture uses **all** of them, so the subset check cannot pass vacuously. Both modules are also walked as an AST and fail on `curses`, `A_BOLD`, `A_DIM`, `COLOR_PAIR` or `color_pair` appearing as an identifier |

Beyond the list: that an eaten dot leaves the picture (SCORE-1), that a dot
under the ghost stays in the state though it is hidden (SCORE-4), that no
maze row carries the status style and nothing but the status line is on row
29 (STAT-1), that rendering is deterministic and does not touch the state,
and that the picture never writes the bottom-right cell (architecture C1).

**Suite**

```
/usr/bin/python3 -m unittest discover -s tests
Ran 258 tests in 7.205s
OK (skipped=2)
```

`main` stood at 186 passed, 2 skipped. 186 + 72 = 258, and the two skips are
the same two. Nothing regressed.

**Mutation checks** — not applicable — not part of this workflow.

---

## Assumption A3 — recorded, not ruled

Open question **A3** is with the user and unanswered. The specification's two
end-of-game examples disagree with each other about where `q quits` starts —
offset 19 in `CAUGHT  score 37   q quits`, offset 20 in
`CLEARED  score 274  q quits` — and the mock-up shows a leading blank column
that neither quoted string contains.

**Proceeding on the technical lead's assumption: all three strings verbatim,
each indented by one column.** That reproduces both the quotes and the
picture. It is **not** a ruling.

If the user answers otherwise, the whole change is
`theme.STATUS_INDENT` and `theme.STATUS_TEMPLATES`, plus the three expected
strings in `TestTheStatusLineInThePicture`. Both are commented in the source
as assumption A3.

---

## A contradiction found in the specification

**Two entities on horizontally adjacent corridor cells must share a picture
column, and the specification never says what should happen.**

The measurement: SCRN-5 gives each entity **three** characters (`▐█▌`,
`▗█▖`) while the maze pitch is **two** picture columns per cell. An entity on
maze column `c` covers picture columns `2c-1, 2c, 2c+1`. An entity on `c+1`
covers `2c+1, 2c+2, 2c+3`. Column `2c+1` is claimed by both.

This is reachable in ordinary play — a horizontal corridor with the player
and the ghost side by side is a frame away from a collision, not an exotic
board — but it does **not** occur anywhere in the mock-up, which draws the
player at maze (13, 10) and the ghost at (27, 1). So the specification's
picture gives no guidance and neither SCRN-5 nor END-4 addresses it.

It is not avoidable while the glyphs stay three characters wide, so this is a
consequence of the specification rather than a defect in the renderer.

**Proceeding on the draw order the plan specifies** — the ghost is drawn last,
so the ghost keeps the shared column and the player loses its right-hand edge
for that one frame. SCRN-5's actual requirement survives: both are still
visible, still distinguishable by colour and by outline. The behaviour is
pinned by `TestTwoEntitiesSideBySide` in both directions, so it is a known
behaviour rather than a surprise, and flipping it is a few lines.

**This needs a ruling only if the user dislikes it**; it is not blocking.

---

## Deviations from the plan

None in substance. Two things worth naming:

1. **The picture fixture is a second file** (`tests/fixtures/spec_picture.txt`)
   rather than an edit to WI-1's `spec_maze.txt`. WI-1's fixture is loaded by
   `tests/test_maze.py` as 29 rows of 37, and changing its shape would have
   broken a merged work item for no gain. A test asserts the two do not drift
   apart.
2. **`theme.neighbour_is_wall` exists** because `Maze.is_wall` returns `True`
   for a cell off the grid, which is right for movement and wrong for the
   glyph rule. This is additive and touches nothing WI-1 landed.

## What needs a human

- **H6 — does the picture look right?** Not mine to judge. What I can hand
  over: the golden fixture reproduces the specification's own picture exactly,
  so the *shapes* are the specification's shapes. What a person still has to
  look at is the **colours**, which the specification names in words only:
  wall 33, dot 178 dim, player 226 bold, ghost 213, status 51, all
  256-colour indices on a black background. If any of those reads wrong,
  the change is one line of `theme.STYLES` and no test moves — the tests
  assert that the colours are distinct and in range, never what they are.
- **A3** (above) — the user's answer, if it differs, is a few lines.
- **The side-by-side overlap** (above) — a ruling only if the user dislikes it.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
