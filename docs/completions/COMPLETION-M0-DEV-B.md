# COMPLETION — M0, Dev B

The M0 lane for Dev B is two work items: **WI-2**, the window and the
launcher, and **WI-4**, the curses adapter and the loop. One note per lane per
iteration (plan §2.5), so both are here, WI-2 first.

---

## WI-2 — the window, the launcher and the two executables

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

---

## WI-4 — the curses adapter and the loop with its one deadline

**Work item** WI-4, the curses adapter and the loop with its one deadline.
**Branch** `wi-4-adapter-loop`, cut from `main` at `c75f052`, with `main`
merged in once WI-3 landed.
**Pull request** #7, `--base main`.
**Lands** SCRN-7, CTRL-1, CTRL-2, CTRL-4, CTRL-5, GHOST-1 (the deadline),
START-5 (painted before the first read), END-6.

### What was finished

- `termgame/controls.py` — **pure.** What a key code means. The arrows to
  directions, `q` and `Q` to quit, and every other key on the keyboard to
  nothing.
- `termgame/ticker.py` — **pure.** When the tick is due, how long to wait for
  a key, and the additive deadline advance. The time arrives as a parameter;
  the module imports no clock, so GHOST-1 is testable without waiting for it.
- `termgame/screen.py` — **impure, and the only module in the repository that
  imports `curses`.** Enter and leave curses safely, `noecho`, `cbreak`,
  `keypad`, `curs_set(0)`, `set_escdelay(25)`, paint a `Frame`, read a key
  with a timeout. It holds no decision about the game.
- `termgame/loop.py` — **impure.** The loop, taking its screen, clock,
  renderer and transitions as parameters so a fake screen and a fake clock can
  drive it. `run_game` is the entry point the `Terminal Game` executable calls,
  and that executable did not have to change.
- `termgame/standins.py` — **pure, and WI-9 deletes it.** A starting state, a
  player step, a ghost that does nothing, and a crude picture — so the M0 demo
  moves, which is what proves the seam.

WI-2's placeholder screen and its nine tests are gone with the body they
tested.

### The test suite as I left it

```
/usr/bin/python3 -m unittest discover -s tests
Ran 368 tests in 6.980s
OK (skipped=2)
```

The same 368 / 2 on `/opt/homebrew/bin/python3` 3.14.7, as the cross-check.
The two skips are `tests/test_launch_smoke.py`, guarded on a controlling tty,
exactly as WI-2 left them. `main` stood at **258 / 2** after WI-3; this branch
adds 119 tests and removes WI-2's nine placeholder ones.

Nothing in this branch opens a window when it runs. **No Terminal window was
opened by this work item at all**, so the census is unchanged by construction.

### The two things worth keeping from it

1. **C1 is now measured rather than trusted.** `tests/test_curses_pty.py`
   runs the adapter against real ncurses on a real 40 × 30 pseudo-terminal:
   `addstr(29, 39, ch)` raises `addwstr() returned ERR`, `insstr` at the same
   cell does not, a full 30 × 40 paint through the adapter is clean, and the
   screen reads back character for character including the corner cell. If
   the hazard ever stopped being real the guard would quietly be dead code.
2. **`int(remaining * 1000)` loses up to a millisecond on a dirty float.**
   `int((10.1 - 10.0) * 1000)` is 99, not 100. The architecture's truncating
   form is what is shipped — it is what the 6.997 ticks/s measurement was
   taken with, and truncation can only wake *early* — but it costs one extra
   turn of the loop per tick, and it is why nothing asserts an exact
   millisecond against a value that is not exact in binary.

### Deviations needing a ruling

1. **WI-2's nine placeholder tests are deleted** along with the body they
   tested. Everything they protected is protected better elsewhere.
2. **`run_game` paints on the no-terminal path.** WI-2 returned silently;
   this writes one frame as plain text and returns. Additive.
3. **The loop looks its renderer up rather than importing it.** WI-3 and WI-4
   were built in parallel, so the import could not be written at the time.
   WI-9 should replace `loop.resolve_render` with a plain import.

### Still needs a human

**H5 — no flicker while the ghost moves.** Perceptual, not claimed here. The
design rests on one `addstr` per cell and one `refresh`, with ncurses diffing
its virtual screen against the physical one, and no `erase()` before the
paint. H6 is WI-3's, but the colours the adapter applies are read from
`termgame/theme.py`, so a change after H6 lands in that pure module.
