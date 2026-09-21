# PR-AMEND-6 — the toolkit was mapping windows and painting nothing

Risk: **HIGH** — this changes the interpreter, the windowing toolkit and the font constant the
window's size is derived from. Nothing else in this project touches all three at once.

Amendment 6. Section 1.2's fixed runtime, re-decided; the font re-measured under it; human
item 5 reopened and answered. **No application logic changes.** No pixel the player sees
changes either, which is the shortest true statement of what this is.

## Why

The user asked for all the tests, including the twelve `pytest.ini` excludes by default.

```
.venv/bin/python -m pytest -q                  1017 passed, 12 deselected
.venv/bin/python -m pytest -q -m needs_window  10 passed, 2 FAILED
```

Both failures in `tests/test_pixels_reach_the_screen.py` — the only two tests in the project
that read the screen rather than the toolkit.

**The control failed.** That file is a pair: a control that draws `████████` on a plain Tk
canvas with no project code in it, and the real check that photographs the running game. Its
own docstring says that if the control fails, nothing below it means anything. So the game was
never the suspect.

Reduced away from the suite entirely — a `Toplevel` with a `#ff0000` canvas, `lift()`,
`-topmost`, `focus_force()`, photographed three times:

```
t=1s red=0 top=[((255,255,255), 4855), ((255,255,254), 622)]
t=3s red=0 top=[((255,255,255), 4855), ((255,255,254), 622)]
t=6s red=0 top=[((255,255,255), 4855), ((255,255,254), 622)]
```

A full-screen capture at the same moment shows the window **is** there — titlebar, frame,
correct position, stacked above the terminal — with a white interior. **Tk 8.5.9 maps the
window and paints nothing into it.**

Not a permission (`screencapture` photographs every other application's windows in the same
shot, 26,368 distinct colours). Not the secondary-display hazard `tests/pixels.py` was written
to avoid (there is one display). Not timing (six seconds, three captures, identical to the
pixel count).

**Every other window test passes on that toolkit**, and that is the part worth keeping: ten of
the twelve assert what Tk was *told* — geometry, title, stacking, canvas item types — and all
of it is correct on a window whose interior is blank.

## What changes

- **The interpreter is `/opt/homebrew/bin/python3.14` with `python-tk@3.14`**, which brings
  Tcl/Tk 9.0.4. Section 1.2 framed the runtime as a choice between "a modern Python with no
  window and an old Python with one". Its measurement was correct and is still correct — the
  Homebrew python has no `_tkinter`. What went unasked is whether it could have one. It can,
  for one `brew install`, and the same red-canvas probe on it reads `red=9009`.
- **`FONT_SIZE` 16 → 12, and `EXACT_GRID_CEILING` 16 → 12 — the same cell, in different units.**
  Tk 8.5.9 took a point as a pixel; 9.0.4 applies the 96/72 a point is owed, so every nominal
  size is 4/3 larger and S-1's size-16 cell is now asked for as size 12. S-1 section 6's scan
  was re-run verbatim, all 91 glyphs, sizes 8 to 36:

  | | S-1, Tk 8.5.9 | AMEND-6, Tk 9.0.4 |
  |---|---|---|
  | Nominal size | Menlo 16 | **Menlo 12** |
  | Advance × linespace | 10 × 19 px | **10 × 19 px** |
  | 40 × 30 window | 400 × 570 px | **400 × 570 px** |
  | `═` bbox at x = 0 / x = 10 | `[-1,0,11,19]` / `[9,0,21,19]` | **identical** |
  | Exact-grid ceiling | size 16 | **size 12** |

  Uniform advance across all 91, no substitution anywhere, `measure(g*40) == 40*measure(g)` for
  all 91, the specimen's 37-character row at 370 — and **the non-vacuity controls still
  differ**, including the U+E000 row that the family check alone would have passed.
- **`MEASURED_MENLO_16` → `MEASURED_MENLO_12`**, and the four tests that named 16 of their own:
  three that build a font directly and one whose second data point was Menlo 8 (5 × 9 on the
  old toolkit, 7 × 13 on the new).
- **`tests/test_runtime.py` is repointed at 3.14 and Tk 9**, which it predicted: *"If a modern
  Tk has been installed deliberately (section 9, human item 5) then this assertion is the one
  place that has to move."*
- **Human item 5 — "consent to installing a modern Tk" — is recorded as asked, closed, and
  asked again.** S-1 closed it on a measurement taken with the window *withdrawn*. That was
  true, and it could never have caught a toolkit that fails to paint a *mapped* one. The user
  answered it in the session that found this.
- README, `requirements.txt`, the reviewer agent's venv command, the two scenario documents the
  font and the repaint table appear in, and the doc line-anchors these edits shifted.

