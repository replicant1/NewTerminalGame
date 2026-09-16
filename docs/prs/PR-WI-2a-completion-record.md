# WI-2a — DEV-B's M0 completion record

**Developer:** DEV-B · **Branch:** `r6/wi-2a-completion-record` · **Base:** `main`

Documents only. No code, no tests, no behaviour change.

WI-1 (PR #23) and WI-2 (PR #26) had both merged before the completion record
for the lane could be written, so it needs a branch of its own —
the same shape DEV-A used for WI-5a and DEV-C for WI-3's completion record.

## What is in it

| File | |
| --- | --- |
| `docs/completions/COMPLETION-M0-DEV-B.md` | The lane record: what landed, the suite as left, the three measurements, what was settled with DEV-A and DEV-C, and what is still open |
| `docs/progress/r6-wi-2-grid-surface.md` | Closing `COMMIT`, `MERGE`, `TEST`, `NOTE` and `DONE` lines, which could only be written after the merge |
| `docs/progress/r6-wi-2a-completion-record.md` | This branch's log |

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 228 tests — 228 passed, 0 failed, 0 skipped
```

Unchanged by this branch, which touches no code.

## The two things in the record a reader should not miss

**Tk's own `TkFixedFont` is not fixed width on this machine.** It resolves to
`.AppleSystemUIFont`, reports `fixed = 0`, and has six distinct advance widths
across the glyphs this game draws. Anything reaching for it gets a
proportional font while being told it is fixed.

**The merged suite now imports `tkinter`** — via `test_tk_toolkit`, which
imports the Tk binding to test key translation without a window. No window is
constructed. It is worth WI-10 knowing that *importing the toolkit below the
shell* and *constructing a window in the suite* are two different rules, and
that the second is the stronger one.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
