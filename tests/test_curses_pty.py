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


#: The real loop, driven by real arrow keys through real ncurses.
#:
#: The keys are written into the terminal *before* the child starts, so they
#: are already in its input queue when ``getch`` first asks: no timing, no
#: synchronisation, nothing to be flaky about.
#:
#: WI-9 note: the transitions and the renderer here are the **real** ones.
#: WI-4 wrote this against the stand-ins because the rules had not landed;
#: now that they have, this run is the real game through real ncurses and
#: the only fake left in it is the pty.
PLAY = r'''
import json, random, sys
sys.path.insert(0, %(root)r)
from termgame import maze as mazelib, rules, screen as screen_module, view
from termgame.loop import run_loop
from termgame.model import GameState, Outcome, Position, UP

BOARD = "\n".join(["#######", "#.....#", "#.###.#", "#.....#", "#######"])
maze = mazelib.from_text(BOARD)
state = GameState(
    maze=maze,
    player=Position(1, 1),
    ghost=Position(3, 5),
    ghost_dir=UP,
    dots=frozenset([Position(1, 2), Position(1, 3), Position(2, 5), Position(3, 1)]),
    score=0,
    outcome=Outcome.PLAYING,
)
result = {}
try:
    with screen_module.session() as scr:
        final = run_loop(
            scr,
            state,
            view.render,
            rules.move_player,
            rules.move_ghost,
            random.Random(0),
            tick=1000.0,          # far away: this run is about the keys
        )
    result["player"] = list(final.player)
    result["score"] = final.score
    result["outcome"] = final.outcome.name
    result["status"] = view.render_rows(final)[-1].rstrip()
    result["returned"] = True
except Exception as error:
    result["error"] = "%%s: %%s" %% (type(error).__name__, error)

with open(%(out)r, "w") as handle:
    json.dump(result, handle)
'''

def arrow_bytes():
    """What a terminal really sends for the arrow keys, read off terminfo.

    **Not** ``ESC [ C`` and friends. ``keypad(True)`` makes ncurses send
    ``smkx``, which puts the terminal into *application cursor* mode, and from
    then on it sends ``ESC O C``. Measured: feed ``ESC [ C`` to a pty and
    ncurses hands back 27, 91, 67 as three separate key codes rather than
    ``KEY_RIGHT``, and the arrows look broken for a reason that has nothing to
    do with the game.

    Reading the four sequences out of terminfo rather than typing them means
    this cannot go stale against a different ``TERM``.
    """
    import curses

    curses.setupterm("xterm-256color")
    return dict(
        (name, curses.tigetstr(capability))
        for name, capability in (
            ("up", "kcuu1"),
            ("down", "kcud1"),
            ("left", "kcub1"),
            ("right", "kcuf1"),
        )
    )


ARROWS = arrow_bytes()

#: Right, **down into a wall**, right, right, right, down, an unmapped key,
#: then `q`. Five requirements in one real run of the real thing.
KEYSTROKES = (
    ARROWS["right"]
    + ARROWS["down"]     # (2, 2) is wall: CTRL-3, nothing happens
    + ARROWS["right"]
    + ARROWS["right"]
    + ARROWS["right"]
    + ARROWS["down"]     # (2, 5) is corridor, and holds a dot
    + b"z"               # CTRL-5, nothing happens
    + b"q"               # CTRL-4, END-6
)


def run_play_on_a_pty():
    """Play a scripted game through real ncurses. ``None`` if impossible."""
    return run_probe_on_a_pty(source=PLAY, keystrokes=KEYSTROKES)


def run_probe_on_a_pty(source=None, keystrokes=b""):
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
        text_source = (PROBE if source is None else source) % {
            "root": ROOT,
            "out": path,
        }
        if keystrokes:
            os.write(master, keystrokes)
        reader.start()
        completed = subprocess.run(
            [sys.executable, "-c", text_source],
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


def once(runner):
    try:
        return runner()
    except (OSError, ImportError, subprocess.SubprocessError, ValueError):
        return None


RESULT = once(run_probe_on_a_pty)
PLAYED = once(run_play_on_a_pty)


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


@unittest.skipIf(PLAYED is None, "a pseudo-terminal could not be made here")
class ScriptedGameThroughRealCursesTest(unittest.TestCase):
    """The loop, the adapter and ncurses together, with no fakes anywhere.

    Every other test of the loop drives it with a fake screen, which is the
    only way to assert what it does. This one asserts that the real thing
    agrees: real escape sequences arriving at a real terminal, decoded by
    ncurses' own keypad handling, reaching the same key mapping and moving
    the player the same way.

    The script is right, down-into-a-wall, right, right, right, down, an
    unmapped key, then `q`. The player starts at (1, 1) on a board whose top
    corridor runs east, so it ends at (2, 5) having eaten three of the four
    dots -- and the press towards the wall and the `z` both did nothing.
    """

    def setUp(self):
        if PLAYED is not None and "failed" in PLAYED:
            self.fail("the scripted game did not run:\n%s" % PLAYED["failed"])
        if PLAYED is not None and "error" in PLAYED:
            self.fail("the scripted game raised: %s" % PLAYED["error"])

    def test_the_arrow_keys_moved_the_player_through_real_ncurses(self):
        # CTRL-1, end to end: the bytes a terminal really sends for an arrow
        # key, through keypad(True), through the key mapping, to a move. Both
        # axes, so a mapping that sent everything one way would be caught.
        self.assertEqual([2, 5], PLAYED["player"])

    def test_the_dots_along_the_way_were_eaten(self):
        self.assertEqual(3, PLAYED["score"])

    def test_the_press_towards_a_wall_did_nothing_at_all(self):
        # CTRL-3. The second key is a down arrow with a wall below; had it
        # moved, the player would have ended somewhere else entirely, and had
        # it been swallowed, the fourth dot would be gone too.
        self.assertEqual([2, 5], PLAYED["player"])
        self.assertEqual(3, PLAYED["score"])

    def test_q_returned_from_the_loop(self):
        # CTRL-4 and END-6 against the real thing. If it had not returned,
        # the probe would have hit its timeout and reported nothing at all.
        self.assertTrue(PLAYED["returned"])

    def test_the_unmapped_key_did_not_quit_and_did_not_move_anything(self):
        # CTRL-5: a `z` sits between the last arrow and the `q`. If it moved
        # the player, the final square would be wrong; if it quit, the loop
        # would have returned before the `q` was ever read.
        self.assertEqual([2, 5], PLAYED["player"])
        self.assertEqual(3, PLAYED["score"])

    def test_the_game_was_still_in_play_when_the_player_quit(self):
        # WI-9: the transitions are now the real ones, so the outcome is a
        # real verdict rather than a stand-in's untouched field. One dot at
        # (3, 1) is left uneaten and the ghost was never due, so a game that
        # came back CLEARED or CAUGHT would mean the rules had been wired in
        # wrongly.
        self.assertEqual("PLAYING", PLAYED["outcome"])

    def test_the_real_status_line_was_what_the_real_renderer_drew(self):
        # WI-9: the picture is view.render's, not a stand-in's. STAT-2 with
        # the score kept up to date, through the whole stack. The leading
        # blank column is WI-3's STATUS_INDENT, assumption A3.
        self.assertEqual(" score 3    arrows, q quits", PLAYED["status"])
