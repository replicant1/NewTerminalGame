# WI-2 — cell metrics, and what the whole of candidate 2 rests on

**Measured by:** DEV-B, run 6, on this machine, with `/usr/bin/python3`
(3.9.6, Tk 8.5.9). Everything below was run, not reasoned about. No window was
mapped: every measuring script withdrew its root before the event loop could
be entered, entered no mainloop, and exited on its own.

Candidate 2 derives "40 characters wide and 30 rows deep" from font metrics
rather than setting it as a property. This document is that derivation.

---

## 1. The font, and why it is pinned by name

| Measured | Result |
| --- | --- |
| Tk patchlevel | **8.5.9** |
| Font families available | **180** |
| Fixed-width families present | Menlo, Monaco, Courier New, Andale Mono, PT Mono |
| **Chosen** | **Menlo** |

### Menlo's cell, at four sizes

| Point size | Advance (px) | Linespace (px) | 40 x 30 window |
| --- | --- | --- | --- |
| 14 | 8 | 16 | 320 x 480 |
| **16** | **10** | **19** | **400 x 570** |
| 18 | 11 | 21 | 440 x 630 |
| 20 | 12 | 24 | 480 x 720 |

**Chosen: Menlo 16pt — a cell of 10 x 19 pixels and a window of 400 x 570.**
That size is **assumption A4** and it is one named constant,
`FONT_POINT_SIZE` in `terminal_game/shell/grid_surface.py`. Only a person can
say whether it is comfortable to read; see section 5.

---

## 2. The finding that matters most: Tk's own "fixed font" is not fixed

`TkFixedFont` is the toolkit's named alias for a fixed-width font. On this
machine it resolves to `.AppleSystemUIFont`, which is **proportional**:

| Font asked for | Resolved to | `metrics("fixed")` | Distinct advances over our glyphs |
| --- | --- | --- | --- |
| `Menlo` | `Menlo` | 1 | **1** (10px) |
| `TkFixedFont` | `.AppleSystemUIFont` | **0** | **6** (4, 10, 14, 15, 16, 18 px at 16pt) |

A surface built on `TkFixedFont` would have looked entirely reasonable in
code, produced a window of the wrong size, and drawn a maze whose walls did
not line up. **This is precisely the silent substitution the plan warns about
in section 1**, and it is why `measure_cell_metrics` refuses three separate
ways rather than trusting the toolkit:

1. the family is not installed → `FontNotAvailable`;
2. the toolkit resolved it to a different family → `FontSubstituted`;
3. the family does not give **every glyph this game draws** the same advance →
   `FontNotFixedWidth`.

Verified against the real toolkit: a family that does not exist raises
`FontNotAvailable`; asking for `Helvetica` raises `FontNotFixedWidth`. Neither
substitutes and neither proceeds.

---

## 3. Do the box-drawing and block glyphs render at the right advance width?

**Yes — this was the open question, and the answer is unambiguous.**

Every one of the **113 characters** the picture can contain — the 95 printable
ASCII characters of the status line, the 11 double-line box glyphs
`═ ║ ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬`, the dot `▪`, the lone wall square `■`, the player's
`▐ █ ▌` and the ghost's `▗ █ ▖` — measures **exactly the same advance** in
Menlo, at 14, 16, 18 and 20 point alike. At 16pt that is 10 pixels for all
113, with no exceptions.

**And the uniformity is Menlo's own, not a coincidence of font fallback.**
Glyphs Menlo does not contain fall back to visibly different advances:

| Probe | Advance at Menlo 16pt |
| --- | --- |
| Any of our 113 glyphs | **10 px** |
| CJK `中` (not in Menlo) | 16 px |
| Emoji `😀` (not in Menlo) | 21 px |
| Private-use `U+E000` (nowhere) | 18 px |

If the box glyphs were being substituted from another font they would measure
16, 18 or 21 like the others do. They measure 10. Menlo has them.

**The architecture's stated candidate-2 risk — "the box-drawing glyphs do not
align at the chosen font size, so the walls do not join up" — is retired for
Menlo by measurement, as far as advance width is concerned.** What remains is
whether the *ink* of the double-line glyphs meets cleanly at the cell
boundary, which is a question about the shapes and not the metrics, and only
an eye can answer it. That is WI-16's.

---

## 4. Repaint cost, and the flicker risk

Measured on the **real** Tk canvas (root withdrawn, never mapped):

| Measured | Result |
| --- | --- |
| Canvas items for a full picture | **696** (the non-blank cells of the specimen) |
| Kinds of item on the canvas | **`{'text'}`** and nothing else |
| Full first paint | **5.6 ms** |
| Repaint after the player moves one square | **median 0.68 ms**, worst 0.71 ms over 20 |
| Tick budget at the ghost's ~7 frames a second | **143 ms** |
| Share of the budget a move costs | **~0.5 %** |

The surface repaints by **difference**, not by redraw. It remembers the frame
it last painted and touches only the cells that differ: a player moving one
square is five cells (the three-column motif shifts two columns), so five
`itemconfigure` calls and nothing else. Nothing is ever cleared, so there is
no moment at which the window holds a blank or half-built picture.

**The plan budgets up to two extra days in WI-2 for a repaint that flickers. I
do not expect to need them** — but nobody has looked at a mapped window yet,
and flicker is a property of a mapped window. The measurement says the work
is 0.5 % of a tick and that there is no clear-then-redraw; it does not say the
window looks right. **That confirmation is WI-4's and WI-16's, and it needs
eyes.**

---

## 5. What still needs a human

1. **Is Menlo 16pt, in a 400 x 570 window, large enough to read comfortably?**
   (Assumption **A4**.) It is one constant, `FONT_POINT_SIZE`; 18pt gives
   440 x 630 and 20pt gives 480 x 720 if the answer is no.
2. **Do the double-line box glyphs join up cleanly at 16pt, or is there a
   hairline gap between cells?** The advances are uniform, so they will be in
   the right places; whether the strokes meet is about the glyph shapes.
3. **Does the picture flicker at seven frames a second on a mapped window?**

---

## 6. How to reproduce any of this

Every number above came from a short script that creates a Tk root,
**withdraws it immediately** so it is never mapped, measures, and destroys the
root. There is no mainloop and nothing to reap. The suite itself never does
any of this: `/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"`
constructs no toolkit object at all, because
`terminal_game/shell/grid_surface.py` names no toolkit and the tests drive it
through the recording double in `tests/doubles.py`.
