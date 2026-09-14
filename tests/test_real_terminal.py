"""The real curses adapter, in a real terminal, with no window anywhere.

A pseudo-terminal is a terminal in every way curses cares about — it has a
size, it has termios settings, it echoes or does not echo — and it exists
entirely inside this process. Nothing here opens anything on the user's
screen, and nothing here can block for ever: the child is given a bounded
`--hold` and is waited for with a timeout it cannot outlive.

These are the tests the fake terminal cannot give us: that a real ncurses
really does hand the terminal back, and that echo really is off.
"""

from __future__ import annotations

import errno
import os
import re
import signal
import struct
import subprocess
import sys
import time
import unittest

try:
    import fcntl
    import termios
    PTYS_AVAILABLE = True
except ImportError:                                  # pragma: no cover
    PTYS_AVAILABLE = False

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Long enough for a child that must import curses and paint a frame; short
#: enough that a wedged test is noticed rather than waited on.
PATIENCE_SECONDS = 20.0

ESCAPE_SEQUENCE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-Z\\-_]|\x0f|\x0e")


def strip_escapes(text):
    """What a human would read on the glass, with the control traffic gone."""
    return ESCAPE_SEQUENCE.sub("", text)


class PseudoTerminal(object):
    """A terminal of a given size, and a child process running inside it."""

    def __init__(self, columns, rows):
        self.master, self.slave = os.openpty()
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ,
                    struct.pack("HHHH", rows, columns, 0, 0))
        self.settings_before = termios.tcgetattr(self.slave)
        self.settings_after = None
        self.output = ""
        self.stderr = ""
        self.returncode = None
        self._process = None

    def run(self, arguments, keystrokes=(), signal_at=None, signal_number=None):
        """Run the game process in here, typing `keystrokes` as we go.

        Each keystroke is `(seconds_from_the_start, bytes)`. `signal_at` and
        `signal_number` deliver a real signal that many seconds in.
        """
        environment = dict(os.environ)
        environment["TERM"] = environment.get("TERM") or "xterm"
        environment["PYTHONPATH"] = REPOSITORY_ROOT
        environment.pop("LINES", None)
        environment.pop("COLUMNS", None)

        self._process = subprocess.Popen(
            [sys.executable, "-m", "terminalgame.game_main"] + list(arguments),
            stdin=self.slave, stdout=self.slave, stderr=subprocess.PIPE,
            cwd=REPOSITORY_ROOT, env=environment, close_fds=True)

        os.set_blocking(self.master, False)
        pending = sorted(keystrokes, key=lambda pair: pair[0])
        started = time.monotonic()
        deadline = started + PATIENCE_SECONDS
        try:
            while True:
                now = time.monotonic()
                while pending and pending[0][0] <= now - started:
                    _, data = pending.pop(0)
                    os.write(self.master, data)
                if signal_at is not None and now - started >= signal_at:
                    self._process.send_signal(signal_number)
                    signal_at = None
                self._drain()
                if self._process.poll() is not None:
                    break
                if now > deadline:
                    self._process.kill()
                    self._process.wait(timeout=5)
                    raise AssertionError(
                        "the game process outlived its bounded hold by "
                        "{0:.0f}s; it must never block indefinitely."
                        .format(PATIENCE_SECONDS))
                time.sleep(0.01)
            self._drain()
            self.returncode = self._process.returncode
            self.stderr = self._process.stderr.read().decode("utf-8", "replace")
            self.settings_after = termios.tcgetattr(self.slave)
            self.elapsed = time.monotonic() - started
        finally:
            self._close()
        return self

    @property
    def visible_text(self):
        return strip_escapes(self.output)

    def echo_is_on(self, settings):
        return bool(settings[3] & termios.ECHO)

    def line_buffering_is_on(self, settings):
        return bool(settings[3] & termios.ICANON)

    @staticmethod
    def modes(settings):
        """The settings, with the one transient bit masked out.

        `PENDIN` is not a mode the player chose; it is the kernel saying it
        still has input to redisplay after the trip through raw mode. It is
        the only bit that differs after a real curses session on macOS —
        measured, see docs/findings/WI-2-pty-terminal-restore.md.
        """
        settings = list(settings)
        settings[3] = settings[3] & ~termios.PENDIN
        return settings

    def _drain(self):
        while True:
            try:
                chunk = os.read(self.master, 65536)
            except OSError as error:
                if error.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    return
                return                       # the child closed its end
            if not chunk:
                return
            self.output += chunk.decode("utf-8", "replace")

    def _close(self):
        for descriptor in (self.master, self.slave):
            try:
                os.close(descriptor)
            except OSError:
                pass
        if self._process is not None and self._process.stderr is not None:
            self._process.stderr.close()


