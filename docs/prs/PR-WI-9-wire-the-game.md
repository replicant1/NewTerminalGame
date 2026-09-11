# WI-9 — Wire the real game together

**Branch** `wi-9-wire-the-game` · **base** `main` at `c8defe7` · Dev A, round 5,
iteration M2.

*Draft: the wiring is in and the suite is green. The scripted full game — a win,
two losses, and the after-the-ending behaviour — is still being written.*

## What this does

The three seams WI-4 built are filled with the things they were built for.

| Seam | Was | Is |
|---|---|---|
| starting state | `standins.new_game` | `rules.new_game` |
| picture | `loop.resolve_render()` — a run-time module lookup | `view.render`, plainly imported |
| player transition | `standins.move_player` | `rules.move_player` |
| ghost transition | `standins.move_ghost` (did nothing) | `rules.move_ghost` |

`termgame/standins.py` is deleted. `loop.resolve_render` is deleted.
`run_loop` itself is byte-for-byte unchanged, which was the whole point of its
taking those four things as parameters.

**The `Terminal Game` child executable did not change.** It calls
`termgame.loop.run_game()` and nothing else, and that is still the entry point.
The seam WI-2 built was in the right place.

## Files

- `termgame/loop.py` — `run_game` builds a real game and drives the loop with
  the real renderer and the real transitions; `resolve_render` gone.
- `termgame/standins.py` — **deleted**.
- `tests/test_loop.py` — the six `ResolveRenderTest` cases replaced by three that
  pin the plain import; a local `a_plain_step` transition replaces
  `standins.move_player` in the loop's own tests, on purpose (see below).
- `tests/test_curses_pty.py` — the real-ncurses scripted run now drives the
  **real** rules and the **real** renderer.
- `tests/test_screen_adapter.py` — the fallback palette is now checked against
  what the real renderer emits for a real game.

## Suite

```
/usr/bin/python3 -m unittest discover -s tests
Ran 566 tests in 11.233s
OK (skipped=2)
```

`main` is 567 / 2 skipped. The arithmetic: −3 (six `resolve_render` fake-lookup
cases become three that pin the plain import), +2 (the pty run now asserts a
real outcome and the real status line). 567 − 3 + 2 = 566. The two skips are
unchanged and are `test_launch_smoke`'s, which need a controlling tty.

## Mutation checks

not applicable — not part of this workflow

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
