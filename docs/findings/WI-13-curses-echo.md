# WI-13 — where ncurses' echo actually is, and why the obvious test cannot fail

**Measured** on macOS 26.6.2 (Darwin 25.6.0), `/usr/bin/python3`, `TERM=xterm-256color`,
against a 40 x 30 `pty.openpty()`, in this worktree, on 2026-09-11.

This exists because CTRL-5's second clause — *"nothing typed is echoed into the
maze"* — had no test at all, and the first two ways of writing one that look
obviously right are both **hollow**. The third works. Anyone who touches
`termgame/screen.py`'s `session()`, or who is tempted to simplify
`NothingTypedIsEchoedTest` in `tests/test_curses_pty.py`, needs these three
measurements or they will reintroduce a test that cannot fail.

---

## 1. The tty's own ECHO bit says nothing about the game

A pty is created with `ECHO` set in the line discipline. The obvious test is to
read `termios.tcgetattr(0)[3] & termios.ECHO` from inside the game's session
and assert it is clear.

Probe: set `ECHO` on the slave, start a child on it, and read the bit after
each curses call.

```
{"before_initscr": true,
 "after_initscr": false,
 "after_cbreak": false,
 "after_noecho": false,
 "after_keypad": false}
```

**`curses.initscr()` clears the bit by itself**, before `noecho()` is reached.
And going the other way:

```
after_initscr: false   after_noecho_cbreak: false   after_curses_echo: false
```

**`curses.echo()` never sets it back.** ncurses does not use the line
discipline's echo at all: it echoes in software, from inside `wgetch`, by
calling `wechochar` on the window. So the ECHO bit is *always* clear inside a
curses session, whatever the game does, and an assertion on it passes
unconditionally.

This was caught the only way it could be — by deleting
`curses.noecho()` from `session()` and finding the new test still green.

## 2. A painted screen swallows the echo, at the bottom-right cell

The second obvious test is to capture everything the game writes to its
terminal and assert the typed character never appears. That works — but **not
in the scripted game**, and the reason is this project's own C1 hazard.

`wechochar` writes the character *at the cursor*, and after
`Screen.paint` the cursor is parked on the bottom-right cell, because the last
thing paint does there is an `insstr` that does not move it. Writing at that
cell cannot advance the cursor, so the echo goes nowhere.

Probe, three `z`s typed, a picture containing no `z`, with `curses.echo()`
forced on:

| what the child did before reading | `z`s that reached the terminal |
| --- | --- |
| nothing | **3** |
| `Screen.paint` of a full 30 x 40 picture | **1** |
| `Screen.paint`, then `move(5, 5)` | **3** |

And in the real scripted game, with `curses.echo()` added to `session()` on
purpose: **0**. So `ScriptedGameThroughRealCursesTest` cannot see this clause
at all, in either direction.

**This is worth knowing beyond the test.** CTRL-5's echo clause currently holds
for *two* independent reasons — `noecho()`, and the corner swallowing whatever
`noecho()` might have missed. That is not a defect and nothing needs changing;
it is why the requirement looks untestable from the game and is not.

## 3. What does work: the real session, with nothing painted in front of it

`tests/test_curses_pty.py::NothingTypedIsEchoedTest` enters the game's own
`screen.session()`, reads three keystrokes through the adapter's own
`Screen.read_key`, and paints nothing. The pty's line-discipline `ECHO` is
cleared before the keystrokes are written, so anything that comes back is the
game's doing.

Deleting `curses.noecho()` from `session()` turns it red, and the failure
prints the evidence:

```
AssertionError: b'z' unexpectedly found in
b'\x1b[?1049h ... \x1b[H\x1b[2Jzzz\x1b[?1l ...'
: the keystrokes the player typed were echoed back into the window:
`z` appears 3 times in what the game wrote to the terminal (CTRL-5)
```

## 4. The document this corrects

`docs/ARCHITECTURE.md` recorded CTRL-5 as *"measured: `noecho` set in
`Screen.__enter__`"*. There is no `Screen.__enter__` — the adapter uses a
`session()` context manager — and nothing was measured. WI-13 rewrites that
cell to say what is now actually true, and points at this file.
