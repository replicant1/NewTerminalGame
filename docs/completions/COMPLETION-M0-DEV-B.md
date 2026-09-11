# COMPLETION — M0, Dev B — WI-2

**Work item** WI-2, the window, the launcher and the two executables.
**Branch** `wi-2-window-launcher`, based on `main` at `436dfa5`.
**Pull request** #4, `--base main`, marked ready.
**Lands** WIN-1, WIN-2, WIN-3, WIN-4, WIN-5 — subject to the human checks below.

## What was finished

- `play` — the supervisor. Reads the reference position (tty match, then the
  frontmost visible window, then a fixed position), opens the game window,
  captures its id at creation, sizes and titles it, places it below and right
  of the reference on that reference's own display, waits for the game to end,
  and closes that window by that id on the success and the failure path alike.
- `Terminal Game` — the child, named literally, invoked with no arguments,
  emitting `\033]7;\007` as its first write. Its body is one call into
  `termgame.loop.run_game`, which in M0 paints a static screen and returns on
  `q`. WI-4 and WI-9 replace that body without touching the executable.
- `termgame/window.py` — the AppleScript island, the only `osascript` caller.
- `docs/findings/WI-2-terminal-window-id.md` — every incantation tried, with
  the exact error text, for WI-8 and WI-10.

## The test suite as I left it

```
/usr/bin/python3 -m unittest discover -s tests
Ran 90 tests in 1.692s
OK (skipped=2)
```

The two skips are `tests/test_launch_smoke.py`, guarded on there being a
controlling tty. Its body was run once with the guard lifted, against the real
Terminal: 2 tests, ok, and Terminal's visible windows were `[367, 2486]` before
and after.

No test in this branch opens a window when it runs in an agent session.

## Two contradictions with the architecture, both measured

1. **WIN-5 cannot poll `busy`** — it is false for the whole of a running game,
   so the prescribed poll closes the window a second after opening it. The
   signal is now `busy or (count of processes of tab 1) > 0`.
2. **WIN-4's coordinates** — AppleScript's window positions and
   `CGDisplayBounds` differ by a constant 1440 in y on this three-display
   machine, and reading one as the other put the game window on a display the
   player was not using.

Both are written up with the numbers in `docs/findings/WI-2-terminal-window-id.md`
and in the PR body.

## Open question touching this work item

**A1 is unanswered.** This branch proceeds on the architect's assumption — the
last picture stays, `q` exits the child, the supervisor closes the window then.
Recorded as an assumption, not a ruling. If the user answers the other way it is
one wait removed from the supervisor, and WI-11 applies it.

## Still needs a human

H1 (WIN-4), H2 (WIN-5), H3 (WIN-3) and H4 (WIN-2, font size). None of them is
reported as done here. H1 and H2 are worth running on a multi-display machine.
