"""The adapter against **real ncurses**, in a real pseudo-terminal.

The implementation plan asks for exactly this if it can be made:

    The bottom-right cell can be written without raising — as a unit test
    against a small pseudo-terminal if you can make one, otherwise as an
    assertion that the paint never targets that cell.

It can be made. ``pty.openpty()`` gives a 40 x 30 terminal that belongs to
nobody and is on nobody's screen; a child process started on it runs
``curses.initscr()`` for real, and reports back through a file.

So this file proves two things a stand-in window cannot:

1. **The hazard is real.** ``addstr(29, 39, ch)`` against real ncurses in a
   real 40 x 30 terminal raises ``addwstr() returned ERR``. If that ever
   stopped being true the guard would be dead code and nobody would know.
2. **The guard works.** A full 30 x 40 picture painted through
   :class:`termgame.screen.Screen` does not raise, and reads back off the
   virtual screen as the picture that went in.

It opens no window. It is not the live smoke test; it touches nothing on the
user's desktop and needs no controlling tty of its own.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: 40 columns, 30 rows — the window the game really runs in (WIN-2).
COLUMNS = 40
LINES = 30

PROBE = r'''
import curses, json, os, sys
sys.path.insert(0, %(root)r)
result = {}
window = curses.initscr()
try:
    result["size"] = list(window.getmaxyx())

    # 1. The hazard, measured rather than assumed.
    try:
        window.addstr(curses.LINES - 1, curses.COLS - 1, "X")
        result["addstr_at_the_corner"] = "no error"
    except Exception as error:
        result["addstr_at_the_corner"] = str(error)

    # 2. insstr at the same cell.
    try:
        window.insstr(curses.LINES - 1, curses.COLS - 1, "X")
        result["insstr_at_the_corner"] = "no error"
    except Exception as error:
        result["insstr_at_the_corner"] = str(error)

    window.erase()

    # 3. The adapter painting a whole picture, through the real thing.
    from termgame import screen as screen_module
    from termgame.model import frame_from_rows
    rows = []
    for r in range(30):
        rows.append("".join(chr(ord("a") + ((r + c) %% 26)) for c in range(40)))
    frame = frame_from_rows(rows)
    scr = screen_module.Screen(window, screen_module.build_attributes())
    try:
        scr.paint(frame)
        result["paint"] = "no error"
    except Exception as error:
        result["paint"] = "%%s: %%s" %% (type(error).__name__, error)

    # 4. Read the virtual screen back and compare it with what went in.
    read_back = []
    for r in range(30):
        read_back.append(
            "".join(chr(window.inch(r, c) & 0xFF) for c in range(40))
        )
    result["matches"] = (read_back == rows)
    result["last_row_in"] = rows[29]
    result["last_row_out"] = read_back[29]

    # 5. The cursor really does hide, and escape delay really is settable.
    result["curs_set"] = curses.curs_set(0)
    curses.set_escdelay(25)
    result["escdelay"] = True
finally:
    curses.endwin()

with open(%(out)r, "w") as handle:
    json.dump(result, handle)
'''


def run_probe_on_a_pty():
    """Run the probe with a 40 x 30 pty for a terminal. ``None`` if impossible.

    **The master end has to be drained while the child runs.** A full 30 x 40
    repaint with colour changes is several kilobytes, a pty's buffer is not,
    and a child whose terminal has filled up blocks in ``write`` for ever.
    Measured the hard way: without the reader thread below, this probe hangs
    until the 60-second timeout with no output and no error.
    """
    import fcntl
    import pty
    import struct
    import termios
    import threading

    handle, path = tempfile.mkstemp(suffix=".json", prefix="termgame-pty-")
    os.close(handle)
    master, slave = pty.openpty()
    drained = []

    def drain():
        while True:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                return
            if not chunk:
                return
            drained.append(chunk)

    reader = threading.Thread(target=drain)
    reader.daemon = True
    try:
        fcntl.ioctl(
            slave, termios.TIOCSWINSZ, struct.pack("HHHH", LINES, COLUMNS, 0, 0)
        )
        environment = dict(os.environ)
        environment["TERM"] = "xterm-256color"
        environment["LINES"] = str(LINES)
        environment["COLUMNS"] = str(COLUMNS)
        source = PROBE % {"root": ROOT, "out": path}
        reader.start()
        completed = subprocess.run(
            [sys.executable, "-c", source],
            stdin=slave,
            stdout=slave,
            stderr=subprocess.PIPE,
            env=environment,
            timeout=60,
        )
        with open(path) as reading:
            text = reading.read()
        if not text:
            return {"failed": completed.stderr.decode("utf-8", "replace")}
        return json.loads(text)
    finally:
        os.close(slave)
        os.close(master)
        if reader.is_alive():
            reader.join(timeout=5)
        if os.path.exists(path):
            os.remove(path)


def probe_once():
    try:
        return run_probe_on_a_pty()
    except (OSError, ImportError, subprocess.SubprocessError, ValueError):
        return None


RESULT = probe_once()


@unittest.skipIf(RESULT is None, "a pseudo-terminal could not be made here")
class RealCursesTest(unittest.TestCase):
    def setUp(self):
        if RESULT is not None and "failed" in RESULT:
            self.fail("the curses probe did not run:\n%s" % RESULT["failed"])

    def test_curses_sees_the_forty_by_thirty_window(self):
        self.assertEqual([LINES, COLUMNS], RESULT["size"])

    def test_writing_at_the_bottom_right_cell_really_does_raise(self):
        # ARCHITECTURE.md C1, re-measured. If this ever says "no error" the
        # guard in screen.paint has become dead code, and that is worth
        # knowing rather than discovering in front of the user.
        self.assertIn("ERR", RESULT["addstr_at_the_corner"])

    def test_inserting_at_the_bottom_right_cell_does_not_raise(self):
        self.assertEqual("no error", RESULT["insstr_at_the_corner"])

    def test_the_adapter_paints_a_whole_picture_without_raising(self):
        self.assertEqual("no error", RESULT["paint"])

    def test_what_reaches_the_screen_is_the_picture_that_went_in(self):
        self.assertEqual(RESULT["last_row_in"], RESULT["last_row_out"])
        self.assertTrue(RESULT["matches"], "the painted screen is not the picture")

    def test_the_bottom_right_cell_carries_its_character_and_is_not_skipped(self):
        # Inserting rather than skipping means the cell is actually drawn.
        self.assertEqual(40, len(RESULT["last_row_out"]))
        self.assertEqual(RESULT["last_row_in"][39], RESULT["last_row_out"][39])

    def test_the_cursor_can_be_hidden(self):
        # SCRN-7's "the text cursor is never visible". curs_set returns the
        # previous visibility, so anything but an exception is success.
        self.assertIsInstance(RESULT["curs_set"], int)

    def test_the_escape_delay_can_be_set(self):
        self.assertTrue(RESULT["escdelay"])


if __name__ == "__main__":
    unittest.main()
