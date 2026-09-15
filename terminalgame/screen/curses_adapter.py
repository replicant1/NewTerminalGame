"""The one module in the system that knows `curses` exists.

It implements the screen port against a real terminal, and it owns the two
obligations that go with that:

* **Restore the terminal on every exit path** — a normal return, an
  unhandled exception, and a fatal signal alike (caution C10). A player left
  in a terminal with echo off and no cursor has a broken shell, and the
  window may be closed out from under them a moment later.
* **Present the whole frame in one pass** (caution C9). Every cell is written
  every time and one refresh makes the lot visible at once.

Both `curses` and `signal` are injectable, so every one of those paths can be
exercised with no terminal anywhere near the test.
"""

from __future__ import annotations

import curses as _curses_module
import locale as _locale_module
import os
import signal as _signal_module

from .port import (
    Colour,
    Frame,
    Key,
    REQUIRED_HEIGHT,
    REQUIRED_WIDTH,
    Screen,
    ScreenTooSmall,
)

#: Signals that would otherwise kill the process without running any `finally`
#: block, leaving the player's terminal in raw mode. SIGINT is deliberately
#: absent: Python turns it into KeyboardInterrupt, which the session's own
#: `finally` already catches on the way out.
FATAL_SIGNALS = ("SIGTERM", "SIGHUP")


def _palette(curses_module):
    """Symbolic colour -> (curses colour, extra attributes), on black.

    The specification names five colours (SCRN-3 to SCRN-6). An eight-colour
    terminal has no "gold" and no "pink", so dim yellow stands for gold and
    bold magenta for pink, which is what those two look like on a terminal
    and is how they are usually spelled.
    """
    return {
        Colour.WALL: (curses_module.COLOR_BLUE, 0),
        Colour.DOT: (curses_module.COLOR_YELLOW, curses_module.A_DIM),
        Colour.PLAYER: (curses_module.COLOR_YELLOW, curses_module.A_BOLD),
        Colour.GHOST: (curses_module.COLOR_MAGENTA, curses_module.A_BOLD),
        Colour.STATUS: (curses_module.COLOR_CYAN, 0),
    }


class CursesScreen(Screen):
    """The screen port, over a curses window.

    Construct it through `TerminalSession`, which is what puts the terminal
    into raw mode and — much more importantly — takes it back out again.
    """

    def __init__(self, window, curses_module=None, attributes=None):
        self._window = window
        self._curses = curses_module or _curses_module
        # colour -> the attribute word to pass to the terminal. Worked out
        # once when the session starts, because it cannot change afterwards.
        self._attributes = attributes or {}

    # -- the port ---------------------------------------------------------

    def size(self):
        rows, columns = self._window.getmaxyx()
        return (columns, rows)

    def new_frame(self):
        width, height = self.size()
        return Frame(width, height)

    def present(self, frame):
        """Write every cell of the frame, then make the lot visible at once.

        "Every cell" is not an accident of this implementation, it is the
        requirement. A three-column actor glyph overwrites a column of the
        square beside it, so a pass that wrote only what had changed would
        leave the other half of somebody else's glyph on the screen.
        """
        width, height = self.size()
        if frame.width != width or frame.height != height:
            raise ValueError(
                "The frame is {0} x {1} but the screen is {2} x {3}; a frame "
                "is presented whole or not at all."
                .format(frame.width, frame.height, width, height))

        window = self._window
        last_row = height - 1
        for row in range(height):
            for column, text, colour in frame.row_runs(row):
                attribute = self._attributes.get(colour, 0)
                if row == last_row and column + len(text) >= width:
                    # Writing the very last cell of a terminal advances the
                    # cursor off the end and curses reports an error, even
                    # though the character lands. Write the run short, then
                    # insert the final character, which does not move the
                    # cursor. Measured, not assumed — see
                    # docs/findings/WI-2-curses-bottom-right-cell.md.
                    head = text[:width - column - 1]
                    if head:
                        window.addstr(row, column, head, attribute)
                    self._write_final_cell(row, width - 1, text[-1], attribute)
                else:
                    window.addstr(row, column, text, attribute)
        # One refresh for the whole picture: the player sees one complete
        # update, never a frame being painted in front of them (SCRN-7).
        window.refresh()

    def read_key(self, timeout_seconds):
        milliseconds = _timeout_in_milliseconds(timeout_seconds)
        self._window.timeout(milliseconds)
        code = self._window.getch()
        if code == -1:
            return None
        return self._translate(code)

    # -- internals --------------------------------------------------------

    def _write_final_cell(self, row, column, character, attribute):
        try:
            self._window.insch(row, column, character, attribute)
        except self._curses.error:
            # Some terminals refuse the bottom-right cell outright. One
            # missing cell in the corner is not worth losing the frame over.
            pass

    def _translate(self, code):
        curses_module = self._curses
        if code == curses_module.KEY_UP:
            return Key.UP
        if code == curses_module.KEY_DOWN:
            return Key.DOWN
        if code == curses_module.KEY_LEFT:
            return Key.LEFT
        if code == curses_module.KEY_RIGHT:
            return Key.RIGHT
        if _is_printable(code):
            return Key.printable(chr(code))
        # Control codes and anything wider than a byte are things the loop
        # discards (CTRL-5), and they are not printable, so they must not
        # arrive claiming to be. An ESC used to reach the loop as
        # `Key.printable("\x1b")`, which was discarded anyway -- the game never
        # behaved wrongly, but `is_printable` was not true of it.
        return Key.other(code)


