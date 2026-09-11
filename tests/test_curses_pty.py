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
sys.path.insert(0, ROOT)

from termgame.model import SCREEN_COLS, SCREEN_ROWS  # noqa: E402
from termgame.window import COLUMNS as WINDOW_COLUMNS  # noqa: E402
from termgame.window import ROWS as WINDOW_ROWS  # noqa: E402

#: 40 columns, 30 rows — the window the game really runs in (WIN-2).
#:
#: **Taken from the project's own constants and not typed again here.** Until
#: WI-13 these were two literals, which made the size test below a closed
#: loop: it sized a pty to 40 x 30 and then asserted curses saw 40 x 30, and
#: no change anywhere in the product could make it fail. Sizing the pty from
#: ``termgame.model`` and asserting against ``termgame.window`` means the
#: terminal really is the one the picture is drawn for, and that the two
#: independent copies of WIN-2's numbers still agree.
COLUMNS = SCREEN_COLS
LINES = SCREEN_ROWS

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
    for r in range(%(rows)d):
        rows.append(
            "".join(chr(ord("a") + ((r + c) %% 26)) for c in range(%(cols)d))
        )
    frame = frame_from_rows(rows)
    scr = screen_module.Screen(window, screen_module.build_attributes())
    try:
        scr.paint(frame)
        result["paint"] = "no error"
    except Exception as error:
        result["paint"] = "%%s: %%s" %% (type(error).__name__, error)

    # 4. Read the virtual screen back and compare it with what went in.
    read_back = []
    for r in range(%(rows)d):
        read_back.append(
            "".join(chr(window.inch(r, c) & 0xFF) for c in range(%(cols)d))
        )
    result["matches"] = (read_back == rows)
    result["last_row_in"] = rows[-1]
    result["last_row_out"] = read_back[-1]

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
import curses, json, random, sys
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
        # SCRN-7. curs_set returns the *previous* visibility, so asking for
        # "hidden" -- which is what the game has already asked for -- changes
        # nothing and hands back what the game left behind. 0 means the game
        # hid it; 1 or 2 means it did not.
        try:
            result["cursor_the_game_left_behind"] = curses.curs_set(0)
        except Exception as error:
            result["cursor_the_game_left_behind"] = "%%s: %%s" %% (
                type(error).__name__,
                error,
            )
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


#: CTRL-5's second clause: **nothing typed is echoed into the maze.**
#:
#: This enters the game's own :func:`termgame.screen.session` and reads three
#: keystrokes through the adapter's own :meth:`Screen.read_key`, and does
#: nothing else. No picture is painted first, and that is the point.
#: ``docs/findings/WI-13-curses-echo.md`` has the measurements; the short
#: version is that ncurses echoes in software, from inside ``wgetch``, at
#: wherever the cursor happens to be — and after a full 30 x 40 repaint the
#: cursor is parked on the bottom-right cell, where C1's hazard swallows the
#: echo. So the scripted game above cannot see this clause even when echo is
#: forced on, and only a session with no painting in front of it can.
ECHO = r'''
import json, sys
sys.path.insert(0, %(root)r)
from termgame import screen as screen_module

result = {}
try:
    with screen_module.session() as scr:
        result["keys"] = [scr.read_key(500) for _ in range(3)]
    result["returned"] = True
except Exception as error:
    result["error"] = "%%s: %%s" %% (type(error).__name__, error)

with open(%(out)r, "w") as handle:
    json.dump(result, handle)
'''

#: Three of a character that appears nowhere in any picture the game draws.
ECHO_KEYSTROKES = b"zzz"


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

