# WI-16 — the look, seen

**Measured by:** DEV-B, run 6, on this machine, `/usr/bin/python3` (3.9.6,
Tk 8.5.9), under the conductor's screen gate. Eight windows opened, eight
reaped, no modal sheet raised.

This document records what a machine could establish about the look of the
game, and — just as importantly — **what it could not, and who has to answer
it**.

---

## 1. The headline: one question is still open and this document does not close it

**SCRN-3 — do the blue double lines actually join up into clean corners, tees
and crossings?**

**Unanswered.** It is the only requirement on this run that no measurement
can settle, and nothing in this document settles it.

The temptation, which I want to name because I am the person best placed to
give in to it: in WI-2 I measured that **all 113 glyphs the picture uses
share one advance width in Menlo**, at 14, 16, 18 and 20 point alike, with a
control showing that glyphs Menlo *lacks* fall back to visibly different
advances. That is a good measurement and it is not the answer. It proves the
glyphs land in the **right places**. Whether the strokes **meet** at the cell
boundary is a property of the glyph outlines, and the only instrument that
can read it is an eye. DEV-C reached the same conclusion independently from
the other side, in WI-8's glyph census.

Three developers have now declined to convert the spacing measurement into a
joining claim. This document declines too.

---

## 2. What *was* measured, on the real screen

Eight real windows, at four font sizes, painted through the real surface from
frames the real composer produced.

| | Result |
| --- | --- |
| Windows opened / reaped | **8 / 8** |
| `window_reaped` true | every one |
| Errors | none |
| Modal sheets raised | none |
| Titlebar read back | **`Terminal Game`**, all 8 times |
| Kinds of thing on the canvas | **`["text"]`**, all 8 times |

**That last row is SCRN-2 observed rather than argued.** Under candidate 2
"there are no images" is a rule rather than a property of the medium
(caution C5), and on a real screen, eight times over, nothing but characters
was ever drawn.

### The three views, as painted

| View | Canvas items |
| --- | --- |
| `game` — a real generated maze, real composer, real status line | 698 |
| `joinery` — every wall junction at once | 714 |
| `colours` — the five colours, labelled | 96 |

### The A4 size comparison

| Point size | Cell | Window | Painted | Reaped |
| --- | --- | --- | --- | --- |
| 14 | 8 × 16 | 320 × 480 | 698 | yes |
| **16 (current)** | **10 × 19** | **400 × 570** | 698 | yes |
| 18 | 11 × 21 | 440 × 630 | 698 | yes |
| 20 | 12 × 24 | 480 × 720 | 698 | yes |

---

## 3. The three questions, and exactly how to answer them

All three are **unanswered**. Each needs a person to look at a screen; none
needs anything built.

```
/usr/bin/python3 tools/the_look.py --seconds 8
```

Three windows, about 25 seconds in total, each closing itself. The tool
prints the three questions before it opens anything.

**1. SCRN-3 — do the double lines join up?** Look at the **second** window,
the `joinery` view. It is a lattice filling the whole window:

```
╔═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╗
║   ║   ║   ║   ║   ║   ║   ║   ║   ║
╠═══╬═══╬═══╬═══╬═══╬═══╬═══╬═══╬═══╣
```

Every junction WI-8 can produce is on that one screen — corners, tees,
straights, and the crossing `╬`, which **the specimen picture does not
contain and which nothing else on this project has ever put on a screen**.
*What to look for:* a hairline gap where two cells meet, or a stroke that
steps sideways instead of running straight. If the lattice looks like solid
continuous rules, the answer is yes.

**2. A4 — is the type large enough to read comfortably?** The first window is
the real game at the current 16pt. To answer by comparison rather than by
guess:

```
/usr/bin/python3 tools/the_look.py --view game --sizes 14,16,18,20 --seconds 5
```

Four windows in turn, same picture, four sizes. If the answer is not 16, the
change is **one constant** — `FONT_POINT_SIZE` in
`terminal_game/shell/grid_surface.py` — and the window size follows from it
automatically. The table in section 2 says what each size costs in pixels.

**3. A1 — does the titlebar read exactly *Terminal Game*?** Visible on all
three windows. **Tk reports the string back to us unchanged on every one of
the eight runs**, which is worth something but is *not* a person seeing a
titlebar: the reported name and the rendered titlebar are different things,
and under candidate 1 they were measured to differ. A glance settles it.

---

## 4. Whether the five colours can be told apart

**Partly measured, partly open.**

*Measured:* the five visible colours are five **different values** on the
surface — there is a test asserting it, so nobody can be shown two hues that
are secretly the same. Each is what the requirements name:

| Thing | Requirement | Colour |
| --- | --- | --- |
| walls | SCRN-3 | wall blue |
| dots | SCRN-4 | dim gold |
| player | SCRN-5 | bright yellow |
| ghost | SCRN-5 | pink |
| status line | SCRN-6 | cyan |

*Open:* whether they are **distinguishable to a person**, which is what
SCRN-5 actually asks. The third window, the `colours` view, exists for this:

```
  wall     ═════
  dot      ▪▪▪▪▪
  you      ▐█▌
  ghost    ▗█▖
  the two actors differ in shape
```

Each label is drawn in its own colour as well as the sample, because a hue
that reads as a clear solid block can still be unreadable as text. Row 29 is
the **real** status line from WI-13, so the cyan on show is the cyan the game
uses.

Note that SCRN-5 asks for the two actors to be told apart by colour **and by
outline**, and the outline half *is* settled: `▐█▌` and `▗█▖` are different
shapes, asserted in WI-12's tests. So even if the two hues were hard to tell
apart, the requirement is not wholly lost.

---

## 5. Window hygiene, as practised

The tool follows DEV-C's proven pattern from `tools/walking_skeleton.py`
rather than a second one of my own. Per window:

- the deadline is scheduled on the toolkit's own scheduler **before** the
  event loop is entered, so it never depends on anybody pressing anything;
- the reap is in a `finally`, so a failure still takes the window away;
- **the next view does not open until the last is confirmed gone**, and if a
  window is ever not reaped the run stops rather than opening another;
- only the handle captured at the moment of creation is ever acted on;
- `--seconds 0` and negative values are **refused at parse time**, so a
  window with no deadline cannot be asked for, let alone opened.

Runs were escalated deliberately — one window for two seconds first, to
confirm the mechanics and the reap, before asking the user's screen for
anything longer.

---

## 6. What this does not cover

- **Flicker at the ghost's cadence.** These views paint one static picture.
  The repaint cost is measured in `docs/findings/WI-2-cell-metrics.md`
  (0.68 ms median against a 143 ms budget) and the surface never clears, but
  flicker on a moving picture belongs to the finished game.
- **Anything about keys.** WI-16 is inside the pixels; the window and its
  keyboard are WI-17's.