def _is_printable(code):
    """Is this byte a character the player could have meant to type?

    The printable ASCII range and nothing else. Below 32 are the control
    codes, 127 is delete, and at 128 and above `curses.getch` is handing back
    the individual BYTES of a multi-byte character rather than a character —
    `chr()` on one of those would invent a Latin-1 letter nobody pressed.
    Only `q` and `Q` are ever consulted (CTRL-4), so nothing here turns on the
    wider range; the point is that `Key.printable` should be true of what it
    says it is.
    """
    return 32 <= code < 127


def _timeout_in_milliseconds(timeout_seconds):
    """Seconds as curses milliseconds, never negative.

    curses reads a negative timeout as "block until a key arrives", which is
    the one thing the game loop must never do — a tick that is already
    overdue would wait for the player instead of firing. So an overdue
    timeout polls and returns immediately.
    """
    if timeout_seconds is None:
        raise TypeError("read_key needs a timeout in seconds, not None.")
    milliseconds = int(round(float(timeout_seconds) * 1000.0))
    return max(0, milliseconds)


class TerminalSession(object):
    """Raw mode for as long as the game runs, and not one moment longer.

    Use it as a context manager::

        with TerminalSession() as screen:
            screen.present(frame)

    On the way in: no echo, character-at-a-time input, arrow keys decoded for
    us, cursor hidden, colours ready, and the terminal checked for size. On
    the way out — by any route at all, including a SIGTERM that would
    otherwise skip every `finally` in the process — echo back on, cursor back
    on, and curses shut down.
    """

    def __init__(self,
                 curses_module=None,
                 signal_module=None,
                 locale_module=None,
                 required_width=REQUIRED_WIDTH,
                 required_height=REQUIRED_HEIGHT,
                 on_fatal_signal=None):
        self._curses = curses_module or _curses_module
        self._signal = signal_module or _signal_module
        self._locale = locale_module or _locale_module
        self._required_width = required_width
        self._required_height = required_height
        self._on_fatal_signal = on_fatal_signal or self._die_of_signal
        self._window = None
        self._screen = None
        self._active = False
        self._previous_handlers = {}

    # -- the context manager ----------------------------------------------

    def __enter__(self):
        return self.open()

    def __exit__(self, exception_type, exception, traceback):
        self.close()
        return False  # never swallow the exception; just leave a sane terminal

    def open(self):
        # ncurses needs the locale set before initscr or it will not put a
        # multi-byte box-drawing character on the screen (SCRN-3).
        try:
            self._locale.setlocale(self._locale.LC_ALL, "")
        except Exception:
            pass

        self._window = self._curses.initscr()
        self._active = True
        try:
            self._curses.noecho()        # CTRL-5: nothing typed reaches the maze
            self._curses.cbreak()        # keys arrive one at a time, unbuffered
            self._window.keypad(True)    # arrows arrive as codes, not escapes
            self._hide_cursor()          # SCRN-7: the cursor is never visible
            attributes = self._start_colour()
            self._check_size()
            self._install_signal_handlers()
        except BaseException:
            # Anything at all going wrong between initscr and a usable screen
            # still leaves the player's terminal the way we found it.
            self.close()
            raise
        self._screen = CursesScreen(self._window,
                                    curses_module=self._curses,
                                    attributes=attributes)
        return self._screen

    def close(self):
        """Put the terminal back. Safe to call twice; often is."""
        if not self._active:
            return
        self._active = False
        self._remove_signal_handlers()
        # Each step guarded on its own: a terminal that refuses one of them
        # must not stop the others from running.
        self._attempt(lambda: self._curses.curs_set(1))
        if self._window is not None:
            self._attempt(lambda: self._window.keypad(False))
        self._attempt(self._curses.nocbreak)
        self._attempt(self._curses.echo)
        self._attempt(self._curses.endwin)

    @property
    def is_active(self):
        return self._active

    # -- internals --------------------------------------------------------

    def _attempt(self, action):
        try:
            action()
        except Exception:
            pass

    def _hide_cursor(self):
        try:
            self._curses.curs_set(0)
        except Exception:
            # A terminal that cannot hide its cursor is not a reason to
            # refuse to play; it is a reason for a human to look at it.
            pass

    def _start_colour(self):
        curses_module = self._curses
        try:
            if not curses_module.has_colors():
                return {}
            curses_module.start_color()
        except Exception:
            return {}
        attributes = {}
        for index, (colour, (foreground, extra)) in enumerate(
                sorted(_palette(curses_module).items(), key=lambda kv: kv[0].name),
                start=1):
            try:
                curses_module.init_pair(index, foreground, curses_module.COLOR_BLACK)
                attributes[colour] = curses_module.color_pair(index) | extra
            except Exception:
                pass
        return attributes

    def _check_size(self):
        rows, columns = self._window.getmaxyx()
        if columns < self._required_width or rows < self._required_height:
            raise ScreenTooSmall(columns, rows,
                                 self._required_width, self._required_height)

    def _install_signal_handlers(self):
        for name in FATAL_SIGNALS:
            number = getattr(self._signal, name, None)
            if number is None:
                continue
            try:
                previous = self._signal.signal(number, self._handle_signal)
            except (ValueError, OSError, RuntimeError):
                # Not the main thread, or the platform has no such signal.
                continue
            self._previous_handlers[number] = previous

    def _remove_signal_handlers(self):
        for number, previous in list(self._previous_handlers.items()):
            try:
                self._signal.signal(number, previous)
            except (ValueError, OSError, RuntimeError):
                pass
        self._previous_handlers = {}

    def _handle_signal(self, signal_number, stack_frame):
        """A signal that would kill us: give the terminal back, then die."""
        self.close()
        self._on_fatal_signal(signal_number)

    def _die_of_signal(self, signal_number):
        self._signal.signal(signal_number, self._signal.SIG_DFL)
        os.kill(os.getpid(), signal_number)
