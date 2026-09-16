# WI-22 — the join: one function owns the whole picture

**Announcement first, for anyone who needs it (section 2, rule 4).**
**`terminal_game.presentation.picture.frame_for(state)` — a game state in, the whole
frame out.** If you need a complete picture of a game, call that. Do not write
`compose_frame(state, status_row(...))` anywhere; after this branch that expression
exists in exactly one place in the repository, which is the body of `frame_for`.

---

## What this is

Amendment 10 of the implementation plan names a seam the plan specified and no work item
was asked to build. SCRN-1 says the window is 29 rows of maze with a status line under
it. WI-12 was told to own rows 0–28 and place the row it is handed; WI-13 was told to own
row 29 as a value. That split let two lanes run in parallel and **left nobody owning the
join**, so every caller bound the two halves together itself.

The two lines therefore existed in **four places**:

| Where | What it was called | Lane |
| --- | --- | --- |
| `terminal_game/shell/game.py` | `compose_picture` | DEV-A (WI-18) — **the only one in production** |
| `tests/scripted.py` | `compose` | DEV-B (WI-19) |
| `tools/the_look.py` | inside `game_frame` | DEV-B (WI-16) |
| `tools/window_manners.py` | `real_compose` | DEV-A (WI-17) |

This branch adds the function in Presentation and points all four at it.

## What landed

| File | What |
| --- | --- |
| `terminal_game/presentation/picture.py` | **new.** `frame_for(state) -> Frame`: WI-12's rows 0–28 with WI-13's row 29 under them, built from this state's own score and outcome. The one place SCRN-1 is a single statement. |
| `tests/test_picture.py` | **new.** Seven tests, and they assert the join and nothing either side of it. |
| `terminal_game/shell/game.py` | `compose_picture` now returns `frame_for(state)`. The name stays: it is `build_game`'s default `compose` argument and `tools/play_the_game.py` imports it. |
| `tests/scripted.py` | `compose` now returns `frame_for(state)`. |
| `tools/the_look.py` | `game_frame` now calls `frame_for(state)`. |
| `tools/window_manners.py` | `real_compose` now returns `frame_for(state)`. |

## Why a new module rather than `frame_composer.py`

The natural-looking home is WI-12's file, and DEV-A said as much when it put the
production copy in the Shell instead. Section 2 forbids editing another developer's
landed files; amendment 10 sanctions an exception **because neither lane has an agent
left** — and it says in terms that the exception "does not license editing anyone's files
beyond the call sites named here."

A new module keeps inside that. `frame_composer.py` and `status_line.py` are untouched;
the four call sites are one-line changes each; nothing was renamed, moved or tidied.

## Where this puts a defect

The point of the seam is which test goes red:

- a wrong wall glyph → WI-8's tests;
- a wrong status line → WI-13's tests;
- a wrong **join** → `tests/test_picture.py`, and nothing else.

`tests/test_picture.py` accordingly asserts two things and their consequences: that rows
0–28 are cell-for-cell what `compose_frame` produced for that state, and that row 29 is
cell-for-cell `status_row(state.score.points, state.outcome)`. It contains **no
status-line literal** (A7) — the expected row 29 is composed from WI-13's own function, so
a ruling on C-3 or C-4 would be followed rather than contradicted.

## Suite

Command, from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

| When | Result |
| --- | --- |
| Before, on `main` at `238f4dd` | **740 passed, 0 failed, 0 skipped** |
| After | **747 passed, 0 failed, 0 skipped** |

Seven added, none lost.

## What was exercised against the real toolkit

**Nothing, and that is the honest answer** (section 4, "proved by a double is not
proved"). This branch adds no Shell code and opens no window. Two of the four call sites
are in on-screen tools (`tools/the_look.py`, `tools/window_manners.py`) and both were
changed by one line each; both modules are imported and exercised by the suite, which is
what the 747 covers. The tools' on-screen behaviour was **not** re-run, because the change
cannot alter the value they display: `frame_for` is character-for-character the expression
it replaced, and `tests/test_picture.py` pins that.

## Noticed and deliberately not done

Reported rather than acted on, per the brief:

1. **`terminal_game/presentation/__init__.py` does not mention the new module**, and its
   "Still to come: the status line (WI-13)" line has been stale since WI-13 landed. It is
   WI-1's file and not a call site.
2. **`tools/the_look.py` still calls `status_row` twice directly**, in `joinery_frame` and
   `colour_frame`. Those are *not* the join — they place row 29 onto a hand-built frame
   that has no `GameState` behind it — so `frame_for` does not apply to them and they were
   left exactly as they are.
3. **Two existing tests re-derive the join** to build their expected value:
   `tests/test_game.py::…` (row 29 of `compose_picture`) and
   `tests/test_the_look.py::test_it_is_the_real_composer_over_a_real_generated_maze`.
   They are arguably now duplicates of `tests/test_picture.py`'s assertions, and they are
   other developers' tests. Raised, not deleted.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
