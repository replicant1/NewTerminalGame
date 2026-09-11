# COMPLETION — M2, Dev A

The M2 lane for Dev A is one work item: **WI-9**, wiring the real game
together.

---

## WI-9 — wire the real game together

**Work item** WI-9, wire the real game together.
**Branch** `wi-9-wire-the-game`, based on `main` at `c8defe7`.
**Pull request** [#12](https://github.com/replicant1/NewTerminalGame/pull/12),
`--base main`, marked ready.
**Lands** no new codes. It is where GAME-1, GAME-2, START-5, CTRL-1..5,
GHOST-1, END-4, END-5, END-6 and WIN-5 stop being true in pieces and start
being true of the running program — subject to the human checks below.

## What was finished

- `termgame/loop.py` — `run_game` builds a fresh game with `rules.new_game`
  from an unseeded `random.Random()` and drives `run_loop` with `view.render`,
  `rules.move_player` and `rules.move_ghost`. `resolve_render`, WI-4's
  run-time module lookup, is gone; the renderer is a plain import, which is
  what WI-4's own report asked WI-9 to do.
- `termgame/standins.py` — **deleted.** WI-4 shipped it saying WI-9 would, and
  WI-9 did. Nothing in the loop noticed, which was the point.
- `tests/test_scripted_game.py` — new, 41 tests. The real loop driven by a
  fake screen and a fake clock and nothing else fake: a game played to a win,
  a game lost because the player walked into the ghost, a game lost because
  the ghost walked into the player with nobody pressing anything, END-3 played
  rather than reasoned about, and then sixteen keys and ticks after the ending
  that change nothing at all.
- `tests/test_curses_pty.py`, `tests/test_screen_adapter.py`,
  `tests/test_loop.py` — the three files that leaned on the stand-ins now lean
  on the real modules, except the loop's own tests, which keep a tiny local
  transition on purpose so that they stay tests of the loop's shape.
- `docs/findings/WI-9-the-running-game.md` — the tick rate, the cost of a
  frame, the ghost's reversals and a game that ended by itself, all measured
  in real processes.

**`Terminal Game` did not change.** The seam WI-2 built was in the right
place; there is now a test that says so.

## The state of the test suite

```
/usr/bin/python3 -m unittest discover -s tests
Ran 606 tests in 12.013s
OK (skipped=2)
```

Cross-checked on `/opt/homebrew/bin/python3` 3.14.7: same counts, `OK`.

**The count went down as well as up**, because this item deletes code and the
tests that went with it. The ledger, observed by diffing the test ids in both
trees rather than reconstructed from memory:

| | |
|---|---|
| Base `c8defe7` | **567** |
| Removed | **7** — `test_loop.ResolveRenderTest` × 6 (the lookup is gone), `test_screen_adapter`'s stand-in-vocabulary test × 1 |
| Added | **46** — `test_scripted_game.py` × 41, `test_curses_pty` × 2, `test_loop` × 2, `test_screen_adapter` × 1 |
| **567 − 7 + 46** | **= 606** |

Two of those pairs are a move and a rename that net to zero and appear on both
sides of the diff; netting them out gives 5 genuinely deleted and 44 genuinely
new, 567 − 5 + 44 = 606. Both framings agree.

The two skips are `test_launch_smoke`'s and are unchanged from `main`; they
need a controlling tty.

## What is not claimed

The perceptual checks are the user's and are not claimed here: the colours
(SCRN-3..6), the absence of flicker and of a visible cursor (SCRN-7), and the
window closing on `q` (WIN-5, human check H2), which I cannot exercise because
I have no controlling tty and will not script keystrokes into somebody else's
application. No Terminal window was opened by this work item.

**A1 remains open** and this branch proceeds on the architect's reading as an
assumption, not a ruling: the last picture stays, `q` exits the process, the
supervisor closes the window then.
