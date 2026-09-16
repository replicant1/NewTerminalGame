# WI-12 — The frame composer

**ANNOUNCING, per the first-lander rule: this branch lands the dot glyph and
the two actor motifs — `DOT_GLYPH`, `PLAYER_MOTIF`, `GHOST_MOTIF` — and
`compose_frame(state, status_row)`, which WI-15 calls to turn a game state
into a picture. WI-8 declares none of those three; this module declares no
wall glyph.**

**Developer:** DEV-B · **Branch:** `r6/wi-12-frame-composer`
**Base:** `main` — opened stacked on `r6/wi-8-wall-glyphs`, **retargeted**
**Iteration:** M2 · **Depends on:** WI-1, WI-6, WI-8 — all landed

A game state becomes rows 0–28 of a frame value. 37 columns of maze, square
*c* at column 2c; a blank 3-column right margin; dots as the dim gold `▪`;
the player as the three-column bright yellow `▐█▌` and the ghost as the
three-column pink `▗█▖`, player painted first so the ghost covers it on a
loss (END-4). Row 29 is placed exactly as handed over and never written.

## Stacked on WI-8, then retargeted

WI-12 depends on WI-8, which had not merged when I opened this, so the PR
went up `--base r6/wi-8-wall-glyphs`. WI-8 merged (PR #43) about a minute
later and **the PR is now retargeted to `main`** with
`gh pr edit 45 --base main`. The stack was real but short.

**I was blocked for a few minutes and said so.** When I started, no
`r6/wi-8-*` branch existed on the remote, so I could not stack. I recorded
`BLOCKED` rather than working around it, and built the parts of the composer
that are unambiguously mine with the walls injected — then DEV-C pushed, and
I took the real thing.

## DEV-C had already announced exactly what I needed

This is the announce rule paying for itself, so it is worth recording. I had
invented a `WallGlyphs` protocol — two methods, one for a wall cell and one
for a connector. Then I read WI-8 and found this in its own docstring:

> **Announced for WI-12** (first-lander rule 4). The frame composer owns
> rows 0-28 and lays the dots and the actors over this; it does not need to
> know a single wall character to do so.

`wall_layer(maze)` hands back the whole wall skeleton as cells, square *c*
already at index 2c and the connector at 2c+1, corridor squares blank.
**I deleted my protocol and took theirs.** It is better than what I was
going to build — the composer now never asks a per-square question at all —
and there is one shape rather than two.

## What is in it

| File | |
| --- | --- |
| `terminal_game/presentation/frame_composer.py` | `compose_frame`, `column_of_square`, `DOT_GLYPH`, `PLAYER_MOTIF`, `GHOST_MOTIF` |
| `tests/test_frame_composer.py` | 44 tests |
| `terminal_game/presentation/__init__.py` | The layer's module list and the five vocabularies, updated |

## How the tests are split, and why

**Every test but one class stands the walls in with a deliberately fake
vocabulary** — `W` for a wall square, `-` for a joining connector. Which
glyph a wall is drawn as belongs to WI-8's 84 tests; asserting `╔` here
would turn one defect into two red files. So WI-12's tests own **where**
things go and WI-8's own **what they look like**.

One class, `TheJoinToTheRealWallGlyphs`, owns the seam and nothing either
side of it: that the composer really lays its dots and actors over the real
layer, at the columns the real layer puts walls in. Its expected picture is
*read from* `wall_layer`, never retyped, so it fails if the overlay lands
wrong and for no other reason.

## Two things I checked rather than argued about

**The plan's section-5 safety claim, verified.** Section 5 says the actors
overwrite the connector on each side and that this is safe, *because* a
connector next to a corridor square is always blank — the horizontal glyph
appears only between two joined wall squares, and an actor only ever stands
on corridor. If that were ever wrong the picture would silently lose a wall.
There is now a test that composes **12 real generated mazes** and asserts
that no non-blank cell of the wall layer is ever covered by an actor.

**A dot count that came out one short, and was right.** A test asserting
every dot in the field is drawn failed at 262 against 261. The missing one
was **the dot under the ghost** — SCORE-4 keeps it in the field, END-4
paints the ghost over it. The test now states that rule rather than counting
blindly, and asserts that the seed really does start the ghost on a dot, so
it cannot pass for the wrong reason.

## Seen, not just asserted

I composed a real generated game (seed 4) and read the picture. 30 rows,
every one exactly 40 characters, a 3-column margin on every maze row, the
double lines joining up, lone blocks where the generator left isolated
walls, and the player's motif at columns 17–19 for square 9:

```
 0|╔═══════╦═══════════════════════════╗   |
 1|║▗█▖▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║   |
...
14|║ ▪ ■ ▪ ╚═══════╣▐█▌║ ▪ ════════╣ ▪ ║   |
...
28|╚═══════════════════════════════════╝   |
29|<row 29 is WI-13's>                     |
```

It looks like the specimen. No window was involved: this is all value.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 489 tests — 489 passed, 0 failed, 0 skipped
```

That is with WI-8 and DEV-A's WI-13 both merged in. 44 of the 489 are new
here. Nothing in this branch opens a window or imports a toolkit.

## What the tests own

**The mapping:** square *c* at column 2c; square 18 at column 36; a
nineteenth square refused; 19 squares filling exactly 37 columns with a
3-column margin (contradiction C-1, asserted rather than restated).

**The picture:** a small hand-built maze composing to a known picture
character for character; moving the player one square moving it two columns;
the rows below a short maze blank; a maze too wide or too deep refused; a
wall layer of the wrong shape or width refused.

**The actors:** each occupying 2c−1 … 2c+1; covering the connector either
side; the two motifs differing in shape as well as colour (SCRN-5); the
motifs being the two the requirements specify.

**The draw order:** when the two share a square the ghost's glyph *and* the
ghost's colour are what appear, and the final picture of a loss shows the
ghost and not the player (END-4).

**The dots:** dim gold; an eaten square blank rather than dotted; a dot
under the ghost still in the field after composing (SCORE-4); composing
changing nothing about the state, and the same state twice giving the same
picture.

**Row 29:** exactly what was handed over, even for a maze as deep as the
picture allows — plus a test that **no status-line literal** (`score`,
`CAUGHT`, `CLEARED`, `q quits`, `arrows`) appears anywhere in the composer,
because the plan forbids it outside WI-13.

**The walls:** a test that no double-line glyph or lone block appears
anywhere in the composer's executable source, so WI-12 cannot quietly
acquire an opinion about WI-8's job.

## WI-13 landed too, and there is now one test for that seam

Merging `main` also brought the status line. The composer takes row 29 as a
value and I have added the one test I owe that join: **whatever
`status_row(score, outcome)` produces is what ends up on row 29**, unchanged,
for all three endings. *What it says* stays WI-13's — its literals are
asserted there and nowhere else, and the test that no status-line literal
appears anywhere in this file still passes.

## Deviations needing a ruling

**A maze must *fit* the picture rather than be exactly 19 × 29.** The plan's
test list asks for "a small hand-built maze composes to a known picture",
which a strict size check would make impossible. So `compose_frame` refuses
a maze too wide or too deep and accepts anything smaller, composing it into
the top-left. The real game always hands over 19 × 29 and there is a test
that it fills the 37 columns and 29 rows exactly. Flagging it because it is
a looser contract than the plan's wording implies.

## Nothing else is blocked on me

WI-15 can call `compose_frame(state, status_row)` today. It needs WI-13's
row 29 as a value and nothing else from this item.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
