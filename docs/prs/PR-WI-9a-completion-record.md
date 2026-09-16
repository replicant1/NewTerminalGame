# WI-9a — DEV-B's M1 completion record

**Developer:** DEV-B · **Branch:** `r6/wi-9a-completion-record` · **Base:** `main`

Documents only. No code, no tests, no behaviour change.

## What is in it

| File | |
| --- | --- |
| `docs/completions/COMPLETION-M1-DEV-B.md` | The lane record for M1: WI-7 and WI-9 |
| `docs/progress/r6-wi-9-input-translator.md` | Closing `COMMIT`, `MERGE`, `TEST` and `DONE` lines, which could only be written after the merge |
| `docs/progress/r6-wi-9a-completion-record.md` | This branch's log |

## The two things in it the technical lead should see

**A contradiction in amendment 1.** The ownership table says *"Directions and
headings — DEV-B, in whichever of WI-7 or WI-9 lands first"*. The
first-lander rule, in the same section and stated as the general rule, gives
them to whatever landed first — which is **DEV-A's WI-5**, on day one. The
tree follows the first-lander rule: WI-7, WI-9 and WI-11 all import
`terminal_game.domain.maze.Direction` and there is no second one. **The table
row is what is wrong, not the code** — declaring a presentation-layer
`Direction` beside the domain's is exactly the duplication amendment 1 exists
to prevent. Recommending the row be corrected to name DEV-A (WI-5).

**The ghost chooses on about 4.79 ticks in a hundred.** GHOST-2 means a
choice needs straight-on blocked *and* another way open, and those coincide
rarely. It still roams — 65 % mean corridor coverage over 2,000 ticks on 30
generated mazes, and no cycle lock. `docs/findings/WI-7-ghost-roaming.md`.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 374 tests — 374 passed, 0 failed, 0 skipped
```

Unchanged by this branch, which touches no code.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
