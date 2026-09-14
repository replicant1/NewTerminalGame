# WI-5b — frame composition

**Branch:** `wi-5b-frame-composition`
**Lane:** DEV-B, iteration M2
**Mode:** local — this file stands in for the pull request. Nothing was pushed; no `gh` was used; the branch is not merged.
**Suite:** `python3 -m unittest discover` from the repository root — **402 passed, 0 failed, 0 skipped** (8.1 s).
**Windows opened:** none. Pure presentation.

---

## What this branch is an integration of — read this before merging it

WI-5b depends on **WI-5a and WI-7**, neither of which is on `main`. This branch is the integration of
the two, and the technical lead asked for the exact record so it can check that merging those
dependencies into `main` one at a time produces the tree WI-5b was actually built and tested on.

| | |
| --- | --- |
| Branched from | **`wi-5a-wall-glyphs` at `a93cbd6`** |
| Merged into it | **`wi-7-game-state` at `af4c6d9`** |
| Merge commit | **`bc21558`** |
| **Resulting tree** | **`8dac164c2b291ac5b711023aaf72cfb60bbd5dff`** |
| Suite at that tree, before any WI-5b code | **352 passed, 0 failed, 0 skipped** — 299 from WI-5a plus 53 from WI-7, landing exactly |

The merge was measured clean with `git merge-tree --write-tree` twice beforehand — once when WI-5a
was at `7a2d678` and again after it moved to `a93cbd6` — and it was. The only file both touch is
`tests/test_layering.py`, where WI-5a adds `PRESENTATION_MAY_IMPORT` and `PresentationLayerTest` and
WI-7 adds `uses_global_random` and two `DomainPurityTest` methods, in different regions.

**If the tree you produce differs from `8dac164`, re-run WI-5b before merging it, not after.**

**One thing happened after that point:** `main` moved to `8c4e2ce` while this item was being written —
a monitor change touching only `orchestration/server.py` and `orchestration/static/index.html`. I
merged it in and re-ran the whole suite (402, unchanged), per the standing condition that the lead
merges what was tested rather than what was hoped. **Neither file is imported by the game or by the
suite**, so the integration tree above is still the one every line of WI-5b was built and run
against; the merge adds orchestration files beside it and nothing else.

---

## The one result worth leading with

**The frame builder reproduces the specification's own worked example exactly — all 29 maze rows,
1 073 cells of picture, 0 characters differing.**

The test builds the maze from the document's picture, places the player at (10, 13) and the ghost at
(1, 27), lays a dot on every corridor square but the player's, composes a frame, and compares it back
to the document line by line. It reads the document rather than a copy of it, so editing the picture
says the builder needs rechecking.

**That test cannot agree with a mistake this code also makes**, which is the whole reason for it. A
person drew that picture before any of this existed. It simultaneously pins the wall glyphs, the
joiner rule, the dot placement, the actor glyphs and their centring, the draw order and the
37-column geometry.

## The files

| File | What it is |
| --- | --- |
| `terminalgame/presentation/frame_builder.py` | `compose`, the four `draw_*` functions, `picture_rows`, `StatusLineTooWide`, and the geometry constants. |
| `tests/test_frame_builder.py` | 50 tests in ten classes. |
| `tests/test_layering.py` | **One line changed** — see below. |
| `docs/findings/WI-5b-the-picture-reproduced.md` | The geometry as measured, and what the reproduction does and does not prove. |
| `docs/progress/wi-5b-frame-composition.md` | The progress log. |

## The geometry, measured rather than assumed

Square `x` is drawn at **column `2x`**; the odd column `2x + 1` is the **joiner** between square `x`
and square `x + 1`; 19 squares occupy `2 × 19 − 1 = 37` columns and the remaining **3** are MAZE-1's
blank right margin. **37 + 3, not 38 + 2** — the correction the technical lead made while planning,
and the picture agrees with it.

The joiner rule came out of all 518 joiner positions in the picture:

| both squares wall? | column `2x + 1` | times |
| --- | --- | --- |
| yes | `═` | **122, no exceptions** |
| no | blank | **396** |
| no | `▐ ▌ ▗ ▖` | **4 — every one a side column of an actor glyph** |

So: both wall gives the line, otherwise blank, and the actors are painted over it afterwards. No case
analysis of which glyphs the two squares carry is needed, because two adjacent wall squares always
join horizontally — each is the other's east or west wall neighbour, so each glyph already has an arm
pointing at the other. That is WI-5a's joining-up property earning its keep a second time.

## Draw order, and every negative paired with its positive

Walls → joiners → dots → **player** → **ghost**. The ghost last is END-4, so a loss shows what
happened.

A frame test goes vacuous in a particular way: **most of these assertions are also true of a builder
that draws nothing.** So each is paired.

| The assertion | What would pass it vacuously | The pair |
| --- | --- | --- |
| on the same square the ghost shows | a builder that never draws the player | apart, the player still shows |
| a dot on every square that has one | a builder that paints a dot on every corridor square | and on **none** that does not — plus an eaten dot visibly changes the picture |
| the dot under the ghost is still in the state | a builder that deleted it and a state nobody re-read | when the ghost moves on, the dot is **visible again** |
| adjacent wall squares are joined | a frame with no joiners at all | there really are joins **and** really are gaps |
| no cell carries a colour outside the palette | a blank frame | all six named colours are actually used |

SCRN-5 is checked on **both** channels — distinct glyphs *and* distinct colours — because a test of
the outlines alone would pass a picture where both actors were the same colour, and a player who
cannot use that channel would have nothing left.

