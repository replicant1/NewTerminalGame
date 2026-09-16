# WI-2 — The character grid surface

**Developer:** DEV-B · **Branch:** `r6/wi-2-grid-surface` · **Base:** `main`

The one thing that turns a frame value into pixels. It measures the
fixed-width font's cell metrics, reports how many pixels 40 x 30 cells need
(which is what makes WIN-2 true), paints every cell at its own computed
position on a black ground in the colour the cell says, shows no caret, and
repaints by difference so there is never a half-built picture on screen.

## On the stacking

The plan stacks WI-2 on `r6/wi-1-picture-value` so that DEV-B need not wait
for WI-1 to merge. **WI-1 merged first (PR #23), so the stack collapsed**:
this branch is cut from a tree identical to `main` and its PR targets `main`
directly. There is nothing to retarget later.

## What is in it

| File | What it is |
| --- | --- |
| `terminal_game/shell/__init__.py` | The shell layer, and the WI-2 / WI-3 boundary written where both of us will meet it |
| `terminal_game/shell/grid_surface.py` | The surface, the geometry, the palette, the font checks. **Names no toolkit.** |
| `terminal_game/shell/tk_grid.py` | The Tk binding — the only module here that imports the toolkit, and it holds no decisions |
| `tests/doubles.py` | `RecordingCanvas`, `FakeFontProbe`, and the picture-reconstruction helpers |
| `tests/test_grid_surface.py` | 57 tests, none of which construct a toolkit object |
| `docs/findings/WI-2-cell-metrics.md` | The measurement the whole of candidate 2 rests on |

## The design

**Split so that the suite never touches the toolkit.** `grid_surface.py`
takes its canvas as a collaborator and imports nothing but the standard
library and the frame value; `tk_grid.py` is forty lines of Tk and has no
decisions in it. Every test in this branch runs against a recording double.
Nothing here can open a window even by mistake.

**Repaint is a difference, not a redraw.** The surface remembers the frame it
last painted and touches only the cells that differ. Nothing is ever cleared,
so there is no moment at which the window server can catch a blank or
half-built picture — that is the whole of the SCRN-7 story, and the numbers
are below.

**Each cell is drawn at its own computed position**, anchored north-west at
`(column * width, row * height)`, never as a row of text. This is the
mitigation the plan asks for from the start, and it costs nothing.

**The font is pinned and a substitution is fatal** — see the finding, because
this one nearly bites.

## Measurements — the important ones

Everything here was run on this machine. **No window was ever mapped**: the
measuring scripts withdrew their root before the event loop could be entered,
entered no mainloop, and exited on their own.

### Menlo 16pt is 10 x 19, so the window is 400 x 570

| Point size | Cell | Window |
| --- | --- | --- |
| 14 | 8 x 16 | 320 x 480 |
| **16 (chosen)** | **10 x 19** | **400 x 570** |
| 18 | 11 x 21 | 440 x 630 |
| 20 | 12 x 24 | 480 x 720 |

### Tk's own `TkFixedFont` is not fixed width — this is the finding to read

On this machine `TkFixedFont` resolves to `.AppleSystemUIFont`, reports
`fixed = 0`, and has **six different advance widths** across the glyphs this
game draws. A surface built on it would look entirely reasonable in code and
produce a window of the wrong size with walls that do not line up. So
`measure_cell_metrics` refuses three ways — family absent, family substituted,
family not uniform across all 113 glyphs we draw — and each raises rather than
proceeding. Verified against the real toolkit: a missing family raises
`FontNotAvailable`, `Helvetica` raises `FontNotFixedWidth`.

### The box-drawing glyphs are fine, and it is not a fallback coincidence

All **113** characters the picture can contain — 95 printable ASCII, the 11
double-line box glyphs, the dot, the lone block, and the five actor glyphs —
measure the **same advance** in Menlo at 14, 16, 18 and 20pt alike. Glyphs
Menlo does *not* have fall back to visibly different widths (CJK 16px, emoji
21px, private-use 18px, against our 10px), so the uniformity is Menlo's own
coverage. **The architecture's stated candidate-2 glyph-alignment risk is
retired for Menlo, as far as advance width goes.** Whether the strokes *meet*
is about glyph shapes, not metrics, and is WI-16's.

### Repaint cost, on the real canvas

| Measured | Result |
| --- | --- |
| Items for a full picture | 696, **all of kind `text`** |
| Full first paint | 5.6 ms |
| Repaint after one player move | median **0.68 ms**, worst 0.71 ms over 20 |
| Tick budget at ~7 frames a second | 143 ms |
| Share of the budget | **~0.5 %** |

The plan budgets up to two extra days in WI-2 for a flickering repaint. **I do
not expect to need them** — but nobody has looked at a mapped window yet, and
flicker is a property of a mapped window. The measurement says the work is
0.5 % of a tick and that nothing is ever cleared; it does not say the window
looks right.

## The WI-2 / WI-3 boundary — DEV-C, this is the call

The plan says WI-3 owns the window, the timer and key delivery; WI-2 owns
everything inside the pixels, and the two of us agree the shape of the one
call between them. DEV-C had not pushed a branch when this was written, so
here is what WI-2 offers, and it is easy to change if DEV-C wants it
differently:

```python
from terminal_game.shell.tk_grid import create_surface

surface = create_surface(root)        # raises SurfaceFontError if the font
                                      # is missing, substituted or not fixed
width, height = surface.pixel_size()  # -> PixelSize(400, 570)
root.geometry("%dx%d+%d+%d" % (width, height, x, y))
surface.canvas.pack()                 # the window owner places it; the
                                      # surface does not know where it sits
surface.paint(frame)                  # the only game-facing call
```

Three things that are deliberately **not** in that list, because they are
DEV-C's: the surface never creates a window, never reads a clock or starts a
timer, and never binds or looks at a key event. `create_surface(master)` takes
the master it is given and creates only a `Canvas` inside it.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 104 tests — 104 passed, 0 failed, 0 skipped
```

57 of those are new in this branch. **None of them constructs a toolkit
object.** `grid_surface.py` does not import `tkinter` at all, and the tests
drive it through `tests/doubles.RecordingCanvas`.

## What the tests own

- **Pixel size is the metrics multiplied out**, at four different metrics, and
  a bigger font gives a bigger window. The last cell's bottom-right corner is
  exactly the window's.
- **Painting reconstructs the picture.** `assert_surface_shows` reads every
  live canvas item back, maps its pixel position to a cell and its fill back
  to a named colour, rebuilds a `Frame` and compares it **as text**, then
  compares the colours. It is not a count of calls. Two items in one cell, a
  position that is not a cell origin, or a colour not in the palette each fail
  loudly rather than being skipped.
- **One placement per non-blank cell** (696 of the specimen's 1,200) and none
  for a blank one.
- **Nothing but characters is ever drawn** — `kinds_drawn() == {"text"}` — and
  the recording double is shown to *notice* an image, a rectangle and a caret,
  so the guard cannot pass vacuously.
- **Repainting an unchanged frame costs no drawing at all**, and moving the
  player touches exactly the five cells that changed.
- **A missing, substituted or non-fixed-width font raises**, including
  separate cases for a wall glyph, the block glyph and the dot being an odd
  width — which is what pins those glyphs into the required set.

Two fixtures assert their own significance in `setUp` (696 non-blank cells in
five colours; exactly five differing cells between the two player positions),
so they cannot quietly become empty and leave the tests asserting nothing.

## Deviations, offered for a ruling

1. **`tk_grid.create_surface` has no automated test.** Exercising it needs a
   live toolkit interpreter, and the plan forbids the suite constructing one.
   I verified it by hand instead — driving the real Tk canvas with a withdrawn
   root — and the numbers are in the finding. It is exercised for real by
   WI-4 and looked at in WI-16. Flagging it rather than quietly leaving a gap.
2. **`insertwidth=0` as the no-caret mechanism.** A canvas shows a caret only
   when an item has focus, which this surface never grants; the zero width is
   belt and braces so a later change cannot produce one. Asserted as
   configuration, and the double records `focus`/`icursor`/`insert` so a test
   can show none happen.
3. **Palette values are mine and provisional.** WI-16 settles them by eye. The
   test that the six are distinct will still hold whatever they become.

## What needs a human

1. **Is Menlo 16pt, in a 400 x 570 window, large enough to read comfortably?**
   (Assumption **A4**.) One constant; 18pt is 440 x 630, 20pt is 480 x 720.
2. **Do the double-line box glyphs join up cleanly at 16pt** — do the strokes
   meet, or is there a hairline between cells? Metrics say they will be in the
   right places; shape is a different question.
3. **Does it flicker on a mapped window at seven frames a second?**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
