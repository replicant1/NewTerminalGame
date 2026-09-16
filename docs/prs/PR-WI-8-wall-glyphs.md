# WI-8 — Wall glyphs

**Announced for WI-12 (first-lander rule 4):** `wall_layer(maze)` in
`terminal_game/presentation/wall_glyphs.py` returns a maze's whole wall
skeleton as frame cells — square *c* at index `2c`, the connector at `2c+1`,
blanks everywhere else. The frame composer can lay dots and actors over it
without naming a single wall character. `wall_layer_text` is the same thing
as lines, for asserting a picture.

**Branch:** `r6/wi-8-wall-glyphs`, based on `main` at `6eb731e`.
**Developer:** DEV-C. **Depends on:** WI-1 and WI-5, both landed long since.

---

## What this is

SCRN-3, in one module. A pure function from a wall square's four neighbours
to the character that square is drawn as — the double-line corners, tees,
crossings and straights, and the lone blue block `■` where a wall has no wall
beside it — plus the rule for the odd "connector" column that sits between
two square columns. All of it in `Colour.WALL_BLUE`, and nothing else in it.

It names the Domain (`Maze`, `Direction`, `Square`) and its own frame
vocabulary. It imports no windowing toolkit and opens no window.

### The public surface

| Name | What it answers |
| --- | --- |
| `WALL_GLYPHS` | the whole table: all sixteen neighbour sets, each to its character |
| `glyph_for_wall_neighbours(neighbours)` | the pure function, total over all sixteen |
| `wall_glyph_at(maze, square)` | asks the maze, then the table; raises `NotAWallSquare` for corridor |
| `wall_cell_at(maze, square)` | the same, as a `Cell` in wall blue |
| `connector_glyph_east_of(maze, square)` | `═` when this square and its eastern neighbour are both wall, blank otherwise |
| `connector_cell_east_of(maze, square)` | the same, as a `Cell`; a blank connector is the frame's `BLANK`, on black ground |
| `wall_layer(maze)` / `wall_layer_text(maze)` | the whole wall skeleton, announced above |

`NotAWallSquare` rather than a space: a corridor square has no wall glyph at
all, and answering with a blank would let a composition bug draw a silently
empty maze.

---

## Where the table came from — measured, not remembered

The specimen picture in `FUNCTIONAL_REQUIREMENTS.md` was inverted back into a
19 × 29 grid of wall and corridor, and every wall square's glyph was read off
against the wall neighbours that square actually has.

**Fifteen of the sixteen combinations occur in the specimen, and every one of
them agrees with the table.** The sixteenth — walls on all four sides, drawn
`╬` — does not occur there. Section 5 of the plan says the same.

That reasoned entry is not a theoretical corner. Over the 200 shared seeds in
`tests/generated_mazes.py`, crossings appear **61 times, in 55 of the 200
mazes, the first at seed 1**. A player will see them. Full census in
`docs/findings/WI-8-glyph-census.md`.

The specimen test does not let the table decide the question it is being
asked: the inversion classifies a square as wall by **Unicode block** (Box
Drawing, U+2500–U+257F, plus the lone block this item owns), not by looking
anything up in `WALL_GLYPHS`. So a swapped pair of tees would still classify
both squares as wall and would still fail the comparison.

---

## Ownership boundaries, as the plan draws them

**The maze query surface is DEV-A's and no query was added to it.**
`Maze.wall_neighbours(square)` already existed — DEV-A landed it with WI-5 and
its docstring says it is there so "the border ring resolve[s] to the corner
and edge glyphs the specimen picture shows". It returns exactly the frozenset
this item needs, including the part that matters most: *a neighbour outside
the grid is not a wall*, which is what makes the border ring read as a ring
rather than as a row of crossings. Nothing was asked of DEV-A.

**A test helper that builds a maze from an ASCII picture already exists too.**
`Maze.from_text`, also DEV-A's, and already used by WI-6, WI-7 and the maze
tests. The plan reserved that helper for whichever of WI-7 and WI-8 needed it
first; neither needed to write one.

