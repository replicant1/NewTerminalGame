# WI-5 — the character grid surface

Turns a 40 × 30 field of glyph-and-colour into pixels. Plan section 5, iteration M0,
lane C. Depends on WI-0 and S-1, both merged.

## What is here

Four modules. **Three are pure** — no toolkit, no clock, no filesystem — and one names
the toolkit, and it is the one `tools.layer_rule.PAINTING_MODULE` was already pointing at,
so **no constant in WI-0 had to change**.

| Module | |
|---|---|
| `terminal_game/presentation/metrics.py` | WIN-2 as arithmetic: a 40 × 30 grid of a measured cell is a pixel rectangle, plus where each cell sits |
| `terminal_game/presentation/palette.py` | The six colours the specification names, as `#rrggbb` |
| `terminal_game/presentation/field.py` | The 40 × 30 field of glyph-and-colour — the data WI-4 and WI-12 will produce |
| `terminal_game/presentation/surface.py` | The painter. **The only module in Presentation that names the toolkit** |

## The four things section 5 asks WI-5 to establish

**WIN-2's pixel size is derived, never asserted.** The surface measures the real font at
construction and computes the window from what it finds. `Menlo 16 → advance 10,
linespace 19 → 400 × 570`, which I measured myself on a withdrawn root before writing
anything, independently confirming S-1. `MEASURED_MENLO_16` records the expected answer so
a **substitution shows up as a disagreement** rather than as a window that is quietly the
wrong size — `metrics_match_measurement()` is how a caller asks.

**SCRN-7, the flicker half.** Flicker is a picture torn down and rebuilt. This surface
never tears down: it creates one rectangle and one text item per cell at construction —
2400 items — and thereafter only reconfigures them, so the item identifiers are fixed for
its life. `present()` does the whole frame's reconfiguration and then asks the toolkit to
draw **once**. That is "composed off-screen and presented once", literally.

**SCRN-7, the caret half.** The canvas takes `takefocus=0`, holds no focused item, has
`insertwidth=0`, and the surface creates no widget that edits text — it creates exactly one
widget and it is a `Canvas`. `caret_is_impossible()` asks all three at once.

**SCRN-2.** There is no method here that draws anything. The only route to the picture is
`present(field)`, a field holds only `Cell`s, and a `Cell` is exactly one character and two
colours — so there is nothing for an image to travel in. `item_types()` reads back what is
actually on the canvas and it is only ever `{"text", "rectangle"}`.

**The default suite puts no window on the user's screen.** `tests/conftest.py` withdraws
the root before the first turn of the event loop, S-1's measured technique, and
`tests/test_surface.py` asserts it held rather than taking it on trust: `state() ==
"withdrawn"`, `winfo_ismapped()` false, `winfo_viewable()` false, checked again after
building a surface and again after painting a frame.

## `update()` is never called, and that is load-bearing

`root.update()` **blocks forever** on Tcl/Tk 8.5 under macOS 26 once the window is mapped —
my own S-2 measurement, bisected with `faulthandler` and pinned at
`tkinter/__init__.py:1314`. The surface calls `update_idletasks()` and never `update()`.
That is the right call regardless: it flushes the pending redraw without reprocessing the
event queue, so a repaint cannot re-enter the game through a key event arriving mid-frame.

**WI-6 inherits this**, as the item that maps the window.

## The repaint strategy, and why (caution C-5 leaves it to WI-5)

Only the cells that differ from the last frame are touched. **Measured on a withdrawn root
before deciding:**

| | |
|---|---|
| Build 2400 items | 11.5 ms, once |
| Full repaint, all 1200 cells | **7.3 ms** |
| A typical turn, 12 cells changed | **0.092 ms** |
| Tick budget (GHOST-1, P6) | 143 ms |

So a full repaint would already fit in 5% of the budget: **the diffing is not for speed.**
It is there for two better reasons. It keeps the item set fixed, which is the actual
mechanism that stops flicker. And it is **not** the dirty-*region* rendering C-5 warns
about — every item permanently owns exactly one cell and is always set to that cell's
current content, so there is no region that can be missed.

## A test I corrected, and a doubt I am recording

Two tests I wrote first were **weaker than their names claimed**, and I fixed them rather
than leaving them: `test_nothing_is_ever_created_or_destroyed_by_a_repaint` and
`test_the_canvas_never_empties_between_frames` both counted canvas items — but a
delete-and-recreate painter puts the *same number* back, so neither caught the thing it
named. They are replaced by one test comparing item **identity** across a full-to-blank
transition, which does. A third is renamed to what it actually asserts.

**The doubt, recorded rather than papered over:** whether the painter touches *only* the
changed cells is not observable from outside, because the picture is identical either way.
Everything that matters is pinned — the picture always equals the field, no cell is missed,
the ids never change — but the diffing itself is a performance property. I did not add spy
machinery to count reconfigurations, because a diff bug that yields the *right* picture is
not a defect anyone would notice. Say so if you would rather have the spy.

## A test that was missing, now written

S-1 measured that every glyph the game draws shares one cell width and recorded it in a
finding — **nothing re-ran it**. That belongs to the cell-metrics responsibility, which is
WI-5's, so it is now three tests: every one of WI-3's sixteen wall glyphs, every actor and
dot glyph, and a guard that the cell width is not zero so the first two cannot pass
vacuously.

## The seam for WI-4 and WI-12

`Field` is the type; **WI-4 and WI-12 produce instances of it.** WI-4 owns rows 0–28 and
the assembly, WI-12 owns row 29, exactly as section 7 says. `Field.write(column, row, text,
colour)` is there for a run of glyphs or a status line, and `Field.row_text(row)` lets both
of their tests assert an exact string without knowing what a cell is. If either wants the
seam shaped differently, that is a conversation between us and not an escalation.

## Suite state

```
.venv/bin/python -m pytest -q          →  263 passed, 0 failed, 0 skipped
```

Run from the repository root, `.venv` built from `/usr/bin/python3` 3.9.6 with pytest
8.4.2. Baseline on `main` when this branch was cut was **81 passed**, so WI-5 adds **182**.
`lsappinfo visibleApplicationCount` was 7 before and after: no window reached the screen.

## What needs a human

**S-1's Dock-tile item now bites, and this is the item that makes it real.** Constructing a
Tk root — even a withdrawn one that never maps — registers a process with the window
server, and a "Python" tile appears in the Dock for the second the suite runs. The default
suite now does that on every run, because the surface tests are in it. *Steps:* run
`.venv/bin/python -m pytest -q` and watch the Dock. *A good answer is* either "fine, it is
a second" — nothing changes — or "no", in which case the surface tests need the
`needs_window` marker and the default suite loses its coverage of the painter. **Not mine
to decide.**

**Whether the box-drawing glyphs *look* joined is still unanswered**, and nothing here
changes that. Every measurement in this PR is about *advance* — the space a glyph claims —
not about ink. Whether a run of `═` reads as one unbroken double line is first visible at
WI-7 and belongs in WI-17's pack.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
