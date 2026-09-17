# WI-16b — completion records for lane C, M1 to M3

The paperwork that closes lane C. **No code, no tests.**

Lane C has no next branch to carry a log tail onto — WI-19 exists to spend answers the user
has not given, and may not run — so this is the case the lead's log-tail ruling reserved
`r7/<item>-completion-record` for.

## What is here

| File | |
|---|---|
| `docs/completions/COMPLETION-M1-DEV-C.md` | WI-6. Notes that WI-8 moved to lane B |
| `docs/completions/COMPLETION-M2-DEV-C.md` | WI-12 and WI-12b. Notes that WI-15 moved to lane B |
| `docs/completions/COMPLETION-M3-DEV-C.md` | WI-16 and WI-16b, plus lane C over the whole run |
| `docs/progress/r7-wi-16b-placement-journey.md` | the `MERGE` and `DONE` lines, which could only be written after #103 landed |

`COMPLETION-M0-DEV-C.md` already exists and is unchanged; the three new records follow it
one per iteration, as lane B's do.

## Lane C, in one place

**Seven landings — S-2, WI-5, WI-6, WI-12, WI-12b, WI-16, WI-16b — and `main` green after
every one.**

Three conflicts, all in `tests/conftest.py` or my own progress logs, all resolved by
keeping both sides, none escalated. One window left on the user's screen for two minutes,
caught and killed by pid. Fourteen crash reports, eleven of them mine, none since
02:00:51Z. One `launchd` job registered for four seconds and removed.

## What lane C leaves for the user

**WIN-4's route is the one that matters, and it is not what section 9 originally asked.**
S-2 proved the anchor is readable with **no permission of any kind**, for any application —
measured on both sides of the Screen Recording gate — so the user is choosing between three
routes rather than granting or declining:

- **A** — CoreGraphics in a short-lived child process before Tk exists. Grants nothing,
  prompts never, **meets WIN-4 in general**. My recommendation, with two costs now named:
  it needs a ruling on the `ctypes` prohibition for shipped code, and a mis-wired reader
  degrades WIN-4 silently because `anchor_from` swallows everything.
- **B** — AppleScript. A dialog once per application, forever, and defeated anyway by the
  `position` defect S-2 measured.
- **C** — no anchor. **What ships today, and WIN-4 is not met.**

The other four are unchanged and none is a thing an agent may record as verified: the
titlebar, the type size, whether the box-drawing glyphs read as unbroken lines, and the
Dock tile the default suite now raises.

## Suite state

```
.venv/bin/python -m pytest -q          →  961 passed, 0 failed, 0 skipped, 9 deselected
```

Unchanged by this PR, which adds no code and no tests. On `main` at `7518e64`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