## Row 29 is a seam — and the plan's sequencing did not hold

**The plan expects WI-6 to have landed before WI-5b, and it has not.** §7 M2: *"WI-6 writes row 29 and
WI-5b writes rows 0 to 28 of the same frame… WI-6 lands first (day 8) so WI-5b composes against a
status row that already exists."* WI-6 has not been dispatched.

I proceeded on the plan's **division** rather than its **order**, which seemed the part that matters:
I compose rows 0 to 28 and leave row 29 to WI-6. `compose(state, status_line=None)` leaves it blank;
given a string it writes it at row 29 in `Colour.STATUS`, **exactly as given, leading space and all** —
what the line says, and whether it has a leading space, is STAT-1 to STAT-3's question and WI-6's to
answer. Nothing in this module needs to change when WI-6 arrives.

Tested from both sides: the maze never writes into row 29, and a status line never writes above it.

**Flagging the sequencing rather than silently absorbing it** — if the technical lead would rather
WI-5b waited for WI-6, this is the moment to say so.

## `tests/test_layering.py` — one line, and it was my own bug

I touched it. Recording that explicitly, per EDIT 11.

`PRESENTATION_MAY_IMPORT`, which **I added in WI-5a**, listed the Domain and the screen port but **not
Presentation itself** — so a presentation module could not import a sibling. It could not show in
WI-5a, where the layer had exactly one module and nothing to import from a sibling. WI-5b's frame
builder imports the wall-glyph table, and the rule failed on a case it should always have allowed.

Widened by one entry, with the reason written beside it in the file. **The hole was in the guard, not
in the code it guards**, and it is worth its shape rather than its size: *a guard written when a
category has one member cannot distinguish "this rule is right" from "this rule has never been
exercised"*. The same could be said of `FORBIDDEN_IN_PRESENTATION` today.

**No module list was edited.** `frame_builder.py` is swept by `presentation_files()` automatically —
the same choice DEV-A made for `player.py` and I made for `ghost_policy.py`, and the equivalent
assertions live in this item's own test file.

## The four settled things, honoured

1. **`Frame.put` still raises; no clipping and no `put_clipped` was added.** Checked rather than
   trusted: over 20 generated mazes, every corridor square's glyph span lies inside columns 0 to 36.
   The specification's own picture shows the case — the ghost at square 1 spans columns 1 to 3 and
   leaves the border wall in column 0 intact. **No counter-case was found.**
2. **37 + 3**, pinned by a test naming the correction.
3. **Presentation imports the port's value vocabulary** — `Colour`, `Frame`, `Cell`, `BLANK`. Nothing
   that acts or remembers.
4. **Ghost after player**, with the pairing described above.

And the trap I set for myself in WI-5a: `draw_maze` asks **`joins_up_with`**, not `maze.is_wall`.
WI-5b is the item that would have been tempted, and the docstring that says not to unify them was
written for this moment.

## Deviations, for a ruling

**1. `compose` takes an optional `status_line`.** The plan describes WI-5b as composing the whole
40 × 30 frame but gives row 29 to WI-6. This is the seam that lets both be true; it is additive and
WI-6 need not use it if it would rather own assembly.

**2. `StatusLineTooWide` is raised for a line wider than the window.** Applying §11.8 with EDIT 12's
test — *name the requirement the input defeats*: a 41-column status line defeats SCRN-1, which gives
it exactly one row of a 40-column window. There is nowhere to put it, so this is the "impossible"
case rather than the "vacuous" one. The boundary is tested: exactly 40 columns is accepted.

**3. `picture_rows(frame)` is public** — the 29 maze rows with the margin trimmed, for reading a
failure. It exists because comparing against the specification's 37-column picture needs it.

## Contradictions found

**One, and it is a sequencing contradiction rather than a logical one:** the plan states WI-6 lands
before WI-5b and it has not, which the plan's own "do the two lanes overlap?" paragraph anticipates
the consequences of. Handled by the seam above; raised rather than absorbed.

Nothing in the requirements conflicted. SCRN-1, SCRN-2, SCRN-4, SCRN-5, SCRN-7, MAZE-1, END-4 and
SCORE-4 are mutually consistent and all are met, and the specification's picture is consistent with
all three of START-3, SCORE-4 and the draw order at once — its 262 visible dots plus 2 actor squares
being exactly its 264 corridor squares.

## What needs a human

Two, both already on WI-14b's list, **neither recorded as verified**:

1. **Do these characters exist in the launcher's font at a single advance width?** The frame now uses
   `═ ║ ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬ ■` for walls, `▪` for dots, `▐ █ ▌` for the player and `▗ █ ▖` for the
   ghost. A substituted glyph at a different width shears the picture. Only the real window can
   answer; a pseudo-terminal cannot.
2. **Are the five colours distinguishable to a person?** Blue walls, dim gold dots, bright yellow
   player, pink ghost, cyan status — on black. SCRN-4's "dim gold" is dim yellow and SCRN-5's "pink"
   is bold magenta, both substitutions ruled acceptable in M0 and both still human checks.

**No window was opened and nothing touched the desktop.**

## Commits

| | |
| --- | --- |
| `bc21558` | WI-5b: merge wi-7-game-state into wi-5a-wall-glyphs to start from |
| `cc15248` | WI-5b: compose the whole picture, and reproduce the specification's exactly |
| *(merge)* | WI-5b: merge main, which moved during the item |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
