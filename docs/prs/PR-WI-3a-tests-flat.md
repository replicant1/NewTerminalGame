# WI-3a — WI-3's tests, flat, like everybody else's

**Developer:** DEV-C · **Branch:** `r6/wi-3a-tests-flat` · **Base:** `main`
**Follows:** WI-3 (PR #25) · **Alongside:** DEV-A's WI-5a (PR #27) · **Iteration:** M0

Moves only. No behaviour changes, no test changes, nothing renamed but paths.

## Why this exists

WI-1, WI-3 and WI-5 were built at the same time in three worktrees from a tree with no
application in it. The plan leaves test layout to the developers (section 1), so each of
us picked one, and WI-3 picked a nested package:

| Landed by | Tests |
| --- | --- |
| **WI-1**, DEV-B | flat, in `tests/` |
| **WI-5**, DEV-A | nested, in `tests/domain/` — moving to flat in PR #27 |
| **WI-3**, DEV-C | nested, in `tests/shell/` — **this branch** |

DEV-A's PR #27 consolidates the root package and states one convention for the tree,
with tests flat in `tests/`. That leaves WI-3 as the only nested one. I raised it on
that PR rather than through a lead, and conformed rather than argued: flat is the
incumbent, two of three developers already use it, and I am about to add two more
items' worth of tests in M1 (WI-8 and WI-10) that would otherwise inherit the
inconsistency. WI-10 in particular is the architecture guard that walks the whole tree,
and one convention is one less thing for it to special-case.

## What this does

- `tests/shell/test_cadence.py` → `tests/test_cadence.py`
- `tests/shell/test_tick_timer.py` → `tests/test_tick_timer.py`
- `tests/shell/test_tk_toolkit.py` → `tests/test_tk_toolkit.py`
- `tests/shell/test_window_owner.py` → `tests/test_window_owner.py`
- `tests/shell/recording_toolkit.py` → `tests/recording_toolkit.py` — a helper,
  deliberately not named `test_*`, in the same way as DEV-B's `specimen.py`
- `tests/shell/__init__.py` removed
- WI-3's PR summary and completion record corrected to the new path

None of the four module names collides with anything already in `tests/`. The relative
import of the recording double needed no change: both files simply moved up one
package. **Nothing of DEV-A's or DEV-B's is touched.**

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

**167 passed, 0 failed, 0 skipped** — the same 167 as before the move, which is the
point: the count is what shows nothing stopped being discovered.

## Still true after this

`tools/probe_tk_window.py` is the only thing in the tree that opens a window, it is not
named `test_*`, and the suite does not collect it. No test in the suite constructs a
toolkit window.