## Scrutiny

- **`tests/test_metrics.py`'s parametrised pixel-size table.** Its second row was "Menlo 11" and
  is now "Menlo 8 on Tk 9.0.4" — same numbers, different label, because 7 × 13 is what size 8
  measures on the new toolkit. Check the labels, not the arithmetic; the arithmetic never moved.
- **`test_the_font_asked_for_is_the_font_resolved`** asserts `size == 12` as a literal rather
  than against `FONT_SIZE`. Deliberate — it pins the measurement, and reading the constant it
  is meant to guard would make it pass by construction. Worth agreeing with.
- **The language level.** The interpreter is 3.14, so `test_runtime.py` no longer fails on a
  `match` statement or a `list[int]` annotation the way it was designed to. The codebase is
  written to 3.9 and stays there; **only review enforces that now**. Restoring the wall means a
  syntax check against a 3.9 parser. Not added here. This is the one thing this amendment
  loses, and it should be agreed to rather than noticed later.
- **`root.update()` returns on Tk 9.0.4** — the S-2 hang was a Tk 8.5 defect. The prohibition
  stays, because every repaint path is built on `update_idletasks()`, which was never the
  problem. Check that the annotations read as "kept deliberately" and not as "no longer true,
  so ignore the rule".
- **Two of section 1.2's claims are now false** — *"no modern Tk is needed"* and *"nothing has
  to be installed on the user's machine"*. Both are recorded as paid, not argued away. They are
  the price of the two pixel tests.

## Review round 1 — Copilot, 🟡 Changes recommended, 4 findings

Three fixed, one disputed on the remedy and fixed on the defect underneath it. All four
answered on their threads; `070af51`.

- **`.claude/agents/code-reviewer.md` grew the venv command and not the formula** (HIGH).
  Correct. A clean review machine would fail `tests/test_runtime.py` before a single game
  test ran. `brew install python-tk@3.14` is now the first line of that block, marked *once
  per machine, not per worktree*.
- **The 3.9 syntax wall went with the interpreter** (MEDIUM). Accepted: documenting the loss
  in this summary is not the same as accepting it. `tests/test_runtime.py` now parses every
  module in `terminal_game/`, `tests/` and `tools/` with
  `ast.parse(..., feature_version=(3, 9))` — CPython's parser told to accept only 3.9, no 3.9
  interpreter needed. It carries a control (a parser told to accept 3.9 must refuse `match`)
  and a non-empty check. **Verified by putting a `match` into `palette.py`:** the sweep fails
  and names the file and line. Syntax only, and the test says so — `functools.cache` is an
  attribute access no parser will see, and review owns that half.
- **README's later 3.9 section still said "the interpreter is 3.9"** (LOW). Right, and my
  sweep missed it by searching for `3.9.6`. It now says the interpreter is 3.14, the source
  is 3.9, and names what enforces each half.
- **Pin the Tk patch version** (MEDIUM) — *declined, and the defect under it is worse than the
  comment said.* A version string is a proxy for a measurement this project already takes:
  `test_the_font_on_this_machine_gives_the_measured_cell` asks the real font, so a patch that
  moved the cell fails at the measurement rather than at a version guard, and `9.0.5` would
  fail a pin while measuring identically. **But the ceiling had no such backing.**
  `exact_cell_grid()` returns `size <= EXACT_GRID_CEILING` — two constants, one set from the
  other, so it cannot fail while both are wrong. S-1 section 7 asked for the real test and
  nothing built it, which is how the ceiling moved 16 → 12 in this PR on one scan with no
  standing test to notice if it moves again. `TestTheExactCellGridIsMeasuredAndNotAsserted`
  now measures it: a 40-glyph row lands where 40 cells land at the size in use, **and does
  not one size above** — the control that makes the ceiling an edge rather than a chosen
  number. **Verified by setting `FONT_SIZE` to 13:** all 20 glyphs drift, `410 != 40 x 11`.

Both new guards were run against the defect they exist to catch before being believed.

## Suite

```
.venv/bin/python -m pytest -q                       1023 passed, 12 deselected
.venv/bin/python -m pytest -q -m needs_window       12 passed, 1023 deselected
.venv/bin/python -m pytest -q -m "needs_window or not needs_window"
                                                    1035 passed
```

Round 1 added six tests: three for the language level, three for the exact-grid ceiling.

**All twelve window tests pass for the first time.** Baseline on `main` at `a4c6766` was
1017 / 12 deselected, and 10 passed / 2 failed on the excluded marker.

Also run, because a green suite is what let this through in the first place: the game itself,
photographed on a real screen. Blue maze, dots, the player, the status line — drawing.
