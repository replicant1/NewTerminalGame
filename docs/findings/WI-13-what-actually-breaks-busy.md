# WI-13 — what actually breaks `busy`, and how the fix was proved

**Item:** WI-13, launcher robustness. **Lane:** DEV-B, iteration M2.
**Measured on:** `wi-13-launcher-robustness` at `f180d1b`, macOS, Terminal.app, Python 3.9.6.
**Windows opened for these measurements: 15. Every one closed; census returned every time.**

This follows `docs/findings/WI-3-busy-is-false-after-a-grid-resize.md`, which found the defect. It
**confirms it, refines its cause, and proves the fix** — and the refinement matters more than it
sounds.

## The refinement: it takes both the grid *and* the game

WI-3 attributes the defect to the grid: *"Font, colours and title are all harmless; it is the grid
alone, and WIN-2 requires the grid."*

**The first thing I measured contradicted that.** One window, `sleep 6`, the full 40 × 30
`configure_window` applied: `busy` reported **true** for the entire life of the process and went false
exactly when it ended. The defect did not reproduce.

So rather than report a fix to a defect I could not reproduce, I ran the four cells — one window each,
the same polling, the same configure call:

| command | grid applied? | samples where `busy` said false while something ran |
| --- | --- | --- |
| `sleep` | no | **0** of 9 |
| `sleep` | yes | **0** of 8 |
| the real game command | no | **0** of 15 |
| the real game command | yes | **8 of 9** |

**Both are needed. Neither alone does it.** The grid is necessary and not sufficient.

Why it matters, and it is not pedantry:

- Anyone who tries to preserve `busy` by **not setting the grid** would test it with a simple command,
  see it work, and ship a launcher that fails on the real game.
- Anyone who tests the **grid** with a simple command concludes `busy` is fine.
- Both roads lead back to a launcher that kills the game and reports success.

**What I did not establish is the true cause.** The real command differs from `sleep` in more than one
way — it waits on `stty size`, it runs under `/bin/sh -c`, and it puts the terminal into curses raw
mode. Raw mode is my suspicion and I have not tested it, so it stays a suspicion. What is established
is the *combination*, which is what an implementer needs.

## The confirmation

With `launcher.game.game_command()` — what production actually sends — the defect reproduces exactly,
twice:

```
   t(s)   busy    processes
   0.33   true    login|-zsh|ssh-add
   0.75   false   login|Python        <== busy says false while it runs
   ...                                    (9 such samples)
   4.25   false   login|Python        <== and still running
   4.68   false   (none)
```

**The process list was accurate across the whole span**, non-empty from +0.33 s to +4.2 s and empty
after — and, in both trials, **never once empty while something was running**. That last is the
property `has_live_processes` depends on, and it is the one I most expected to find broken.

**An earlier probe of mine did see an empty list at +0.33 s, and it was my error, not the launcher's.**
`do script` starts in the player's home directory, where `python3 -m terminalgame.game_main` is not
importable, so the game died instantly and the empty list was honest. Worth recording because the
symptom — "the process list says nothing is running while the game is starting" — is exactly what a
real start-up race would look like, and it would have sent the next person down a long road.

## The fix, proved rather than asserted

WI-3 gave the defect a signature: *"a whole session then takes the same 1.0 s whether the game was
asked to run for 5 seconds or for 12, because in both cases it was killed and the launcher said
`closed`."*

So the fix is proved by the session time tracking the game. Through `launcher.game.play` — the
production path, not a test double:

| hold asked for | session took | reported |
| --- | --- | --- |
| 3 s | **4.04 s** | `closed=True` |
| 8 s | **9.03 s** | `closed=True` |

**Holds differ by 5 s; sessions differ by 4.99 s.** The game runs its full length and the window is
closed cleanly afterwards. Before the fix both rows would have read ≈1.0 s.

## What changed in the code, and why deletion rather than deprecation

`wait_until_idle` now defaults to `has_live_processes`, and `run` inherits it. That alone would have
fixed the session.

**`Desktop.is_busy` and `script.window_is_busy` were deleted outright.** Two things in one system
answering *"is the command still running"* differently is the trap — and this defect is the proof of
how it plays out. Both existed for the whole of WI-3, the correct one was documented at length in a
warning, and **the wrong one was still the default**, so the defect survived being thoroughly
understood. A warning is not a guard.

The warning docstring went with it. A warning that outlives its defect teaches readers that warnings
in this code are not to be believed. What it *knew* is kept — `run` still says what it waits on and
why, and there is a test that it does.

## Machine safety, as practised

Every probe: the window id captured at the moment of creation and **only that id ever named**; a
command that ends by itself; polling for a fixed span so nothing was decided early; the close only
after the process list was empty; verified with `visible`, never `exists`; the reap in a `finally` so
it ran on the failure path too; and **never a close while something was running** — a probe that found
the command still alive at its bound left the window open and named its id.

**15 windows opened, 15 closed, and the visible-window census returned to its starting value after
every single probe.** No modal sheet was raised at any point.

## What this does not establish

- **Not the true cause** — see above. The combination is measured; the mechanism is not.
- **Nothing about a refused Automation permission.** Q2 stands: no agent can grant or verify it, and it
  remains a human check on WI-14b. Every measurement here was taken on a machine where permission had
  already been granted.
- **Nothing about `q`.** These sessions ended because the game's `--hold` ran out, not because a person
  pressed a key. Whether a human pressing `q` ends the session cleanly is WI-14b's to check.
- **Nothing about what the window looked like.** Font coverage and colour legibility remain human
  checks and are recorded nowhere as verified.