**WI-8 declares neither the dot glyph nor the two actor motifs.** Those are
WI-12's. `DeclaresNothingItDoesNotOwn` in the tests pins that from this side
without naming either of them: over forty generated mazes, every character
this module emits is in `WALL_GLYPHS` or is a blank, and every colour is wall
blue or the black ground. There is nowhere a motif could have been smuggled
in.

---

## The one thing in this item nobody can measure

**Whether the strokes actually meet is not settled here and is not claimed
anywhere.**

The spacing *is* settled: DEV-B measured that all 113 glyphs the picture uses
share one advance width in Menlo at 14, 16, 18 and 20pt, with a control
showing glyphs Menlo lacks fall back to visibly different advances — so the
uniform figure is Menlo's own coverage, not a fallback artefact. The
characters will land in the right places.

Whether the ink of one `═` meets the ink of the next at the cell boundary is
a question about glyph *shapes*, not metrics. No test in this branch bears on
it, the module's docstring says so, and the test module's docstring says a
green run here is not evidence for it. It is open, `docs/findings/WI-2-cell-metrics.md`
already records it as open, and **WI-16 asks it properly**.

---

## Tests

`tests/test_wall_glyphs.py`, 43 tests.

- **`TheSixteenCombinations`** — all sixteen, one test each, every expected
  character written as a literal so a reader can hold the file next to the
  specimen picture and check them off. The fixture is a 3 × 3 maze whose
  diagonals are corridor, so only the four orthogonal neighbours can
  influence the answer.
- **`TheTableIsTotalAndWellFormed`** — the powerset of the four directions is
  sixteen and every member has a glyph; every glyph is exactly one character,
  so it fits a `Cell`; neighbour order makes no difference; a non-`Direction`
  is refused.
- **`AskingAboutASquare`** — the glyph comes back in wall blue; corridor
  raises `NotAWallSquare`; a square off the grid raises rather than being
  answered with a blank.
- **`TheConnectorColumn`** — the horizontal between two joined walls, and
  blank in each of the three other cases; a joining connector is blue and a
  blank one is the frame's `BLANK` on black ground; asking past the last
  square of a row raises.
- **`TheWallLayer`** — a bordered ring reads as a ring (the plan's border-ring
  case: corners, edges and connectors in one picture small enough to check by
  eye) and a lone wall stands alone; a row is `2w − 1` cells; a 19-square maze
  is exactly `MAZE_COLUMNS`, tying the layout to the frame's constant rather
  than to the literal 37.
- **`TheSpecimenPicture`** — the normative picture (assumption A6) reproduced
  character for character, plus the two sanity checks on the inversion and the
  fifteen-of-sixteen measurement kept where it can go stale.
- **`DeclaresNothingItDoesNotOwn`** — the WI-12 boundary, above.
- **`TheWallsOfARealMaze`** — corridor squares are blank and wall squares are
  not; seed 1 really contains a crossing; the first ten seeds produce all
  twelve distinct characters, so no entry is unreachable.

**Suite**, from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
392 passed, 0 failed, 0 skipped
```

349 before this branch, so 43 new. No window is opened by any of them, and
`tkinter._default_root` was confirmed `None` after running the whole suite in
one interpreter — the existing test that asserts it is untouched and passes.

Two tests were written and then removed for re-asserting behaviour
`tests/test_maze.py` already owns: that `wall_neighbours` excludes what is off
the grid, checked at four corners, and a weaker "only two colours appear"
alongside the stronger "blue marks ink, black marks nothing". The border ring
is now asserted once, as a picture, and the colour rule once, over forty
mazes.

---

## Also produced

`docs/findings/WI-8-glyph-census.md` — how often each of the twelve characters
occurs across 200 generated mazes, and the crossing measurement above. It is
in `findings/` rather than here because it is the kind of number a later item
will want to rely on, and this file will not be read again.

---

## Deviations

**Additive.** `wall_layer` / `wall_layer_text` are more than "a pure function
from a wall square's four neighbours to the glyph". They are that function
plus the connector rule applied across a grid — both of which this item owns —
and they exist so WI-12 need not re-derive the layout. Announced above per
first-lander rule 4. Flagged for a ruling as an additive deviation.

Nothing was omitted and nothing was done differently.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
