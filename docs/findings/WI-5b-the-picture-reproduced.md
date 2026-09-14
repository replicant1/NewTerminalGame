# WI-5b — the specification's picture, reproduced from the model

**Item:** WI-5b, frame composition. **Lane:** DEV-B, iteration M2.
**Measured on:** `wi-5b-frame-composition` at `cc15248`, Python 3.9.6, standard library only.

**The frame builder reproduces the specification's own worked example exactly: all 29 maze rows,
1 073 cells of picture, 0 characters differing.** That is the single most useful measurement this item
produced, and this is what it took to get there and what it does and does not prove.

## The geometry, and the two numbers that matter

A maze square is two terminal columns wide, and neighbouring squares **share** the column between
them. So:

| | |
| --- | --- |
| Picture width | `2 × 19 − 1 = 37` columns |
| Right margin | `40 − 37 = 3` columns |
| Square `x` is drawn at | column `2x` — the even columns, 0 to 36 |
| Column `2x + 1` | the **joiner** between square `x` and square `x + 1` |

**37 + 3, not 38 + 2.** The architecture's MAZE-1 row had it as 19 × 2 = 38 of 40 columns, which the
technical lead corrected while planning. The picture settles it: its rows are 37 characters.

## The joiner rule, derived rather than guessed

Measured across all 518 joiner positions in the specification's picture:

| both squares wall? | what sits in column `2x + 1` | times |
| --- | --- | --- |
| yes | `═` | **122, no exceptions** |
| no | blank | **396** |
| no | `▐`, `▌`, `▗`, `▖` | **4 — every one a side column of an actor glyph** |

Four exceptions, and all four are the outer columns of the player and the ghost, which are three
columns wide and drawn last. So the rule is one line — **both wall gives the line, otherwise blank** —
and the actors are simply painted over it afterwards.

**No case analysis on which glyphs the two squares carry is needed.** Two adjacent wall squares always
join horizontally, because each is the other's east or west wall neighbour, so each glyph already has
an arm pointing at the other. That is WI-5a's joining-up property doing work a second time.

## The actors, measured

| | square | glyph | characters |
| --- | --- | --- | --- |
| Player | (10, **13**) | `▐█▌` | RIGHT HALF BLOCK, FULL BLOCK, LEFT HALF BLOCK |
| Ghost | (1, 27) | `▗█▖` | QUADRANT LOWER RIGHT, FULL BLOCK, QUADRANT LOWER LEFT |

Both centred on column `2x`, spanning `2x − 1` to `2x + 1`. **I read the player's row off the page as
12 and it is 13** — which is the argument for parsing the picture rather than transcribing it, made
for the second time on this project.

**SCRN-5 is met by both halves.** The outlines differ — half blocks against lower quadrants — and the
colours differ, bright yellow against pink. Either alone would leave a player who cannot use that
channel with nothing.

**The ghost at square 1 spans columns 1 to 3 and leaves column 0 — the border wall — untouched.** That
is the M0 ruling about `Frame.put` measured in the specification's own picture rather than reasoned
about: an actor stands only on squares 1 to 17, so its glyph spans columns 1 to 35 of 0 to 36 and
cannot run off either edge. No clipping is needed and none was added.

## The dot arithmetic, which cross-checks three requirements at once

The picture's even columns hold **262 dots and 2 full blocks**, and the maze has **264 corridor
squares**. Those numbers only agree if all three of these hold:

- **START-3** — every corridor square holds a dot except the player's. So the state has 263 dots.
- **SCORE-4** — the ghost's square keeps its dot. So one of the 263 is underneath the ghost.
- **END-4 / draw order** — the actors are drawn over what is beneath them. So 262 are visible.

263 − 1 covered = 262 visible, plus the two actor squares = 264. The picture is internally consistent
with all three, which is worth knowing before treating it as an authority.

## What the reproduction test does and does not prove

**It proves** that the wall glyphs, the joiner rule, the dot placement, the actor glyphs, the actor
centring, the draw order and the 37-column geometry are all simultaneously right, against a picture
drawn by a person before any of this code existed. A test written against my own understanding could
agree with a mistake I had made; this one cannot.

**It does not prove** anything about:

- **A dot that has been eaten.** The picture is a game at score 0. Whether an eaten dot disappears
  needs its own test and has one — in both directions, because a builder that painted a dot on every
  corridor square regardless would satisfy "a dot appears wherever there is one".
- **The two actors on the same square.** The picture has them far apart. END-4's whole point is what
  happens when they coincide, and that is tested separately — as is the converse, that the player
  still shows when they are apart, without which a builder that never drew the player would pass.
- **The frame being rebuilt rather than patched.** A single picture says nothing about the second one.
- **Anything visual.** Whether these characters exist in the player's font at a single advance width,
  and whether the colours are legible, remain human checks on WI-14b's list and are **not** recorded
  as verified anywhere.

## A hole found in this project's own guard

`PRESENTATION_MAY_IMPORT` in `tests/test_layering.py` — added by WI-5a, by me — listed the Domain and
the screen port but **not Presentation itself**, so a presentation module could not import a sibling.

It could not show in WI-5a, where Presentation had exactly one module and nothing to import from a
sibling. WI-5b's frame builder imports the wall-glyph table, and the rule failed on a case it should
always have allowed.

Worth recording for its shape rather than its size: **a guard written when a category has one member
cannot distinguish "this rule is right" from "this rule has never been exercised".** The same could be
said of `FORBIDDEN_IN_PRESENTATION` today. The fix was one entry, and the reason is written beside it
in the file so that the next person to widen it has to think rather than copy.
