# WI-4 — Driving the real game through a pseudo-terminal

Measured on this machine, `/usr/bin/python3` 3.9.6, macOS 26.6.2 (Darwin
25.6.0, arm64). Written down because **WI-10 will want to run the game
automatically and this is how it can be done without a window, a tty, or a
person** — and because two of the four things below cost an hour each to find
and give no error message at all when you get them wrong.

## The harness

`pty.openpty()`, `TIOCSWINSZ` to 30 × 40, a child process with the slave end
as its stdin and stdout, `TERM=xterm-256color`, and the result handed back
through a temporary file. `curses.initscr()` in the child then sees a real
40 × 30 terminal.

It opens no window, touches nothing on the user's desktop, and needs no
controlling tty of its own. `tests/test_curses_pty.py` is the working version.

## 1. The bottom-right cell — architecture C1, re-measured

| Call, in a real 40 × 30 curses screen | Result |
|---|---|
| `addstr(29, 39, "X")` | raises **`addwstr() returned ERR`** |
| `insstr(29, 39, "X")` | no error |
| `Screen.paint` of a full 30 × 40 picture | no error |
| the screen read back with `inch` | identical to the picture, corner included |

The architect's measurement stands exactly. `insstr` is the fix because it
never moves the cursor, and the cell is genuinely drawn rather than skipped.

## 2. The pty master must be drained while the child runs

**Symptom:** the probe hangs until its timeout with no output, no error and no
traceback.

**Cause:** a full 30 × 40 repaint with colour changes is several kilobytes and
a pty's buffer is not. Nothing was reading the master end, the buffer filled,
and the child blocked in `write` for ever.

**Fix:** a daemon thread reading the master until EOF, started before the
child. Close the slave before the master on the way out so the thread sees
EOF and ends.

This will bite anything that runs the game non-interactively. It is not
specific to curses — any program that writes more than a bufferful will do it.

## 3. Arrow keys are `ESC O C`, not `ESC [ C`

This is the one worth the document on its own.

`keypad(True)` makes ncurses emit `smkx`, which is
`\033[?1h\033=` — it puts the terminal into **application cursor mode**. From
that moment a real terminal sends `ESC O C` for the right arrow, not the
`ESC [ C` that everybody types from memory.

**Measured.** Feeding `ESC [ C ESC [ C ESC [ B z q` to the pty and reading
with `getch` gave:

```
[27, 91, 67, 27, 91, 67, 27, 91, 66, 122]
```

— ten separate key codes, no `KEY_RIGHT` anywhere. The game looks completely
broken and the fault is entirely in the test harness.

The four sequences, from `xterm-256color` terminfo:

| Key | Capability | Bytes |
|---|---|---|
| up | `kcuu1` | `\033OA` |
| down | `kcud1` | `\033OB` |
| left | `kcub1` | `\033OD` |
| right | `kcuf1` | `\033OC` |

**Read them out of terminfo rather than typing them** —
`curses.setupterm("xterm-256color")` then `curses.tigetstr("kcuf1")`. That
works without a tty and cannot go stale against a different `TERM`.

## 4. Keystrokes can be queued before the child starts

Writing the whole script to the master **before** launching the child works:
the bytes sit in the terminal's input queue and `getch` finds them waiting.
There is no timing to get right and nothing to be flaky about.

This matters for the same reason rule 4 of plan §2.6 does: a driven game that
has already been told how it ends cannot be left blocking with no way to end
it. The scripted run in `tests/test_curses_pty.py` ends its script with `q`,
so the loop returns on its own.

## What this makes possible

A whole game can be played automatically, through the real adapter and real
ncurses, with the real key decoding, and asserted on afterwards:

```
right, down-into-a-wall, right, right, right, down, z, q
  -> player (1,1) ends at (2,5), score 3, loop returned
```

That is CTRL-1, CTRL-3, CTRL-4, CTRL-5 and END-6 in one run of the real thing
with no fakes anywhere. WI-10 can extend the same harness to a full win and a
full loss without ever opening a window or asking a person to press anything.

What it still cannot do is judge **H5** (flicker) or **H6** (the picture
looking right). Those remain a person's.
