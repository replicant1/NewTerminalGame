# S-1 — toolkit feasibility: can Tcl/Tk 8.5 be tested headlessly, and what are the cell metrics?

**Measured** on 17 Sep 2026 between 01:34Z and 01:38Z, from the worktree
`.claude/worktrees/agent-ad9b18e196f2c349f`, on macOS 26.6.2, screen 1512 × 982 points.
Interpreter `/usr/bin/python3`, CPython **3.9.6**, `tkinter` **Tk 8.5 / Tcl 8.5**,
`tk windowingsystem` = `aqua`, `tk scaling` = 1.000750469043152.

These are facts about that machine at that moment. Anything you are about to depend on
closely, re-measure.

---

## The verdict

> **Yes. The Presentation layer can be tested headlessly on Tcl/Tk 8.5.**
> A Tk root can be constructed, driven and destroyed inside a test without any window
> reaching the user's screen. **Human item 5 of section 9 — consent to install a modern
> Tk — does not open.** Assumption **P8** holds in both of its halves.

There is one side effect the plan does not anticipate, and it is not a window: see
[The Dock tile](#the-dock-tile-the-one-thing-that-is-visible).

---

## 1. A Tk root that never reaches the screen

**The technique.** Call `withdraw()` on the root *before the first turn of the event
loop*. Tk defers mapping a toplevel to idle time, so a root withdrawn before any
`update()`, `update_idletasks()` or `mainloop()` never maps at all — it is not "shown and
then hidden", it is never shown.

```python
root = tkinter.Tk()
root.withdraw()          # must be the very next statement
root.update_idletasks()  # only now does the event loop run
```

**What was measured.** With the event loop pumped as far as it will go without blocking:

| Observation | After `withdraw()` | After `update_idletasks()` + `update()` |
|---|---|---|
| `root.state()` | `withdrawn` | `withdrawn` |
| `root.winfo_ismapped()` | `False` | `False` |
| `root.winfo_viewable()` | `False` | `False` |
| `root.winfo_exists()` | `True` | `True` |
| `root.winfo_geometry()` | — | `1x1+34+67` |

A child `Toplevel` withdrawn the same way behaves identically: `ismapped=False`,
`viewable=False`. Widgets can be created on it, packed, measured and destroyed.

**Confirmed from outside the process**, so the answer does not rest on Tk's own word.
`/usr/bin/lsappinfo` is shipped with macOS, needs no permission and raised no prompt:

- `lsappinfo front` returned `ASN:0x0-0x4f24f2` before the probe, during it and after it —
  **the frontmost application never changed**, so nothing stole focus from the person at
  the keyboard.

**Inside a virtual environment too.** A venv created with `/usr/bin/python3 -m venv` keeps
`tkinter` (3.9.6, Tk 8.5) and the same probe run from `venv/bin/python` reports
`withdrawn / False / False`. The suite command in plan section 1.2 is therefore safe.

### The Dock tile: the one thing that *is* visible

Constructing a Tk root — **even one that is withdrawn and never mapped** — registers the
process with Launch Services as a *foreground* application for as long as it lives:

```
asn: ASN:0x0-0x30d80d5-"Python"
     bundleID="com.apple.python3"
     pid = 96912  type="Foreground"  Version="3.9.6"  fileType="APPL"  Arch=ARM64
```

and it appears in `lsappinfo visibleProcessList` alongside the person's real applications:

```
Google_Chrome:  Terminal:  Finder:  Code:  Preview:  TextEdit:  MacDown:  Python:
```

**The control rules out the interpreter as the cause.** An identical process that holds
open for the same duration but never imports `tkinter` has **no Launch Services record at
all**. The registration is Tk's doing.

In practice this means a **"Python" tile appears in the Dock for the duration of any test
run that builds a Tk root**, and disappears when the process exits. It is not a window;
WI-5's and WI-16's bar — *"the default suite puts no window on the user's screen"* — is
still met, and `lsappinfo front` shows it never takes focus. But it is something a person
sitting at the screen will see, and nobody has agreed to it. **This is for a human** — see
section 5.

I found no way to suppress it from a plain script on Tk 8.5: the Dock tile is governed by
the application's activation policy, and Tk 8.5 exposes no way to set
`NSApplicationActivationPolicyAccessory`. I did not try to install anything.

---

## 2. The font, and why it has to be Menlo

**180 font families are visible to Tk.** `TkFixedFont` already resolves to **Menlo**.

| Candidate | Present? | Owns every glyph the game draws? |
|---|---|---|
| **Menlo** | yes | **yes — no substitution anywhere** |
| Monaco | yes | no — substitutes the whole box + block range to Menlo, and U+2592 comes out one pixel narrow |
| Courier New | yes | no — substitutes 24 block elements to Menlo |
| Andale Mono | yes | no — substitutes the same 24 |
| PT Mono | yes | no — substitutes the same 24 |
| SF Mono, Courier, Consolas, DejaVu Sans Mono | **absent** | — |

**Every glyph the game draws is present in Menlo at its native advance.** Checked with
both `font actual FONT -family CHAR` (Tk 8.5's per-character substitution query) and
`font measure`:

- the double-line box set **U+2550 – U+256C** — all 29, which covers all sixteen of WI-3's
  neighbour cases including the crossing `╬`;
- the block elements **U+2580 – U+259F** — including `█` U+2588, `▐` U+2590, `▌` U+258C
  (the player `▐█▌`) and `▗` U+2597, `▖` U+2596 (the ghost `▗█▖`);
- `■` U+25A0 (the lone wall square) and `▪` U+25AA (the dot);
- every character in the three status-line literals.

All of them report `actual family = Menlo` and all measure **exactly** `measure("M")`.

**The substitution test is not vacuous.** Characters Menlo genuinely lacks report a
different family and a different advance, so a "Menlo" answer means something:

| Character | `font actual -family` | advance (vs `M` = 10) |
|---|---|---|
| U+0915 Devanagari KA | Kohinoor Devanagari | 13 |
| U+4E2D CJK 中 | PingFang SC | 16 |
| U+0BF5 Tamil year sign | Tamil Sangam MN | 24 |
| U+E000 private use | Menlo *(Menlo has a PUA glyph)* | **18** — caught by the advance test, not the family test |

That last row is why **both** checks are worth keeping: family alone would have passed it.

---

## 3. Cell metrics, and the size ceiling nobody expected

### Per-glyph advance is uniform at every size

At **every** Menlo size from 8 to 36, every glyph listed above measures exactly
`measure("M")`. The double-line box characters and the block characters do **not** need a
special case: Tcl/Tk 8.5 gives them the same cell width as a letter. This is the half of
assumption P8 the technical lead was most worried about, and it holds.

### But a whole row only lines up at size 16 and below

`Font.measure()` returns whole pixels. At some sizes Tk's own string layout uses a
*fractional* advance, so a 40-character row drawn as one string is **not** 40 × the
per-character advance. Measured over `"M" * 40` and over a real specimen maze row:

| Menlo size | advance | linespace | 40 × 30 window | `measure(c*40)` = `40*measure(c)`? | worst drift over 40 cells |
|---|---|---|---|---|---|
| 8 | 5 | 9 | 200 × 270 | **yes** | 0 |
| 9 | 5 | 10 | 200 × 300 | **yes** | 0 |
| 10 | 6 | 11 | 240 × 330 | **yes** | 0 |
| 11 | 7 | 13 | 280 × 390 | **yes** | 0 |
| 12 | 7 | 14 | 280 × 420 | **yes** | 0 |
| 13 | 8 | 15 | 320 × 450 | **yes** | 0 |
| 14 | 8 | 16 | 320 × 480 | **yes** | 0 |
| 15 | 9 | 18 | 360 × 540 | **yes** | 0 |
| **16** | **10** | **19** | **400 × 570** | **yes** | **0** |
| 17 | 10 | 20 | 400 × 600 | no | 9 px |
| 18 | 11 | 21 | 440 × 630 | no | 7 px |
| 19 | 11 | 22 | 440 × 660 | no | 18 px |
| 20 | 12 | 24 | 480 × 720 | no | 2 px |
| 24 | 14 | 28 | 560 × 840 | no | 18 px |
| 30 | 18 | 35 | 720 × 1050 | no | 2 px |
| 36 | 22 | 41 | 880 × 1230 | no | 13 px |

*(sizes 21–23, 25–29 and 31–35 were all measured and are all `no`; the full scan is
reproducible from the script in section 6.)*

**Size 16 is the largest Menlo size with an exact integer cell grid.**

### Recommendation for WI-5 and WI-6

> **Menlo, size 16. Cell 10 × 19 pixels. A 40 × 30 window is 400 × 570 pixels.**

At that size a row placed cell by cell at `x = column * 10` and the same row drawn as a
single string land on identical pixels, so **WI-5's repaint strategy is not constrained by
the font** — it may draw per cell, per row, or only the changed cells, and get the same
picture. Above size 16 that stops being true and WI-5 would be forced into per-cell
placement.

Two cross-checks at size 16, from a canvas rather than from the font object:

- a single `═` drawn anchored `nw` at x = 0 has bbox `[-1, 0, 11, 19]`, and the same glyph
  at x = 10 has bbox `[9, 0, 21, 19]` — the canvas adds one pixel of margin either side, so
  the two cells **abut exactly** with no overlap and no gap;
- the specimen's own 37-character maze row measures 370 = 37 × 10, exactly.

**If a human later judges size 16 too small** (human item 3, assumption P4), the next sizes
up all break the exact grid. WI-5 should then place text per cell at `column * advance`
rather than per row, and WI-19 should re-read this table before picking the new constant.

---

## 4. What this settles, and what it does not

**Settled:**

- **P8, both halves.** A Tk root builds in a test without a window; the box-drawing and
  block glyphs share one cell width.
- Human item 5 of section 9 does not open. **Nothing was installed.**
- WI-5, WI-6, WI-7, WI-14 and WI-16 proceed exactly as the plan writes them.

**Not settled, and deliberately not guessed at:**

- **Whether the box-drawing glyphs *look* joined.** Every measurement here is about
  *advance* — the horizontal space a glyph claims. Whether Menlo's `═` ink actually spans
  the full 10 pixels, so that a run of them reads as one unbroken double line rather than a
  dashed one, cannot be seen without rasterising, and Tk 8.5 offers no canvas-to-image path
  and there is no PyObjC or PIL on this interpreter to do it another way. **The first
  chance to see this is WI-7's window; WI-17 should put it in front of a person.**
- **Whether 10 × 19 pixel type is comfortable to read.** Unchanged: that is human item 3.
- **Flicker-free repaint and caret suppression (SCRN-7).** Not in S-1's scope; WI-5 owns
  them. Nothing measured here makes them harder.

---

## 5. For the human (an addition to section 9)

**A "Python" tile appears in the Dock whenever the test suite runs.** Not a window, and it
never takes focus, but it is visible and it was not asked for.

*Steps:* run the test suite once the Presentation tests exist, and watch the Dock.
*A good answer is:* either "that is fine, it is a second or two" — in which case nothing
changes — or "no, I do not want that", in which case the Presentation tests need to be
marked so they are excluded by default, which costs WI-5 and WI-16 a marker and costs the
default suite its coverage of the surface. **Do not decide this on my behalf.**

---

## 6. Reproducing this

The probes were throwaway and live outside the repository, so they are recorded here
rather than committed. Each has a `SIGALRM` hard deadline, none contains a `mainloop`, and
none can block: plan section 1.5 in full.

```python
# The headless check, whole. Run with /usr/bin/python3.
import os, signal, sys
signal.signal(signal.SIGALRM, lambda s, f: os._exit(3))
signal.alarm(20)
import tkinter as tk
root = tk.Tk()
root.withdraw()                      # before the first event-loop turn
root.update_idletasks(); root.update()
print(root.state(), bool(root.winfo_ismapped()), bool(root.winfo_viewable()))
root.destroy(); signal.alarm(0)
# -> withdrawn False False
```

```python
# The cell-grid scan that produced the table in section 3.
import os, signal
signal.signal(signal.SIGALRM, lambda s, f: os._exit(3))
signal.alarm(60)
import tkinter as tk, tkinter.font as tkfont
GLYPHS = ["M", " ", "═", "║", "╔", "╗", "╚", "╝",
          "╠", "╣", "╦", "╩", "╬", "■", "▪",
          "█", "▐", "▌", "▗", "▖",
          "s", "c", "o", "r", "e", "0", "9", ",", "q", "!"]
root = tk.Tk(); root.withdraw(); root.update_idletasks()
for size in range(8, 37):
    f = tkfont.Font(root=root, family="Menlo", size=size)
    adv, lsp = f.measure("M"), f.metrics("linespace")
    uniform = all(f.measure(g) == adv for g in GLYPHS)
    exact = all(f.measure(g * 40) == 40 * adv for g in GLYPHS)
    print(size, adv, lsp, 40 * adv, 30 * lsp, uniform, exact)
root.destroy(); signal.alarm(0)
```

External confirmation, needing no permission and raising no prompt:

```
/usr/bin/lsappinfo front                     # before, during, after — must not change
/usr/bin/lsappinfo find pid=<child pid>      # the ASN, if Launch Services registered it
/usr/bin/lsappinfo visibleProcessList        # whether it claims a Dock tile
```

---

## 7. The test that should pin this, and where it belongs

The conclusions **can** be pinned headlessly, so per plan section 5 they should be. There
is no suite yet — WI-0 creates it, in parallel with this spike — so the test is **left to
WI-5**, which owns the cell-metrics responsibility and is the first item that needs it.
The conductor ruled it that way rather than have this spike race WI-0 over the package
layout. Recorded as a deviation in the S-1 PR summary.

What WI-5's test should assert, as consequences:

1. Building the surface's Tk root leaves it **not viewable** — `winfo_ismapped()` is false
   and `winfo_viewable()` is false — after the event loop has been pumped.
2. For every glyph in the game's alphabet, `measure(glyph) == measure("M")` **and**
   `font actual -family` is the chosen family, with at least one character the family
   lacks asserted to report a *different* family, so the test cannot pass vacuously.
3. `measure(glyph * 40) == 40 * measure(glyph)` for every glyph — the property that makes
   the chosen size safe, and the one that silently fails if the size constant is raised.
4. The cell metrics yield the claimed pixel size: `40 * advance` by `30 * linespace`.

Assertion 2's control character and assertion 3 are the two that stop this from being a
test that merely restates the code. Neither duplicates anything WI-6 owns: WI-6 asserts the
*window* is that size, which is the seam, not the metric.