@unittest.skipUnless(PTYS_AVAILABLE, "no pseudo-terminals on this platform")
class RealTerminalTest(unittest.TestCase):
    """The adapter against the real curses module, in a real terminal."""

    def test_the_frame_reaches_a_real_terminal(self):
        terminal = PseudoTerminal(40, 30).run(["--hold", "0.2"])

        self.assertEqual(0, terminal.returncode, terminal.stderr)
        text = terminal.visible_text
        self.assertIn("Terminal Game", text)
        self.assertIn("the screen port is alive", text)
        self.assertIn("arrows, q quits", text)
        self.assertIn("╔", text, "the box-drawing glyphs must survive the "
                                 "trip through the terminal (SCRN-3)")

    def test_a_real_terminal_is_handed_back_with_echo_and_line_mode_restored(self):
        terminal = PseudoTerminal(40, 30).run(["--hold", "0.2"])

        self.assertEqual(0, terminal.returncode, terminal.stderr)
        self.assertTrue(terminal.echo_is_on(terminal.settings_after),
                        "the player would be left in a terminal that shows "
                        "nothing they type (caution C10)")
        self.assertTrue(terminal.line_buffering_is_on(terminal.settings_after),
                        "the player would be left in a terminal that acts on "
                        "every keystroke (caution C10)")
        self.assertEqual(terminal.modes(terminal.settings_before),
                         terminal.modes(terminal.settings_after),
                         "every mode the player had must come back as it was "
                         "found — input, output, control, local and the "
                         "special characters alike")

    def test_nothing_typed_during_the_game_is_echoed_back(self):
        terminal = PseudoTerminal(40, 30).run(
            ["--hold", "1.0"],
            keystrokes=[(0.4, b"hello there")])

        self.assertEqual(0, terminal.returncode, terminal.stderr)
        self.assertNotIn("hello there", terminal.visible_text,
                         "nothing typed is echoed into the maze (CTRL-5)")

    def test_q_ends_it_well_before_the_hold_would(self):
        terminal = PseudoTerminal(40, 30).run(
            ["--hold", "30"],
            keystrokes=[(0.4, b"q")])

        self.assertEqual(0, terminal.returncode, terminal.stderr)
        self.assertLess(terminal.elapsed, 10.0,
                        "q must be acted on at once, not at the end of the "
                        "hold (CTRL-4)")

    def test_a_terminal_too_small_is_refused_loudly_and_nothing_is_drawn(self):
        terminal = PseudoTerminal(80, 24).run(["--hold", "0.2"])

        self.assertEqual(2, terminal.returncode)
        self.assertIn("40", terminal.stderr)
        self.assertIn("30", terminal.stderr)
        self.assertIn("24", terminal.stderr)
        self.assertNotIn("the screen port is alive", terminal.visible_text)

    def test_a_terminal_too_small_is_still_handed_back(self):
        terminal = PseudoTerminal(80, 24).run(["--hold", "0.2"])

        self.assertTrue(terminal.echo_is_on(terminal.settings_after),
                        "refusing to play must not cost the player their "
                        "terminal")
        self.assertEqual(terminal.modes(terminal.settings_before),
                         terminal.modes(terminal.settings_after))


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(PTYS_AVAILABLE, "no pseudo-terminals on this platform")
class RealTerminalSignalTest(unittest.TestCase):
    """Caution C10's worst case, in a real terminal.

    A SIGTERM runs no `finally` block anywhere in the process. Without a
    handler the game would die in raw mode and leave the player in a terminal
    that echoes nothing — in a window that the launcher is about to close out
    from under them.
    """

    def test_a_terminating_signal_still_hands_the_terminal_back(self):
        terminal = PseudoTerminal(40, 30).run(
            ["--hold", "30"], signal_at=0.5, signal_number=signal.SIGTERM)

        self.assertEqual(-signal.SIGTERM, terminal.returncode,
                         "the process must still die of the signal it was "
                         "sent, not swallow it")
        self.assertTrue(terminal.echo_is_on(terminal.settings_after),
                        "killed mid-game, the player is left with a terminal "
                        "that shows nothing they type")
        self.assertTrue(terminal.line_buffering_is_on(terminal.settings_after))
        self.assertEqual(terminal.modes(terminal.settings_before),
                         terminal.modes(terminal.settings_after))
        self.assertLess(terminal.elapsed, 10.0,
                        "the signal must end it, not be ignored until the hold")

    def test_a_hangup_still_hands_the_terminal_back(self):
        terminal = PseudoTerminal(40, 30).run(
            ["--hold", "30"], signal_at=0.5, signal_number=signal.SIGHUP)

        self.assertEqual(-signal.SIGHUP, terminal.returncode)
        self.assertTrue(terminal.echo_is_on(terminal.settings_after))
        self.assertEqual(terminal.modes(terminal.settings_before),
                         terminal.modes(terminal.settings_after))