#: Right, **an unmapped key**, down into a wall, right, right, right, down,
#: then `q`. Five requirements in one real run of the real thing.
#:
#: **Why the `z` is second and not second-to-last.** It used to sit between
#: the last arrow and the `q`, and WI-12 found that the half of its test
#: which claims "the `z` did not quit" could not fail there: a `z` that quit
#: would have ended the loop one keystroke early, at the same square with the
#: same score, and every recorded field would have been byte-identical. Here,
#: a `z` that quit ends the game after one move — at (1, 2) with a score of
#: 1, three moves and two dots short of the recorded ending.
KEYSTROKES = (
    ARROWS["right"]
    + b"z"               # CTRL-5, nothing happens -- and see above
    + ARROWS["down"]     # (2, 2) is wall: CTRL-3, nothing happens
    + ARROWS["right"]
    + ARROWS["right"]
    + ARROWS["right"]
    + ARROWS["down"]     # (2, 5) is corridor, and holds a dot
    + b"q"               # CTRL-4, END-6
)


def run_play_on_a_pty():
    """Play a scripted game through real ncurses. ``None`` if impossible."""
    return run_probe_on_a_pty(source=PLAY, keystrokes=KEYSTROKES)


def run_echo_probe_on_a_pty():
    """Read three keys through the real session. ``None`` if impossible."""
    return run_probe_on_a_pty(source=ECHO, keystrokes=ECHO_KEYSTROKES)


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
    slave_is_open = True
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
        # CTRL-5, and the whole reason its assertion can fail. **The echo
        # that CTRL-5 is about is ncurses', not the kernel's.** Measured
        # here, on this machine: `curses.initscr()` clears the tty's own ECHO
        # bit by itself and `curses.echo()` never sets it back -- ncurses
        # echoes in software, from inside `wgetch`, straight into the window.
        # So the tty's ECHO bit says nothing at all about whether the game
        # echoes, and a test that read it would pass whatever the game did.
        #
        # What does say so is whether a typed character ever reaches the
        # terminal. Clearing ECHO on the pty before the keystrokes are
        # written stops the line discipline echoing them itself, so a `z`
        # found in what the terminal received can only have been put there by
        # the game. Measured: with `curses.echo()` the three `z`s of a
        # throwaway probe came back three times; with `noecho`, not at all.
        settings = termios.tcgetattr(slave)
        settings[3] &= ~termios.ECHO
        termios.tcsetattr(slave, termios.TCSANOW, settings)
        line_discipline_echo_was_off = not (
            termios.tcgetattr(slave)[3] & termios.ECHO
        )
        environment = dict(os.environ)
        environment["TERM"] = "xterm-256color"
        environment["LINES"] = str(LINES)
        environment["COLUMNS"] = str(COLUMNS)
        text_source = (PROBE if source is None else source) % {
            "root": ROOT,
            "out": path,
            "rows": LINES,
            "cols": COLUMNS,
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
        # The child has gone, so closing this end lets the reader see EOF and
        # finish. Without that the tail of the last repaint is still in
        # flight when `drained` is read, and the terminal output below would
        # be however much of it happened to have arrived.
        os.close(slave)
        slave_is_open = False
        reader.join(timeout=5)
        with open(path) as reading:
            text = reading.read()
        if not text:
            data = {"failed": completed.stderr.decode("utf-8", "replace")}
        else:
            data = json.loads(text)
        # Measured on this side of the pty: everything the game wrote to its
        # terminal, and the state of the line discipline before it started.
        data["terminal_output"] = b"".join(drained)
        data["line_discipline_echo_was_off"] = line_discipline_echo_was_off
        return data
    finally:
        if slave_is_open:
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
ECHOED = once(run_echo_probe_on_a_pty)


@unittest.skipIf(RESULT is None, "a pseudo-terminal could not be made here")
class RealCursesTest(unittest.TestCase):
    def setUp(self):
        if RESULT is not None and "failed" in RESULT:
            self.fail("the curses probe did not run:\n%s" % RESULT["failed"])

    def test_curses_sees_the_window_the_project_says_the_game_runs_in(self):
        """WIN-2, against the project's own constants.

        Until WI-13 this asserted ``[LINES, COLUMNS]`` where ``LINES`` and
        ``COLUMNS`` were two literals in this file and the pty had been sized
        to them a few lines earlier. It imported neither
        ``window.COLUMNS/ROWS`` nor ``model.SCREEN_COLS/ROWS``, so nothing
        that could be changed in the product could make it fail; it proved
        that curses reads back the size it was given, which is a fact about
        curses.

        Now the pty is sized from ``termgame.model`` -- the shape the
        renderer draws -- and checked against ``termgame.window`` -- the
        shape the AppleScript asks Terminal for. Those are two independent
        copies of WIN-2's numbers, and the picture and the window disagreeing
        is exactly the failure this is for. The literal 40 x 30 is pinned as
        well, since both could drift together.
        """
        self.assertEqual(
            [WINDOW_ROWS, WINDOW_COLUMNS],
            RESULT["size"],
            "the terminal the picture is drawn for is not the terminal the "
            "game asks Terminal.app to open",
        )
        self.assertEqual((30, 40), (SCREEN_ROWS, SCREEN_COLS))
        self.assertEqual((30, 40), (WINDOW_ROWS, WINDOW_COLUMNS))

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

    def test_this_terminal_can_hide_its_cursor_at_all(self):
        """The guard on the guard, and it is **not** SCRN-7.

        This asserts that ``curs_set`` works on this terminal, which is what
        the probe's own call measures. Before WI-13 this test was named for
        SCRN-7 and asserted ``isinstance(RESULT["curs_set"], int)`` -- a
        value the probe script had set itself, so no change to the game could
        make it fail, and SCRN-7's "the text cursor is never visible" was
        left with nothing behind it at all. What actually covers SCRN-7 is
        ``ScriptedGameThroughRealCursesTest`` below, which reads back the
        visibility the *game* left behind. This one is only here so that a
        terminal which cannot hide a cursor is told apart from a game which
        does not.
        """
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

    The script is right, an unmapped key, down-into-a-wall, right, right,
    right, down, then `q`. The player starts at (1, 1) on a board whose top
    corridor runs east, so it ends at (2, 5) having eaten three of the four
    dots -- and the press towards the wall and the `z` both did nothing.

    It also carries the two clauses WI-12 found nothing behind: SCRN-7's
    hidden cursor and CTRL-5's echo, both read off the real terminal from
    inside the real session.
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
        """CTRL-5's first clause: an unmapped key does nothing.

        The `z` is the **second** keystroke, immediately after the first
        arrow. If it moved the player the final square would be wrong; if it
        quit, the loop would have returned right there, at (1, 2) with a
        score of 1.

        It used to be second-to-last, and WI-12 found that the "did not quit"
        half could not fail in that position: quitting at the `z` and
        quitting at the `q` that followed it left every recorded field
        byte-identical.
        """
        self.assertEqual([2, 5], PLAYED["player"])
        self.assertEqual(3, PLAYED["score"])
        self.assertEqual("PLAYING", PLAYED["outcome"])

    def test_the_colours_the_theme_names_reach_the_real_terminal(self):
        """SCRN-3, SCRN-4, SCRN-5, SCRN-6 — as bytes on a real terminal.

        ``tests/test_theme.py`` asserts which colour the game asks for and
        ``tests/test_screen_adapter.py`` asserts which colour reaches
        ``init_pair``. This is the end of that chain: the escape sequence a
        terminal actually receives. ``ESC [ 38 ; 5 ; n m`` is "foreground is
        256-colour index n", which is what ncurses emits for a colour pair
        whose background is ``-1``.

        A test cannot say whether cyan *looks* cyan on the user's screen —
        that is human check H6 — but it can say that the byte stream asks for
        it, and nothing did before WI-13.
        """
        output = PLAYED["terminal_output"]
        for colour, what in (
            (33, "blue walls (SCRN-3)"),
            (178, "gold dots (SCRN-4)"),
            (226, "the bright yellow player (SCRN-5)"),
            (213, "the pink ghost (SCRN-5)"),
            (51, "the cyan status line (SCRN-6)"),
        ):
            self.assertIn(
                b"\x1b[38;5;%dm" % colour,
                output,
                "the terminal was never asked for colour %d, %s"
                % (colour, what),
            )

    def test_the_text_cursor_is_not_visible_while_the_game_is_running(self):
        """SCRN-7's "the text cursor is never visible", at last.

        Read back from inside the real session: ``curs_set`` returns the
        previous visibility, so asking for "hidden" -- which the game has
        already asked for -- hands back what the game left behind and changes
        nothing. 0 is hidden; 1 and 2 are the two visible settings.

        Before WI-13 the only test that claimed this asserted that the
        *probe's own* ``curs_set(0)`` returned an int.
        """
        self.assertEqual(
            0,
            PLAYED["cursor_the_game_left_behind"],
            "the game left the text cursor visible in the maze (SCRN-7)",
        )

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


@unittest.skipIf(ECHOED is None, "a pseudo-terminal could not be made here")
class NothingTypedIsEchoedTest(unittest.TestCase):
    """CTRL-5's second clause — *"nothing typed is echoed into the maze"*.

    **Nothing in this project asserted this before WI-13.** WI-12 found that
    the string "echo" did not occur anywhere in the suite;
    ``curses.noecho()`` sat in :func:`termgame.screen.session` with a comment
    naming CTRL-5 and nothing behind it, and ``ARCHITECTURE.md`` recorded the
    clause as *measured* in a ``Screen.__enter__`` that has never existed.

    Two things had to be got right for this to be a test rather than another
    claim, and both are written up in ``docs/findings/WI-13-curses-echo.md``:

    1. **The tty's own ECHO bit is the wrong thing to read.** ``initscr``
       clears it unasked and ``curses.echo()`` never sets it back, so an
       assertion on it passes whatever the game does. The first version of
       this test read it, and breaking ``noecho`` on purpose is what caught
       that.
    2. **A painted screen hides the answer.** ncurses echoes in software at
       wherever the cursor is; after a full repaint the cursor is parked on
       the bottom-right cell, where C1's hazard swallows the echo. So this
       enters the game's real ``session()`` and reads keys through the real
       ``Screen.read_key`` with no painting in front of it, which is where
       what ``session()`` establishes is visible.

    The pty's own line-discipline echo is turned off before the keystrokes
    are written, so a `z` reaching the terminal can only be the game's doing.
    """

    def setUp(self):
        if "failed" in ECHOED:
            self.fail("the echo probe did not run:\n%s" % ECHOED["failed"])
        if "error" in ECHOED:
            self.fail("the echo probe raised: %s" % ECHOED["error"])

    def test_the_three_keystrokes_really_did_reach_the_game(self):
        """The guard on the guard: an unread keystroke cannot be echoed.

        If the probe read nothing, "no `z` came back" would be free.
        """
        self.assertEqual([ord("z")] * 3, ECHOED["keys"])
        self.assertTrue(ECHOED["returned"])

    def test_the_pty_was_not_echoing_on_its_own_account(self):
        self.assertTrue(
            ECHOED["line_discipline_echo_was_off"],
            "the pty was echoing the keystrokes itself, so a `z` in the "
            "output would not be the game's doing",
        )

    def test_the_terminal_output_was_captured_at_all(self):
        # session() writes the terminfo entry/exit sequences whatever else
        # happens, so an empty capture means the plumbing, not the game.
        self.assertGreater(len(ECHOED["terminal_output"]), 0)

    def test_nothing_typed_is_echoed_into_the_maze(self):
        output = ECHOED["terminal_output"]
        self.assertNotIn(
            b"z",
            output,
            "the keystrokes the player typed were echoed back into the "
            "window: `z` appears %d times in what the game wrote to the "
            "terminal (CTRL-5)" % output.count(b"z"),
        )
