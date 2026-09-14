# WI-5a — wall-glyph selection

**Branch:** `wi-5a-wall-glyphs`, cut from `main` at `c4171fb`
**Lane:** DEV-B, iteration M1
**Mode:** local — this file stands in for the pull request. Nothing was pushed; no `gh` was used; the branch is not merged.
**Suite:** `python3 -m unittest discover` from the repository root — **299 passed, 0 failed, 0 skipped** (7.0 s).
**Windows opened:** none. A glyph table drives nothing on the desktop.

---

## What this is

SCRN-3: a pure mapping from a wall square's four neighbours to the blue double-line glyph that joins
up with them, and the single blue block for a wall square with no wall beside it. Sixteen neighbour
patterns, twelve distinct glyphs, one colour.

It creates the **Presentation layer**, which did not exist before this branch.

## The files

| File | What it is |
| --- | --- |
| `terminalgame/presentation/__init__.py` | The layer, and where screen geometry is allowed to live. |
| `terminalgame/presentation/wall_glyphs.py` | `BY_NEIGHBOURS` (the table), `glyph_for_neighbours`, `joins_up_with`, `wall_neighbours`, `wall_glyph`, `wall_glyphs`, `WALL_COLOUR`, `NotAWallSquare`. |
| `tests/test_wall_glyphs.py` | 38 tests in seven classes. |
| `tests/test_layering.py` | **Extended**, not created — `PresentationLayerTest`, 5 tests. |
| `docs/findings/WI-5a-glyph-table-from-the-picture.md` | The derivation, and the two things it incidentally proves. |
| `docs/progress/wi-5a-wall-glyphs.md` | The progress log. |

Names collide with nothing: the existing test files are `test_screen_port.py`, `test_curses_adapter.py`,
`test_game_main.py`, `test_real_terminal.py`, `test_layering.py`, `test_maze.py`,
`test_maze_generator.py`, `fake_terminal.py`, and DEV-A's `test_launcher_*.py`,
`test_end_to_end_join.py`, `test_game_command.py`, `launcher_fakes.py`. The only shared file is
`tests/test_layering.py`, already on `main`.

## The table was measured, not read off by eye

The specification contains a worked example — a game in progress, 29 rows of maze. **That is 287 wall
squares drawn by whoever wrote the requirements**, and reading a 37-column ASCII picture by hand is
exactly where a transcription error hides. So it was parsed instead.

The picture's rows are 37 columns = `2 × 19 − 1`, so **square `x` is drawn at column `2x`** and the
odd columns are the joins. Parsing column `2x` recovers the maze: 287 wall squares, 264 corridor.
**Every neighbour pattern appearing in the picture is drawn with exactly one glyph** — not one
pattern, in 287 squares, is ever drawn two different ways.

Fifteen of the sixteen entries are settled that way. The sixteenth is the four-way crossing, which
never occurs in the picture; SCRN-3 names *"crossings"* in its own words and there is only one
double-line crossing. **That row is the one entry in the table with no worked example behind it**, and
the finding says so rather than letting the table look uniformly well-evidenced.

## The thing most likely to be got wrong later

**Off the grid is *not* a wall neighbour.** `Maze.square_at` answers `WALL` for anything beyond the
edge — WI-4 made it do that on purpose, so an actor walking at the edge is told the world is solid.
For glyph joining the opposite answer is needed, or the border ring draws as a mesh of crossings
instead of a rectangle.

Both answers are individually reasonable, and the wrong one still produces a picture that looks like a
maze. So it was checked rather than chosen. Re-deriving the whole table from the picture under each
convention:

| convention | patterns seen | patterns drawn more than one way |
| --- | --- | --- |
| off the grid is **not** wall | 15 | **0** |
| off the grid **is** wall | 16 | **5** |

Under the wrong convention the picture contradicts itself five times, one pattern being drawn seven
different ways. **The specification settles it; nobody had to have an opinion.**

The distinction has its own name rather than being a branch inside `is_wall`, because it is **two
questions that happen to be spelt the same way** and not one question with two answers.
`maze.is_wall(x, y)` answers *can an actor move there* — yes beyond the edge, the world outside the
maze is solid. `joins_up_with(maze, x, y)` answers *is there a wall square to join up with* — no
beyond the edge. **Both are right, and the obvious tidy-up that makes them agree would break one.**
`TwoQuestionsOneSpellingTest` holds it: the two agree at every square inside the grid, which is why
the difference is easy to miss; they disagree beyond it on purpose; and the border ring is the
consequence a unification would destroy.

