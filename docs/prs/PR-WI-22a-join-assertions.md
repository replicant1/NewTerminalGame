# WI-22a — rewrite the two assertions that re-derived the join

Amendment 11. Three bounded things and nothing else. **No production behaviour changes**;
`terminal_game/presentation/picture.py`, `frame_composer.py` and `status_line.py` are
untouched, and the only non-test file edited is a package docstring.

## 1. The two assertions

Each of these tests pinned a real join that nothing else in the suite pins — the **Shell →
picture** join in one case, the **tool → picture** join in the other — and each built its
expected value by *re-deriving* the join inside the test. That is the wiring's own job done
a second time in the test, so both copies could have drifted together and the test would
have gone on passing. Section 4, as amendment 11 restates it: the fault is the assertion,
not the test.

**`tests/test_game.py::ThePictureTheSessionIsComposedWithTest`**

| | |
| --- | --- |
| Was | `status_row(state.score.points, state.outcome)` compared cell by cell against row 29 of `compose_picture(state)` |
| Now | `frame_for(state) == compose_picture(state)` |

**`tests/test_the_look.py::TheGameViewIsTheRealThing::test_it_is_the_real_composer_over_a_real_generated_maze`**

| | |
| --- | --- |
| Was | `compose_frame(state, status_row(...))` rebuilt in the test, compared against `game_frame()` |
| Now | `frame_for(state) == game_frame()` |

Both now fail if and only if their own wiring stops going through the seam, and own nothing
on either side of it.

**One rename, and it needs flagging.** The first test's method was called
`test_row_29_is_exactly_what_the_status_line_says_it_is`, which after the rewrite would
have described something the test no longer does. It is now
`test_the_session_is_composed_with_presentations_picture_function`. The class name is
unchanged. **Neither name is cited by `docs/TRACEABILITY.md`** — checked before and after —
but WI-20b's sweep is being written as this lands and its citation checker turns a wrong
citation into a red `main`, so it is called out here rather than left to be discovered.

Two imports in `tests/test_game.py` became unused and were removed with the assertion they
served: `status_line.status_row` and `frame.FRAME_COLUMNS`. `presentation.picture.frame_for`
replaces them.

## 2. The stale package docstring

`terminal_game/presentation/__init__.py` still said *"Still to come: the status line
(WI-13)"*, which has been false since WI-13 landed, and it listed neither `status_line` nor
`picture` nor `specimen`. A reader looking in the package's own front door for the function
that makes a whole picture would not have found it. It now lists every module in the
package, says in bold that `frame_for` is what to call for a complete frame, and no longer
claims anything is still to come.

## 3. What was deliberately left alone

**`tools/the_look.py`'s two direct `status_row` calls**, in `joinery_frame` and
`colour_frame`, and the test that pins them
(`tests/test_the_look.py::TheColourViewNamesWhatItShows::test_row_twenty_nine_is_the_real_status_line_not_a_sample`).
They place row 29 onto hand-built frames that have no `GameState` behind them, so the
`state -> frame` seam does not apply to them and `frame_for` could not be called there.
Amendment 11 records this so nobody "fixes" it later.

Also left alone, and correctly: `tests/test_frame_composer.py:414` calls `compose_frame`
with a real `status_row`. That is WI-12's own test that the real row is *placed as it
arrives* — the composer's contract with WI-13, not the join — and it owns that.

## The measurement

`grep` over `terminal_game`, `tools` and `tests` for every `compose_frame(` call:
**twelve hits, and exactly one of them pairs `compose_frame` with a `status_row` derived
from a state — `terminal_game/presentation/picture.py:71`, the body of `frame_for`.** The
rest are WI-12's own tests, which hand the composer a deliberately fake stand-in row.
Nothing re-derives the join any more.

Structure measured rather than mutated, per section 4.

## Suite

From the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

| When | Result |
| --- | --- |
| Before, on `main` at `b11a8a6` | **747 passed, 0 failed, 0 skipped** |
| After | **747 passed, 0 failed, 0 skipped** |

Unchanged, as it should be: two assertions rewritten, no test added and none removed. Also
byte-compiled `terminal_game`, `tools` and `tests` with `/usr/bin/python3 -m compileall` to
catch the two removed imports. The six house rules are among the 747 and all pass; the
suite constructs no Tk interpreter.

## Real-toolkit exercise

**None, and that is the honest answer** (section 4). This branch changes two test
assertions and one docstring. No Shell code, no window, no use of the conductor's screen
gate.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
