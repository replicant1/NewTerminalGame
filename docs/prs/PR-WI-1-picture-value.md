# WI-1 — The picture as a value

**Developer:** DEV-B · **Branch:** `r6/wi-1-picture-value` · **Base:** `main`

The seam the whole test strategy hangs off. The presentation layer does not
draw; it returns a picture. This work item is that picture: a pure, comparable
30 x 40 value that renders to plain text, so every later picture assertion is a
text comparison with no window and no toolkit anywhere near it.

## What is in it

| File | What it is |
| --- | --- |
| `terminal_game/__init__.py` | The package, and the layer dependency rule written where a developer will meet it |
| `terminal_game/presentation/__init__.py` | Presentation layer — composes, never draws, never imports a toolkit |
| `terminal_game/presentation/frame.py` | `Colour`, `Cell`, `BLANK`, `Frame`, `FrameBuilder`, and the measured geometry constants |
| `tests/__init__.py` | The suite, and the pinned command that runs it |
| `tests/specimen.py` | The specimen picture from the requirements, transcribed as data (shared test data, deliberately not named `test_*`) |
| `tests/test_frame.py` | 45 tests |

## The design, in one paragraph

`Colour` is a six-member enum — blue walls, dim gold dots, bright yellow
player, pink ghost, cyan status, black ground — and nothing else is accepted
anywhere. A `Cell` is exactly one character in one of those colours; there is
no way to put anything else in one, which is where SCRN-2 (caution C5) is
written down. `Frame` is immutable, hashable and comparable, and `to_text()`
renders it as 30 lines of exactly 40 characters with nothing stripped, so the
blank 3-column right-hand margin is three real spaces. `FrameBuilder` is the
mutable half: `set_cell`, `write` (one character per cell, all-or-nothing if it
would overrun), `place_row` (how row 29 will arrive from WI-13 as a value), and
`build()`. A frame already built never changes, whatever the builder does next.

## Geometry — the measurement, taken again

I measured the specimen picture in `FUNCTIONAL_REQUIREMENTS.md` rather than
taking the number on trust:

| Measured | Result |
| --- | --- |
| Rows in the specimen | 30 |
| Width of every one of the 29 maze rows | **37** characters, all identical |
| Status row | 27 characters, with one leading space |
| Right-hand margin in a 40-column window | **3** columns |

This confirms plan section 5 and contradiction **C-1**. The architecture's
MAZE-1 prose says 38 columns and a 2-column margin; its own measurement V8 and
mine both say 37 and 3. `MAZE_COLUMNS = 37` and `RIGHT_MARGIN_COLUMNS = 3` are
what this branch builds, and the constants are asserted *against the specimen
picture* rather than restated, so a change to the picture breaks the test
rather than drifting past it.

## Structural decisions, offered rather than asked

The plan leaves names and layout to the developers (section 1, "what is not
fixed"). These are mine; say so if you want them different.

- **Package `terminal_game/`, one sub-package per layer** — `domain`,
  `application`, `presentation`, `shell`. WI-10's architecture guard then has
  a trivial job: the rule is the directory name.
- **Tests in a flat `tests/` package at the root.** The pinned
  `discover -t . -s .` finds them; `docs/` and `.claude/` have no
  `__init__.py` so discovery skips them.
- **`tests/specimen.py`** carries the specimen picture as shared data. WI-12
  and WI-19 will want it and should not retype it.
- **Immutable `Frame` plus a separate `FrameBuilder`.** END-5 says the last
  picture stays on screen; a stored picture that its composer can still mutate
  is not a value.
- **Out-of-range positions raise `IndexError`, negatives included.** Python's
  negative indexing would otherwise wrap and draw silently in the wrong place,
  which is exactly the "silently ignored" failure the work item names.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 45 tests — 45 passed, 0 failed, 0 skipped
```

No test in this branch opens a window, imports a toolkit, or takes more than
20 ms.

## What the tests own

Shape (30 x 40, and every way of being something else refused); positions
outside the frame, negatives included, refused and leaving the frame unchanged;
the closed colour vocabulary, including a colour from a *different* enum being
refused; a cell holding exactly one character, and the three-column actor
motifs therefore being three separate cells; value semantics — equal, unequal
by one glyph, unequal by one *colour* while rendering identically, and hashing
alike; immutability of a built frame; `place_row` for row 29; and the whole
specimen picture rendered character for character with its 3-column margin
asserted as black ground rather than merely as spaces.

## Nothing needing a ruling

No deviations. No blocked work. The C-1 correction is confirmed by measurement,
not reopened.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
