# WI-13 — The status line

**Lane:** DEV-A *(moved here from DEV-C by amendment 3)* · **Branch:**
`r6/wi-13-status-line`, based on `main` at `6cee5c9` · **Mode:** non-local

**Announcing, per section 2's rule 4** — two functions other lanes will want:

```python
from terminal_game.presentation.status_line import status_text, status_row

status_text(score: int, outcome: Outcome) -> str            # the line itself
status_row(score: int, outcome: Outcome) -> Tuple[Cell, ...]  # 40 cells for place_row
```

`status_row` hands over row 29 as a value; WI-12 places it with
`FrameBuilder.place_row(STATUS_ROW, ...)` and writes nothing on that row
itself.

---

## What this item is

Row 29, in cyan, and nothing else on that row ever (STAT-1, SCRN-6). Three
per-ending templates with the score substituted, reproducing STAT-2 and
STAT-3 character for character (assumption **A7**).

| File | What it is |
| --- | --- |
| `terminal_game/presentation/status_line.py` | the three templates, `status_text`, `status_row` |
| `tests/test_status_line.py` | 28 tests — and the only status-line literals in the project |
| `docs/findings/WI-13-status-line-literals.md` | what the literals measure out to, and the two contradictions as numbers |
| `docs/progress/r6-wi-13-status-line.md` | the progress log |

Requirements: **STAT-1**, **STAT-2**, **STAT-3**, **SCRN-6**, and **SCORE-5**
in part (the score is shown; that it never falls is `Score`'s, from WI-6).

## The literals, and where they came from

Extracted from `docs/FUNCTIONAL_REQUIREMENTS.md` programmatically rather than
retyped, and measured:

| Literal | Length | Column of `q quits` |
| --- | --- | --- |
| `score 0    arrows, q quits` | 26 | 19 |
| `CAUGHT  score 37   q quits` | 26 | 19 |
| `CLEARED  score 274  q quits` | 27 | 20 |
| specimen picture, row 29 | **27** | 20 |

Both contradictions the plan predicted are confirmed as numbers:

- **C-3** — the specimen's row 29 is `' score 0    arrows, q quits'`, one
  leading space longer than STAT-2's literal. **A7 takes the literal**, so
  the text starts at column 0.
- **C-4** — `q quits` cannot be at column 19 and column 20 under one padding
  rule. **A7 takes two per-ending templates**, each reproducing its own
  example. The line therefore grows and shrinks with the digits in the score
  rather than holding a column.

**Neither is a ruling.** The user has not answered either. If an answer
arrives, the change is the three template constants in `status_line.py` and
the three literals in `tests/test_status_line.py` — nowhere else.

## Two things worth knowing before you read the tests

**`CLEARED  score 274` is illustrative, not reachable.** A whole game is
worth **259 to 271 points, mean 264.5** — measured over 200 mazes in
`docs/findings/WI-6-start-squares.md`. The literal is reproduced exactly
anyway, because A7 makes the specification's example normative; but no player
will ever see 274, and a test that asserted a game ending on 274 would be
asserting something the game cannot produce. The tests use 264 for the
"three digits do not corrupt the line" cases and 274 only where the
specification's own literal is being reproduced.

**The whole row is cyan, including the blank cells past the text.** Measured:
`GridSurface._show` deletes rather than paints a cell whose glyph is a space,
so nothing on screen differs either way. One colour for the whole row lets
STAT-1 — *"the bottom row shows the score and the keys, and nothing else"* —
be asserted as a property of the row rather than of a prefix of it. This is
an ownership call, not a design one: WI-13 owns row 29.

## The prohibition, and the one place it is about to be tested

A7 confines every status-line literal to this item. **Two lanes are going to
meet it:**

- **WI-12** places row 29 and never composes its text — build an expected
  row 29 with `status_row(...)`.
- **WI-19** is asked to assert whole frames as text. A 30-line expected
  picture typed out by hand *would contain the status literal*, and would
  breach the confinement without anyone intending it. Compose the expected
  row 29 with `status_text(...)` and join it onto the 29 maze rows.

**No automated scanner forbidding the literal elsewhere was written**, and
deliberately: it would fail WI-19's honest work. Amendment 2's lesson — a
rule stated wrongly is worse than no rule — applies directly.

## Nothing here opens a window

Pure Presentation. No toolkit is imported, no clock is read, no random source
is reached for. `tkinter._default_root` is untouched, so WI-10's rule 5 is
unaffected.

## The suite

Run from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 402 tests in 3.752s

OK
```

**402 passed, 0 failed, 0 skipped.** 374 were on `main` at `6cee5c9`; **28
are WI-13's.**

**No mutation test was written and no working code was broken to watch a test
go red.** That is prohibited and none was invented.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