## How a lookup table was tested without testing it against itself

A table test is the easiest kind to write vacuously: walk `BY_NEIGHBOURS`, assert each entry equals
itself, green forever, says nothing. So **nothing that decides what is correct here was derived from
the table.** Three independent authorities:

**1. The specification's picture.** Parsed out of `docs/FUNCTIONAL_REQUIREMENTS.md` at test time,
turned back into a `Maze`, and every wall square re-rendered through the table and compared glyph for
glyph. **287 squares, 0 mismatches.** The test reads the document rather than a copy of it on purpose:
edit the picture and the suite says the table needs rechecking, which is what should happen.

**2. The Unicode names of the glyphs.** `unicodedata.name('╚')` is `BOX DRAWINGS DOUBLE UP AND RIGHT`
— the Unicode standard's own description, which has never heard of this project. Two properties are
checked against it for all sixteen patterns: *every wall neighbour has an arm pointing at it*, and
*the glyph chosen is the one with the fewest spare arms*. The second is what makes a lone-north wall
`║` rather than `╬` — both have a north arm; `║` has one spare arm where `╬` has three — so the
"there are no half-lines" argument is checked rather than asserted in a comment.

**This is also what catches an inverted axis.** `UP` is north because north is `y − 1`. An
implementation that mapped north to `DOWN` would still draw something maze-shaped with half its
corners wrong, and a glyph table is precisely where that hides. There is a test named for it.

**3. Whole generated mazes.** Over 40 seeds: the four corners of the border ring are the four corners
and never crossings; the border edges are straights or tees and never corners; and wherever two wall
squares touch, both glyphs reach towards each other — with the arms again read from Unicode, not from
the table.

The one case where an arm legitimately points at a corridor — a wall with a single wall neighbour,
drawn as a straight, exactly as the picture draws `════ ▪` — is tested as the *only* such case: a
corner or tee with a spare arm would be a bug, and the test distinguishes them.

**No test was proved able to fail and no working code was broken.** The two convention comparisons in
the finding are re-derivations of the table from the picture under a different *reading of the
specification* — no module was edited and nothing was made to fail.

## What the tests establish, against the plan's list

The plan's WI-5a row asks for three things:

| Asked | Where |
| --- | --- |
| every one of the sixteen neighbour patterns maps to the glyph that joins its neighbours, the isolated case included | `TheGlyphsAgreeWithUnicodeTest` for all sixteen; `ThePictureInTheSpecificationTest` for the fifteen the picture vouches for; `test_the_lone_block_is_the_only_glyph_with_no_arms` for the isolated case |
| the colour is blue | `TheColourTest` — followed through to `curses.COLOR_BLUE` via the adapter's palette, not stopped at the name `Colour.WALL` |
| the mapping is a function of the four neighbours and of nothing else | `test_the_mapping_depends_on_the_four_neighbours_and_nothing_else` — wall squares from 30 different mazes at different coordinates, grouped by pattern, one glyph per group |

## What WI-5b inherits

```python
from terminalgame.presentation.wall_glyphs import (
    wall_glyph,      # (maze, x, y) -> the character for that wall square
    wall_glyphs,     # (maze) -> [(x, y, glyph), …] in reading order
    WALL_COLOUR,     # Colour.WALL, for every wall square
)
```

Three things WI-5b needs to know:

1. **This item says what goes in column `2x` and stops.** The shared column `2x + 1` between two
   squares — the `═` that joins two horizontally adjacent walls — is WI-5b's. The finding records the
   `2 × 19 − 1` geometry that was measured off the picture, which is the fact WI-5b will want.
2. **`wall_glyph` raises `NotAWallSquare` for a corridor square or one off the grid**, per plan §11.8.
   Do not catch it and substitute a space; a caller asking for the wall glyph of a corridor square has
   a bug, and the refusal is where it shows.
3. **The colour never varies.** SCRN-3 varies the character with the neighbours and nothing else.

## `tests/test_layering.py` — what the extension contains

Stating content rather than agreement, as the file is the one place the lanes could collide:

- Everything already there is **unchanged** — `LayerRuleTest` (3 tests) and `DomainPurityTest`
  (6 tests), same names, same assertions.
