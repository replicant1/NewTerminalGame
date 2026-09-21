# AMEND-6 — the toolkit that maps windows without painting them

Measured on 2026-09-21, from the primary checkout on `main` at a4c6766. Found by running
the suite the plan excludes by default, which nothing had done since WI-17.

    .venv/bin/python -m pytest -q                  1017 passed, 12 deselected
    .venv/bin/python -m pytest -q -m needs_window  10 passed, 2 FAILED

The two failures are both in `tests/test_pixels_reach_the_screen.py`, and they are the only
two tests in the project that read the screen rather than the toolkit.

## 1. The control failed, so the game was never the suspect

That file is a pair: a **control** that draws `████████` on a plain Tk canvas with no
project code in it, and the real check that photographs the running game. Its own docstring
says that if the control fails, nothing below it means anything. The control failed.

Reduced further, away from the suite entirely — a `Toplevel` with a `#ff0000` canvas,
`lift()`, `-topmost`, `focus_force()`, photographed at 1 s, 3 s and 6 s:

```
t=1s red=0 top=[((255,255,255), 4855), ((255,255,254), 622)]
t=3s red=0 top=[((255,255,255), 4855), ((255,255,254), 622)]
t=6s red=0 top=[((255,255,255), 4855), ((255,255,254), 622)]
```

**Zero red pixels.** A full-screen capture taken at the same moment shows the window is
genuinely there — titlebar, frame, correct position, stacked above the terminal — and its
interior is white. The toolkit maps the window and paints nothing into it.

Three things it is *not*, each ruled out rather than assumed:

- **Not a screen-recording permission.** `screencapture` photographs every other
  application's windows on this machine, including the terminal the suite runs in. The
  capture that misses the Tk window is rich in detail everywhere else: 26,368 distinct
  colours.
- **Not a secondary-display coordinate error** — the failure mode `tests/pixels.py` was
  written to avoid. There is one display: a built-in Liquid Retina XDR, 3024 × 1964, main.
- **Not a timing or event-loop problem.** Six seconds and three separate captures inside a
  running event loop give the identical histogram, to the pixel count.

The interpreter is `/usr/bin/python3`, CPython 3.9.6, and its `_tkinter` binds **Tk 8.5.9**
— Apple's system Tcl/Tk, which predates every macOS this machine has run.

## 2. What the suite could not see, and why

**Every other window test passes on the toolkit that draws nothing**, and that is the part
worth keeping. Ten of the twelve `needs_window` tests assert against what Tk was *told*:
the window's reported geometry, its title, its stacking, the item types on its canvas. All
of that is correct. It is correct on a window whose interior is blank.

This is the same gap `tests/pixels.py` was written for, in its own words — *"a game that
renders a blank window shipped with 996 tests green"* — and it has now caught a second,
larger instance of itself. The first was an application defect. This one is the toolkit,
and **no application code could have been written to pass it.**

## 3. The third option, which nobody had costed

Section 1.2 framed the runtime as a choice between "a modern Python with no window and an
old Python with one". The measurement it rested on was correct and is still correct:
`/opt/homebrew/bin/python3.14` has no `_tkinter` at all. What went unasked is whether it
could have one.

```
brew install python-tk@3.14     # brings tcl-tk 9.0.4
```

That is the whole cost. The same red-canvas probe on the result:

```
tk patchlevel: 9.0.4
t=1s red=9009 top=[((255,0,0), 9009), ((255,49,43), 34)]
```

## 4. The font, re-measured — the cell did not move

S-1's scan from its section 6 was re-run verbatim on Tk 9.0.4, over all 91 glyphs the game
draws, at every Menlo size from 8 to 36.

**Tk 8.5.9 took a point as a pixel. Tk 9.0.4 applies the 96/72 scaling a point is owed.**
Every nominal size is therefore 4/3 larger than S-1 read it, and the cell S-1 found at
size 16 is now asked for as **size 12**:

