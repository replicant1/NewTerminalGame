# WI-5a — the wall-glyph table, derived from the specification's picture

**Item:** WI-5a, wall-glyph selection (SCRN-3). **Lane:** DEV-B, iteration M1.
**Measured on:** `wi-5a-wall-glyphs` at `8fe03d2`, Python 3.9.6, standard library only.

The specification contains a worked example of a game in progress — 29 rows of maze drawn by
whoever wrote the requirements. **It is 287 wall squares of evidence about SCRN-3**, and this is what
it says. Anyone revisiting the glyph table should start here rather than reading the picture off by
eye, which is exactly where a transcription error would hide.

## The geometry of the picture

The picture's maze rows are **29 rows of 37 columns**. 37 is `2 × 19 − 1`: nineteen squares drawn two
terminal columns to a square, with the column between two squares shared. So **square `x` is drawn at
column `2x`**, and the odd columns carry the joins — an `═` where two horizontally adjacent wall
squares meet, a dot or a space otherwise.

That is a Presentation fact, not a Domain one, and it is the fact WI-5b will need. Parsing column
`2x` of each row recovers the maze exactly: **287 wall squares, 264 corridor squares, 551 in total**,
which is 19 × 29.

## What the picture determines

Every neighbour pattern that appears in the picture is drawn with **exactly one** glyph. Not one
pattern in 287 squares is ever drawn two different ways.

| N | S | E | W | glyph | times in the picture |
| --- | --- | --- | --- | --- | --- |
| · | · | · | · | `■` | 2 |
| ✓ | · | · | · | `║` | 11 |
| · | ✓ | · | · | `║` | 7 |
| · | · | ✓ | · | `═` | 10 |
| · | · | · | ✓ | `═` | 9 |
| ✓ | ✓ | · | · | `║` | 118 |
| · | · | ✓ | ✓ | `═` | 90 |
| ✓ | · | ✓ | · | `╚` | 2 |
| ✓ | · | · | ✓ | `╝` | 8 |
| · | ✓ | ✓ | · | `╔` | 8 |
| · | ✓ | · | ✓ | `╗` | 7 |
| ✓ | ✓ | ✓ | · | `╠` | 7 |
| ✓ | ✓ | · | ✓ | `╣` | 3 |
| · | ✓ | ✓ | ✓ | `╦` | 2 |
| ✓ | · | ✓ | ✓ | `╩` | 3 |
| ✓ | ✓ | ✓ | ✓ | `╬` | **0 — never occurs** |

**Fifteen of the sixteen entries are settled by the picture.** The sixteenth, the four-way crossing,
never occurs in it — a wall square surrounded on all four sides by wall is possible but rare, and this
maze happens not to contain one. SCRN-3 names *"crossings"* in its own words, and
`BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL` is the only double-line crossing there is, so the entry
is not in doubt. It is nonetheless **the one row of the table with no worked example behind it**, and
a reader deciding how much to trust the table should know which row that is.

## Off the grid is not a wall neighbour — and this is forced, not chosen

`Maze.square_at` answers `WALL` for any square beyond the edge of the grid. WI-4 made it do that
deliberately, so an actor walking at the edge is told the world is solid rather than handed an
exception. **For glyph joining the opposite answer is needed**: a wall square in the border ring has
nothing beyond the edge to join up with, so the top-left corner must be `╔` and not `╬`.

It would be easy to record that as a preference. It is not one. Re-deriving the whole table from the
picture under each convention:

| convention | patterns seen | patterns drawn more than one way |
| --- | --- | --- |
| off the grid is **not** wall | 15 | **0** |
| off the grid **is** wall | 16 | **5** |

Under the wrong convention the picture contradicts itself five times — including one pattern drawn
**seven different ways** (`╔ ╗ ╚ ╝ ╠ ╣ ╦` all for `N S E W`). Under the right one it is perfectly
consistent across 287 squares. **The picture settles the convention; nobody had to choose it.**

This is the single most likely thing to be got wrong by someone rewriting this later, because both
answers are individually reasonable and the wrong one still produces a picture that looks like a maze.

## Why a single wall neighbour gives a straight, not a stub

The double-line box-drawing set has **no half-line characters** — there is no "double line arriving
from the north and stopping". So a wall square whose only wall neighbour is to the west is drawn `═`,
and its east arm points at a corridor square. The picture does this too: `════ ▪`, a run that simply
ends.

The rule, stated so it can be checked rather than eyeballed: **every wall neighbour has an arm
pointing at it, and the glyph used is the one with the fewest spare arms.** For a single neighbour
that yields the straight (one spare arm) rather than a tee (two) or the crossing (three). For two or
more neighbours it yields an exact character with no spare arms at all.

## The glyphs check against Unicode, which never heard of this project

`unicodedata.name` gives each glyph's arms independently of anything here:

| glyph | Unicode name | arms |
| --- | --- | --- |
| `═` | BOX DRAWINGS DOUBLE HORIZONTAL | east, west |
| `║` | BOX DRAWINGS DOUBLE VERTICAL | north, south |
| `╔` | BOX DRAWINGS DOUBLE DOWN AND RIGHT | south, east |
| `╚` | BOX DRAWINGS DOUBLE UP AND RIGHT | north, east |
| `╠` | BOX DRAWINGS DOUBLE VERTICAL AND RIGHT | north, south, east |
| `╬` | BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL | all four |
| `■` | BLACK SQUARE | none |

**`UP` is north, because north is `y − 1`.** That sentence is the whole of the axis-inversion trap:
an implementation that mapped north to `DOWN` would still draw something maze-shaped, and half the
corners would be wrong in a way no casual look would catch. Checking the table against the Unicode
names is what turns that into a failing test rather than a thing somebody notices in M3.

## A second thing the picture turns out to prove

The illustrative maze was drawn by hand for the specification, before any generator existed. Checked
against WI-4's requirements it comes out clean:

| | |
| --- | --- |
| 2 × 2 fully-open blocks (MAZE-2) | **0** |
| Border squares that are corridor (MAZE-3) | **0** |
| Dead ends (MAZE-5) | **0** |
| Unreachable corridor squares (MAZE-6) | **0** |
| Corridor squares with both coordinates even (the odd lattice, caution C8) | **0** |
| Corridor squares | **264** — inside WI-4's measured range of 259–272 |

**The maze somebody drew by hand is one WI-4's generator could have produced**, down to sitting on the
same odd lattice. That is independent corroboration of the generator from a source that predates it,
and it is worth more than another thousand seeds of the generator agreeing with itself.

## What this does not establish

- **Nothing about how any of it looks on a real screen.** Whether the terminal's font has these
  box-drawing characters at a single advance width is WIN-2's, is already on WI-14b's human-check
  list, and no agent can settle it.
- **Nothing about the colour beyond the port.** The table's colour is `Colour.WALL`, and the adapter
  maps that to `curses.COLOR_BLUE`. Whether the resulting blue is legible on the player's black
  background is a human check.
- **Nothing about the joins between squares.** Column `2x + 1` — the shared column between two
  squares — is WI-5b's, not this item's. WI-5a says what goes in column `2x` and stops.
