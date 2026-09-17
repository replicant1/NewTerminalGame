# S-2 — completion record and progress-log tail

The paperwork half of S-2. PR [#76](https://github.com/replicant1/NewTerminalGame/pull/76)
carried the finding and merged as `77c422e`; this carries the two things that could only be
written after it landed.

## What is here

| File | |
|---|---|
| `docs/completions/COMPLETION-M0-DEV-C.md` | Lane C's M0 completion record — the verdict, the two defects, the unowned Tk measurement, and three suite runs with their heads |
| `docs/progress/r7-s-2-anchor-window.md` | The `MERGE` line and the post-merge count, which did not exist when #76 was pushed |

No code, no test, no change to the finding.

## Suite state

```
.venv/bin/python -m pytest -q          →  56 passed, 0 failed, 0 skipped
```

Run at 01:44:20Z from the repository root on `77c422e` — `main` with S-2 already in it —
in a `.venv` built from `/usr/bin/python3` 3.9.6 with pytest 8.4.2. S-2 adds no test, so 56
is the count `main` already carried. `lsappinfo visibleApplicationCount` was 7 before and
after: the default suite puts no window on the screen.

## The two things worth carrying upward from #76

**WIN-4 is answerable, and the question changed shape.** The anchor *can* be read with no
permission at all, for any application — proven on both sides of the Screen Recording gate.
So plan section 9 item 4 is not "grant or decline" but a choice between three routes, and
the finding lays them out. Option A meets WIN-4 in general and asks the user for nothing.

**The crash was Tk-specific.** `ctypes` into CoreGraphics ran clean 8 times in a plain
process and crashed 3 times out of 3 inside a live Tk root. Option A is built to keep the
two apart. Pending the user's answer the prohibition holds and **WI-15 implements nothing**.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