| | S-1, Tk 8.5.9 | AMEND-6, Tk 9.0.4 |
|---|---|---|
| Nominal size | Menlo 16 | **Menlo 12** |
| Advance × linespace | 10 × 19 px | **10 × 19 px** |
| 40 × 30 window | 400 × 570 px | **400 × 570 px** |
| `═` bbox at x = 0 | `[-1, 0, 11, 19]` | **`[-1, 0, 11, 19]`** |
| `═` bbox at x = 10 | `[9, 0, 21, 19]` | **`[9, 0, 21, 19]`** |
| Exact-grid ceiling | size 16 | **size 12** |

Every S-1 conclusion reproduces at the new size:

- all 91 glyphs — the 29 double-line box characters, the 32 block elements, `■`, `▪` and
  every character of the status line — measure exactly `measure("M")`;
- all 91 report `font actual -family` = Menlo, with no substitution;
- `measure(g * 40) == 40 * measure(g)` for all 91;
- the specimen's 37-character maze row measures 370, exactly 37 × 10;
- **the non-vacuity controls still differ**, which is what stops the family check passing
  by accident: Devanagari KA → Kohinoor Devanagari, advance 13; CJK 中 → PingFang SC,
  advance 17; the Tamil year sign → Tamil Sangam MN, advance 24; and U+E000, still Menlo
  and still advance 18, caught by the advance check and not the family one.

The exact-grid ceiling moved from 16 to 12 **in nominal units only** — both readings name
the same cell. Above it the drift is 4 to 38 px over 40 cells at every size from 13 to 36,
so the property fails as decisively as S-1 found it failing above 16.

### What this means for human item 3

Section 9's item 3 — *is the type large enough to read comfortably* — was answered by a
person looking at a running game in WI-17. **That verdict survives this change untouched**,
because the window it was given is the window this produces: the same 400 × 570 rectangle,
the same 10 × 19 cell, the same glyph bboxes. `FONT_SIZE` is a number in the toolkit's
units, not a size on the glass. Only the second of those was ever put to a human, and it
has not changed.

## 5. What changed, and what did not

Changed: the interpreter pin, the Tk pin, `FONT_SIZE` 16 → 12, `EXACT_GRID_CEILING`
16 → 12, `MEASURED_MENLO_16` → `MEASURED_MENLO_12`, the three tests that built a font at
size 16 of their own, and the one test whose second data point was Menlo 8 (5 × 9 on the
old toolkit, 7 × 13 on the new).

Not changed: **any pixel the player sees.** No production logic, no geometry, no colour,
no glyph. Every `400 × 570` in the codebase is still correct, which is the clearest single
statement of what this amendment is.

    .venv/bin/python -m pytest -q                  1017 passed, 12 deselected
    .venv/bin/python -m pytest -q -m needs_window  12 passed, 1017 deselected

## 6. What this costs, and one thing it leaves open

The plan's section 1.2 claimed two things that are now false: *"no modern Tk is needed"*
and *"nothing has to be installed on the user's machine"*. Both are the price of the two
pixel tests, and they are recorded as paid rather than argued away.

**The language level is now a convention rather than a wall.** The codebase is written to
3.9 and stays there; the interpreter is 3.14, so `tests/test_runtime.py` no longer fails on
a `match` statement or a `list[int]` annotation the way it was designed to. Nothing in the
codebase uses either, and review is what keeps it that way. Anyone who wants the wall back
adds a syntax check against a 3.9 parser — cheap, and not done here, because nobody has
needed one yet.

## 7. Reproducing it

```python
# The red-canvas probe of section 1. Run it on each interpreter.
import tkinter, sys
sys.path.insert(0, "tests")
import pixels
root = tkinter.Tk(); root.withdraw()
top = tkinter.Toplevel(root)
c = tkinter.Canvas(top, width=400, height=300, background="#ff0000",
                   highlightthickness=0, borderwidth=0)
c.pack(); top.deiconify(); top.lift(); top.focus_force()
def shoot():
    print(pixels.capture(c, "/tmp/probe.bmp"))
    print("red:", pixels.near(pixels.histogram("/tmp/probe.bmp"), (255, 0, 0)))
    top.destroy(); root.quit()
top.after(1000, shoot)
root.mainloop()
```

The font scan is S-1 section 6's script unchanged, with `range(8, 37)` and the same
`GLYPHS` list; add `max(abs(f.measure(g * 40) - 40 * adv) for g in GLYPHS)` to it for the
drift column of section 4.
