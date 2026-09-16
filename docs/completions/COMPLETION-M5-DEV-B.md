# M5 — DEV-B — complete

**Work item:** WI-22, *the snagging list*, under amendment 10 its principal task is the
`state -> frame` seam.
**Branch:** `r6/wi-22-the-join`, based on `main` at `238f4dd`.
**Pull request:** [#64](https://github.com/replicant1/NewTerminalGame/pull/64).
**Mode:** non-local.

## What was finished

| File | What |
| --- | --- |
| `terminal_game/presentation/picture.py` | new — `frame_for(state) -> Frame`, the one place SCRN-1's "29 rows of maze, one row of status" is a single statement |
| `tests/test_picture.py` | new — seven tests owning the join and neither side of it |
| `terminal_game/shell/game.py` | `compose_picture` delegates to `frame_for` (the production call site) |
| `tests/scripted.py` | `compose` delegates to `frame_for` |
| `tools/the_look.py` | `game_frame` calls `frame_for` |
| `tools/window_manners.py` | `real_compose` delegates to `frame_for` |

The expression `compose_frame(state, status_row(state.score.points, state.outcome))` now
occurs **once** in the repository, inside `frame_for`. It occurred four times before.

Nothing was renamed, moved or otherwise tidied. `frame_composer.py` and `status_line.py`
are untouched.

## The state of the test suite as I left it

From the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

| When | Result |
| --- | --- |
| Before any change, on `main` at `238f4dd` | **740 passed, 0 failed, 0 skipped** |
| On `r6/wi-22-the-join` after the change | **747 passed, 0 failed, 0 skipped** |

This document is committed on the branch, so it is written before the merge. The
post-merge run — `git fetch origin && git merge origin/main`, then the same command again
— is recorded on the last `TEST` line of `docs/progress/r6-wi-22-the-join.md` and in the
report to the conductor. Read the count from there, not from here.

Seven tests added, none lost, none skipped. The six house rules are among the 747 and all
pass; no Tk interpreter is constructed by the suite.

## Open items handed on

Three things were noticed and deliberately not done — they are set out in full in
`docs/prs/PR-WI-22-the-join.md`:

1. `terminal_game/presentation/__init__.py` does not list the new module and is stale
   about WI-13.
2. `tools/the_look.py` still calls `status_row` directly in `joinery_frame` and
   `colour_frame`; those are not the join and `frame_for` does not apply.
3. Two existing tests, in `tests/test_game.py` and `tests/test_the_look.py`, re-derive the
   join to build their expected value and may now duplicate `tests/test_picture.py`.