- `domain_files()` now delegates to a new `files_under(layer)`; its behaviour is identical.
- Added: `THE_PRESENTATION`, `FORBIDDEN_IN_PRESENTATION`, `PRESENTATION_MAY_IMPORT`,
  `presentation_files()`, and `PresentationLayerTest` with 5 tests — the layer is where it says it is;
  Presentation imports no `curses`, `subprocess`, `os`, `sys` or `time`; it imports only
  `terminalgame.domain` and `terminalgame.screen.port`; it never mentions the curses adapter; and the
  Domain never imports Presentation.

## Deviations and one question needing a ruling

**1. The question: may Presentation import the screen port?** Plan §3 says *"Presentation depends on
Domain, and on nothing else"* and, in the same paragraph, that Presentation *"turns a domain state
into a grid of characters and colours"*. It cannot name a colour without `Colour`, which lives in
`terminalgame/screen/port.py`. The architecture's dependency arrow (line 54) says
*"Application → Presentation → Domain, and Application → Screen port"*, omitting Presentation → port;
but the port's own docstring has said since WI-2 that *"Presentation asks for `Colour.WALL`"*, and
the §9 traceability rows for SCRN-4, SCRN-5 and SCRN-6 all describe Presentation as owning a "glyph
**and colour** table".

**Assumed and proceeding on:** Presentation may import the port's **value vocabulary** — `Colour`, and
later `Cell`/`Frame` for WI-5b — and nothing behind the port. It never imports the adapter, and there
is a test for that. **This is an assumption, not a ruling**, and it is pinned in one tuple,
`PRESENTATION_MAY_IMPORT`, so a decision the other way changes one line and the test tells whoever
makes it whether anything else broke.

The alternative — Presentation defining its own colour names and Application translating — is
coherent but duplicates the five names the specification gives, and puts a translation table in
Application where nothing else lives.

**2. Additive: `wall_glyphs(maze)`, `wall_neighbours(maze, x, y)` and `joins_up_with(maze, x, y)` are
public.** The plan asks only for the mapping. `wall_glyphs` is what WI-5b will actually call;
`wall_neighbours` and `joins_up_with` are exposed because the off-the-grid rule lives in them and
deserves both a name and a test of its own. Neither adds behaviour
beyond the table.

**3. Additive: `NotAWallSquare`.** Plan §11.8 — refuse where the argument makes the requirement
impossible. SCRN-3 has nothing to say about how a corridor square is drawn.

## Contradictions found

**One, and it is the ruling question above** — §3's "on nothing else" against §3's own "characters and
colours", with the architecture's arrow on one side and the port's docstring and the §9 traceability
rows on the other. Evidence is quoted in full in the section above. It is not a blocker and the code
runs either way; it wants deciding before WI-5b builds a frame on the assumption.

**Not a contradiction, but worth recording:** the specification's illustrative maze — drawn by hand,
before any generator existed — satisfies every one of WI-4's requirements, including sitting entirely
on the odd lattice of caution C8: 0 open 2 × 2 blocks, 0 border breaches, 0 dead ends, 0 unreachable
squares, 264 corridor squares against WI-4's measured range of 259–272. **The maze somebody drew by
hand is one the generator could have produced.** That is independent corroboration of WI-4 from a
source that predates it, and worth more than another thousand seeds of the generator agreeing with
itself. There is a test for it.

## What needs a human

Two, neither of which an agent can settle, and both already on WI-14b's list.

1. **Do the box-drawing characters exist in the launcher's font, at a single advance width?**
   `═ ║ ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬ ■` must all be exactly one column wide or the picture shears. A
   pseudo-terminal cannot answer this; the real window can. Steps: run the launcher once WI-3 has
   landed, and look at whether the vertical walls line up down the whole height of the window. A
   sheared column means the font substituted a glyph at a different width.
2. **Is the blue legible?** `Colour.WALL` reaches the terminal as `curses.COLOR_BLUE` on black, which
   on some profiles is very dark. Whether SCRN-3's "blue double lines" read as walls to a person is a
   human judgement and is **not** recorded anywhere as verified.

**No window was opened and nothing touched the desktop.**

## Commits

| | |
| --- | --- |
| `8fe03d2` | WI-5a: the wall-glyph table, measured from the specification's picture |
| `7a2d678` | WI-5a: the finding, the PR summary, and the log |
| `036e213` | WI-5a: name the second question rather than let it share the first's words |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
