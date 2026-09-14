# WI-3 — the window is not 40 x 30 yet when the game starts looking

Measured while joining the launcher to the real game process. macOS 25.6.0,
Terminal.app, Python 3.9.6.

## The race

`do script` starts the command **at the moment the window is created**. The
launcher's `configure` — the call that makes the window 40 columns by 30 rows —
only runs after that call returns. So there is a window of time in which the
game is running in a terminal that is still the player's profile default size.

That matters because the game checks its size exactly once, at curses start-up
(`TerminalSession.open` → `_check_size`), and fails loudly below 40 x 30. That
loud failure is correct behaviour and the join must not provoke it by accident.

`defaults read com.apple.Terminal` has no rows/columns entry on this machine, so
the profile default is Terminal's built-in **80 x 24**. Twenty-four is three
rows short of what the game requires.

## The margin, measured

One window (id 7681), instrumented on both sides — the launcher recording when
each of its calls completed, the launched process recording the first moment it
could look at the terminal:

| | |
| --- | --- |
| window created | +0.124 s |
| `configure` completed (window now 40 x 30) | +0.316 s |
| launched process's first look at the terminal | +0.823 s |
| what it saw | `30 40` |

**Margin: `configure` completed 0.496 s before the game could look.**

So the race is currently won. But it is won by login-shell start-up latency —
the time the player's `.zshrc` and friends take before the shell becomes the
command — and that is an accident of this machine's profile, not a property of
the design. A player with a fast shell start-up, or a machine under load that
slows `osascript` down, could invert it and get a "screen too small" failure
instead of a game.

## What was done about it

The launched command carries a bounded size gate ahead of the game:

```sh
i=0; while [ $i -lt 60 ]; do set -- $(stty size 2>/dev/null); \
  if [ ${1:-0} -ge 30 ] && [ ${2:-0} -ge 40 ]; then break; fi; \
  i=$((i+1)); sleep 0.1; done
```

It waits for the window to become the size the launcher asked for, then execs
the game. Three properties, all deliberate:

- **Bounded** — sixty attempts at a tenth of a second, six seconds, then it
  stops waiting. Nothing in a launched window may block for ever.
- **It falls through rather than aborting.** On a screen that genuinely is too
  small the game still runs and still reports it loudly. The gate removes a
  race; it must never suppress the failure.
- **`stty size` rather than `tput lines`** — it reads the terminal directly, so
  it needs no `TERM` and no terminfo. If it fails, `set --` leaves the
  positional parameters empty and `${1:-0}` makes that a zero, which fails the
  comparison and costs one more turn of a loop that is bounded anyway.

`stty size` reports **rows first**, which is the easy thing to get backwards;
getting it backwards would wait for a 40-row, 30-column window that the launcher
never asks for, so the gate would always time out. There is a test that passes
distinct values for rows and columns and checks which comparison each lands in.

Behaviour checked against a stubbed `stty` on the `PATH`, with no window
involved:

| `stty size` says | gate |
| --- | --- |
| `30 40` | returns at once (0.37 s, mostly interpreter start-up) |
| `24 80` (too short) | bounds out at the configured limit, then falls through |
| fails outright | bounds out, then falls through |

## A note for whoever revisits window creation

The obvious alternative — create the window empty, size it, and only then run
the game in it — was tried, and it does remove this race. It was **not** adopted,
because it does not remove the other one: a tab that has had its grid set
reports `busy` = false for the whole life of the process in it, whether it was
sized before or after the command started. See
`WI-3-busy-is-false-after-a-grid-resize.md`.
