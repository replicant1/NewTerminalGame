# WI-2 — the game's screen edge can be tested on a pseudo-terminal, and `PENDIN` is the one bit that does not come back

**Measured on** this machine, macOS (Darwin 25.6.0), Python 3.9.6, `TERM=xterm`.
**Reproduce with** `python3 -m unittest tests.test_real_terminal` from the repository root.

## 1. A pseudo-terminal is enough. No window needs to be opened.

Everything the curses adapter does — raw mode, colour, box-drawing glyphs, a whole
frame in one pass, a key read with a timeout, and giving the terminal back — can be
driven and observed on a pseudo-terminal created with `os.openpty()`. **Nothing on
the user's screen is involved**, so none of the window-safety hazards apply: no
window id to capture, no modal sheet to raise, nothing to reap.

The recipe, which is in `tests/test_real_terminal.py` and is reusable by WI-12:

1. `master, slave = os.openpty()`
2. set the size **before** the child starts, or curses reads the default 80 x 24:
   `fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))`
3. `subprocess.Popen([...], stdin=slave, stdout=slave, stderr=PIPE, env={"TERM": "xterm", ...})`
4. read `master` non-blocking (`os.set_blocking(master, False)`), tolerating `EAGAIN`
5. `termios.tcgetattr(slave)` before and after tells you whether the terminal was
   handed back — this is the assertion that matters, and no fake can make it.

Two details that cost time if you do not know them:

- **`LINES` and `COLUMNS` must be removed from the child's environment.** If either
  is set, ncurses believes it over the window size, and the size test silently
  measures the wrong thing.
- **The child's `stderr` must be a pipe, not the pty.** Otherwise the loud
  "window too small" message lands in the middle of the captured screen output
  and cannot be told apart from the picture.

## 2. `PENDIN` is the one termios bit that differs afterwards

After a complete, clean curses session, the terminal's local flags come back **not
quite** identical:

| | `c_lflag` |
| --- | --- |
| before the game | `1483` = `0x5CB` |
| after the game | `536872395` = `0x200005CB` |
| difference (XOR) | `0x20000000` = `termios.PENDIN`, and nothing else |

Every other bit in every other field is identical, `ECHO` and `ICANON` included, and
so are the special characters. This holds for all four exit paths measured: a normal
exit, a `q`, a `SIGTERM`, and the refusal of a too-small terminal.

`PENDIN` is not a mode the player chose. It is the kernel saying it still has typed
input to re-display now that the line discipline is back in canonical mode. It is
**transient state, not a setting**, and a player's shell is not broken by it.

**Consequence for anyone writing a restore test:** compare `c_lflag` with `PENDIN`
masked out, or the test fails on a correct implementation. `PseudoTerminal.modes()`
in `tests/test_real_terminal.py` does exactly that and explains why in place.

## 3. What was actually confirmed in a real terminal

All eight of these were run and observed, not reasoned about:

| Claim | How it was shown |
| --- | --- |
| The frame reaches a real terminal, box-drawing glyphs and all | `╔`, the title and the status text all appear in the captured output |
| The terminal is handed back after a normal exit | `tcgetattr` before == after, `PENDIN` aside |
| The terminal is handed back after `SIGTERM` | same, and the process still dies of the signal (`returncode == -15`) |
| The terminal is handed back after `SIGHUP` | same (`returncode == -1`) |
| The terminal is handed back after a refusal | same, with exit status 2 |
| Nothing typed is echoed (CTRL-5) | `hello there` typed mid-game never appears in the output |
| `q` is acted on at once (CTRL-4) | the process ended in well under a second against a 30-second hold |
| A terminal below 40 x 30 is refused loudly, and nothing is drawn | exit status 2, the message on stderr naming 40, 30 and 24; no picture in the output |

## 4. What is **not** settled here

- **Colour as rendered.** The adapter emits the right colour pairs, and the tests
  confirm the five named colours reach the terminal as five distinct attributes.
  Whether dim yellow reads as *gold* and bold magenta as *pink* to a person
  (SCRN-3 to SCRN-6) is a human check and belongs to WI-14b.
- **Flicker.** One refresh per frame is what the code does and what the tests pin.
  Whether the result looks flicker-free in a real Terminal window (SCRN-7) is a
  human check.
- **The font's glyph coverage.** The glyphs survive the pty. Whether the font in
  the launcher's window has them is WIN-2 and a human check.
