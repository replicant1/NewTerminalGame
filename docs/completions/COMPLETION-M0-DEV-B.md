# M0 — DEV-B's lane, complete

**Developer:** DEV-B · **Iteration:** M0, *the two hard things proved* ·
**Mode:** non-local, real pull requests, merged by me

DEV-B's M0 lane is WI-1 (1 day) and WI-2 (3 days). Both are built, merged, and
green on `main`.

---

## What landed

| Item | Branch | PR | State |
| --- | --- | --- | --- |
| **WI-1** — the picture as a value | `r6/wi-1-picture-value` | [#23](https://github.com/replicant1/NewTerminalGame/pull/23) | **merged** |
| **WI-2** — the character grid surface | `r6/wi-2-grid-surface` | [#26](https://github.com/replicant1/NewTerminalGame/pull/26) | **merged** |

The plan stacks WI-2 on WI-1 so DEV-B need not wait. **WI-1 merged first, so
the stack collapsed**: WI-2 was cut from a tree identical to `main`, its PR
targeted `main` from the start, and there was nothing to retarget.

### The code

| File | |
| --- | --- |
| `terminal_game/presentation/frame.py` | `Colour`, `Cell`, `Frame`, `FrameBuilder`, and the measured geometry |
| `terminal_game/shell/grid_surface.py` | The surface, the geometry, the palette, the font checks. Names no toolkit |
| `terminal_game/shell/tk_grid.py` | The Tk binding — small, and holds no decisions |
| `tests/specimen.py`, `tests/doubles.py` | The specimen picture as data; the recording canvas and fake font probe |
| `tests/test_frame.py`, `tests/test_grid_surface.py` | 47 + 59 tests |
| `docs/findings/WI-2-cell-metrics.md` | The measurement the whole of candidate 2 rests on |

---

## Suite, as left

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 228 tests in 3.4s

OK
```

**228 passed, 0 failed, 0 skipped**, on `main` with WI-1, WI-2, WI-3, WI-5 and
the three naming follow-ups all landed. 106 of the 228 are DEV-B's.

No test in DEV-B's lane constructs a toolkit window, and neither
`frame.py` nor `grid_surface.py` imports a toolkit at all.

---

## The three measurements worth keeping

All taken on this machine with `/usr/bin/python3` (3.9.6, Tk 8.5.9). **No
window was ever mapped**: every measuring script withdrew its root before the
event loop could be entered and destroyed it afterwards.

**1. The window is 400 x 570 pixels.** Menlo at 16pt measures 10 x 19 pixels a
cell, so 40 x 30 cells come to 400 x 570. The point size is **assumption A4**
and is one named constant.

**2. Tk's own `TkFixedFont` is not fixed width here.** It resolves to
`.AppleSystemUIFont`, reports `fixed = 0`, and has **six** distinct advance
widths across the glyphs this game draws. This is exactly the silent
substitution that would have changed the size of the window while looking
entirely reasonable in code, and it is why `measure_cell_metrics` refuses
three separate ways rather than trusting the toolkit.

**3. The box-drawing glyphs are the right width, and it is not a fallback
coincidence.** All 113 characters the picture can contain measure the same
advance in Menlo at 14, 16, 18 and 20pt. Glyphs Menlo does *not* have fall
back to 16, 18 and 21 px against our 10, so the uniformity is Menlo's own
coverage. **The architecture's stated candidate-2 glyph-alignment risk is
retired for advance width.** Whether the strokes *meet* is a question about
shapes, and is WI-16's.

### And the risk the plan budgeted two days for

| Measured on the real canvas | |
| --- | --- |
| Full first paint | 5.6 ms, 696 items, all of kind `text` |
| Repaint after one player move | median 0.68 ms |
| Tick budget at ~7 frames a second | 143 ms |

The surface repaints by **difference**: it remembers the last frame and
touches only the cells that changed, so nothing is ever cleared and there is
no moment holding a half-built picture. **I do not expect to need the two
extra days** — but nobody has looked at a mapped window, and flicker is a
property of a mapped window.

---

## What was settled with the other developers, not escalated

**With DEV-A — the root package name.** WI-1 and WI-5 were built at the same
time from an empty tree and picked `terminal_game/` and `terminalgame/`.
DEV-A resolved it in WI-5a by conforming to WI-1's spelling, since WI-1 landed
first. Nothing of DEV-B's changed.

**With DEV-C — the WI-2 / WI-3 boundary**, settled against WI-3 as landed
rather than guessed at, and recorded on
[PR #25](https://github.com/replicant1/NewTerminalGame/pull/25#issuecomment-5692155351):

1. **`terminal_game/shell/__init__.py` conflicted (add/add).** Combined both
   docstrings, and corrected the one substantive claim: DEV-C's said only
   `tk_toolkit` names the toolkit, which stopped being true when `tk_grid`
   landed. Both are now named.
2. **Two `PixelSize` types became one — DEV-C's.** They declared it on the
   toolkit seam, where the window owner is *told* its size, and left the
   computation to WI-2. They landed first, so mine went. A test asserts what
   the surface hands over is the type `WindowOwner` declares.
3. **An ordering problem in the join, which neither of us could have seen
   alone.** `WindowOwner` is told its pixel size *at construction* and is also
   what creates the window — but the size comes from font metrics, and
   measuring a font needs a Tk interpreter that does not exist yet. Handled
   entirely on WI-2's side with `measure_metrics()` and `grid_pixel_size()`,
   which make a Tk interpreter, withdraw it before the event loop can be
   entered so it is never mapped, measure, and destroy it. DEV-C's code is
   untouched. **This is the sequence WI-18 will need.**

---

## Still open

**For a human** (assumption **A4** and the two that go with it):

1. Is Menlo 16pt, in a 400 x 570 window, large enough to read comfortably?
   One constant; 18pt is 440 x 630 and 20pt is 480 x 720.
2. Do the double-line box glyphs join up cleanly at 16pt, or is there a
   hairline between cells?
3. Does the picture flicker on a mapped window at seven frames a second?

All three are WI-16's, which is DEV-B's in M3.

**For the technical lead:**

- **`tk_grid.create_surface` and `measure_metrics` have no automated test**,
  because exercising them needs a live toolkit interpreter and the plan
  forbids the suite constructing one. Verified by hand instead, headlessly;
  exercised for real by WI-4. Flagged rather than left as a quiet gap.
- **The merged suite now imports `tkinter`**, via DEV-C's `test_tk_toolkit`,
  though it constructs no window. DEV-B's own modules and tests do not. Worth
  knowing when WI-10 writes the architecture guard: *importing* the toolkit
  below the shell is the thing to forbid, and *constructing a window* in the
  suite is a separate and stronger rule.

---

## Next for DEV-B

M1: WI-7 (the ghost's movement policy) and WI-9 (the input translator). Both
depend on work that has landed — WI-7 on WI-5, WI-9 on WI-1 — so neither is
blocked.
