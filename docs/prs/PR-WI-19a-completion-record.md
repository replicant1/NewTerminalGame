# WI-19a — DEV-B's M4 completion record

**Developer:** DEV-B · **Branch:** `r6/wi-19a-completion-record` · **Base:** `main`

Documents only. No code, no tests, no behaviour change.

## What is in it

| File | |
| --- | --- |
| `docs/completions/COMPLETION-M4-DEV-B.md` | The lane record for M4: WI-19 |
| `docs/progress/r6-wi-19-scripted-game.md` | Closing `MERGE`, `TEST` and `DONE` lines |
| `docs/progress/r6-wi-19a-completion-record.md` | This branch's log |

## The two things worth the technical lead's time

**Two of my own fixtures were wrong and the tests caught both** — and in
both cases the fix was to the fixture or the harness, not the assertion. A
*"player walks into the ghost"* test came back CLEARED, because on a
three-square corridor the middle dot is already the last dot. And a frame
count was off by one because my planner ticked once after the winning move:
harmless, ignored by the session, but a turn that shows no picture and a
real loop would not make it.

**The suite got slower and I gave most of it back.** WI-19 first took it
from 4.8s to 13.1s, 5.1s of that the `PYTHONHASHSEED` subprocess replay.
Trimmed to 10.9s, of which 2.6s is the real 19 × 29 game being played to a
win — which is the point of the item.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 693 tests — 693 passed, 0 failed, 0 skipped
```

Unchanged by this branch, which touches no code.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
