"""The game loop -- and, in M0, the placeholder behind it.

IMPURE. ``run_game`` is the single entry point the ``Terminal Game``
executable calls. WI-4 replaces the body with the real loop and its one
deadline, and WI-9 wires the real game in; **neither needs to touch the
executable**, which is the whole point of the entry point being here.

What M0 needs from this module is only enough to prove the window: paint a
static screen and return when the player presses ``q`` (END-6, WIN-5).

It does not import ``curses`` -- ``screen.py`` is the only module allowed to,
and it does not exist yet. The placeholder writes plain text, which is also why
it stays off the bottom-right cell (ARCHITECTURE.md C1: a write to the last
cell of the last row scrolls a plain terminal and raises under curses).
"""

import os
import sys

COLUMNS = 40
ROWS = 30

#: Clears the screen and homes the cursor; hides the cursor.
_CLEAR = "\033[2J\033[H\033[?25l"
#: Shows the cursor again on the way out.
_RESTORE = "\033[?25h"


def placeholder_screen(columns=COLUMNS, rows=ROWS, size_label=""):
    """The M0 static picture, as *rows* strings of exactly *columns* chars.

    Pure. WI-3 lands the real picture; nothing here is meant to survive it.
    """
    lines = []
    body = [
        "",
        "TERMINAL GAME",
        "",
        "placeholder screen (WI-2, milestone M0)",
        "",
        "the maze arrives with WI-3 and WI-9",
        "",
        size_label,
        "",
        "press q to quit",
    ]
    top = "+" + "-" * max(0, columns - 2) + "+"
    lines.append(top[:columns])
    interior = max(0, rows - 2)
    first_text_row = max(0, (interior - len(body)) // 2)
    for index in range(interior):
        text = ""
        if first_text_row <= index < first_text_row + len(body):
            text = body[index - first_text_row]
        lines.append(_framed(text, columns))
    if rows >= 2:
        lines.append(top[:columns])
    return [line[:columns].ljust(columns) for line in lines[:rows]]


def _framed(text, columns):
    inner_width = max(0, columns - 2)
    text = text[:inner_width]
    padding = inner_width - len(text)
    left = padding // 2
    right = padding - left
    return "|" + " " * left + text + " " * right + "|"


def paint(lines, stream=None):
    """Write the picture, never touching the last cell of the last row."""
    stream = sys.stdout if stream is None else stream
    stream.write(_CLEAR)
    last = len(lines) - 1
    for index, line in enumerate(lines):
        if index == last:
            line = line[:-1]  # ARCHITECTURE.md C1: stay off the corner cell
        stream.write("\033[%d;1H%s" % (index + 1, line))
    stream.flush()


def size_label():
    try:
        size = os.get_terminal_size()
        return "%d columns x %d rows" % (size.columns, size.lines)
    except OSError:
        return ""


def run_game():
    """The entry point ``Terminal Game`` calls. Returns a process exit code.

    M0: paint once, wait for ``q``. Returns immediately when there is no
    controlling terminal -- an agent running this must never leave a process
    blocking forever in a window nobody can close.
    """
    try:
        paint(placeholder_screen(size_label=size_label()))
        return wait_for_quit()
    finally:
        sys.stdout.write(_RESTORE)
        sys.stdout.flush()


def wait_for_quit(stream=None):
    """Block until ``q``, ``Q``, Ctrl-C or end of input. Returns 0."""
    stream = sys.stdin if stream is None else stream
    try:
        fd = stream.fileno()
    except (AttributeError, ValueError, OSError):
        return 0
    if not os.isatty(fd):
        return 0

    import termios
    import tty

    saved = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            char = os.read(fd, 1)
            if not char:
                return 0
            if char in (b"q", b"Q", b"\x03", b"\x04"):
                return 0
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
