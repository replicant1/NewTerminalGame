"""A terminal that lives in memory, so the tests need no real one.

This is a **fake**, not a stub: it keeps the state a terminal keeps — what is
on the glass, whether it is echoing, whether the cursor is showing, whether
curses has it — and it changes that state when it is told to. The tests then
assert what the terminal ended up like, which is what the player would see,
rather than asserting that some call was made.

It also keeps a virtual clock, so a test can ask the real question about a key
read: how long did it actually wait?
"""

from __future__ import annotations


class CursesError(Exception):
    """Stands in for `curses.error`."""


class FakeCursesWindow(object):
    """The glass, and the keyboard in front of it."""

    def __init__(self, width, height, terminal):
        self.width = width
        self.height = height
        self._terminal = terminal
        self.buffer = [[" "] * width for _ in range(height)]
        self.attributes = [[0] * width for _ in range(height)]
        #: A snapshot of the glass at each moment the terminal was refreshed.
        #: One entry means the player saw one complete update.
        self.presented = []
        self.keypad_on = False
        self._timeout_milliseconds = None
        #: (moment_in_seconds, key_code), soonest first.
        self._pending_keys = []
        #: Set by the test to make a write fail, to exercise a failure path.
        self.fail_writes = False

    # -- what a curses window can be asked -------------------------------

    def getmaxyx(self):
        return (self.height, self.width)

    def keypad(self, flag):
        self.keypad_on = bool(flag)

    def addstr(self, row, column, text, attribute=0):
        if self.fail_writes:
            raise CursesError("this terminal refuses writes")
        if not 0 <= row < self.height:
            raise CursesError("row {0} off the glass".format(row))
        if column < 0 or column + len(text) > self.width:
            raise CursesError("columns {0}..{1} off the glass"
                              .format(column, column + len(text)))
        if row == self.height - 1 and column + len(text) >= self.width:
            # The real thing: the cursor is pushed off the bottom-right corner
            # and curses complains, even though the characters land.
            raise CursesError("cursor off the bottom-right corner")
        for offset, character in enumerate(text):
            self.buffer[row][column + offset] = character
            self.attributes[row][column + offset] = attribute

    def insch(self, row, column, character, attribute=0):
        if self.fail_writes:
            raise CursesError("this terminal refuses writes")
        self.buffer[row][column] = character
        self.attributes[row][column] = attribute

    def refresh(self):
        self.presented.append(self.text_rows())

    def erase(self):
        self.buffer = [[" "] * self.width for _ in range(self.height)]
        self.attributes = [[0] * self.width for _ in range(self.height)]

    def timeout(self, milliseconds):
        self._timeout_milliseconds = milliseconds

    def getch(self):
        """Wait out the timeout, or return the moment a key is due.

        The virtual clock advances by however long the wait really was, so a
        test can assert that a waiting key came back at once and that an empty
        keyboard cost exactly the timeout.
        """
        if self._timeout_milliseconds is None:
            raise AssertionError(
                "getch was called without a timeout being set first; the game "
                "loop must never block indefinitely.")
        if self._timeout_milliseconds < 0:
            raise AssertionError(
                "a negative curses timeout means 'block until a key arrives', "
                "which the game loop must never do.")
        limit = self._terminal.now + self._timeout_milliseconds / 1000.0
        if self._pending_keys and self._pending_keys[0][0] <= limit:
            moment, code = self._pending_keys.pop(0)
            self._terminal.now = max(self._terminal.now, moment)
            return code
        self._terminal.now = limit
        return -1

    # -- what a test can ask ---------------------------------------------

    def press(self, code, at=None):
        """Queue a key, due now unless a later moment is given."""
        moment = self._terminal.now if at is None else at
        self._pending_keys.append((moment, code))
        self._pending_keys.sort(key=lambda pair: pair[0])

    def text_rows(self):
        return ["".join(row) for row in self.buffer]

    def attribute_at(self, column, row):
        return self.attributes[row][column]

    def scribble(self, row, column, text):
        """Put debris on the glass without going through curses.

        Stands for the column a three-column actor glyph overwrites in the
        square next door: something on the screen that the frame says should
        not be there.
        """
        for offset, character in enumerate(text):
            self.buffer[row][column + offset] = character


class FakeCurses(object):
    """A stand-in for the `curses` module, and for the terminal behind it."""

    error = CursesError

    KEY_UP = 259
    KEY_DOWN = 258
    KEY_LEFT = 260
    KEY_RIGHT = 261
    KEY_F1 = 265

    A_NORMAL = 0
    A_BOLD = 0x1000
    A_DIM = 0x2000

    COLOR_BLACK = 0
    COLOR_BLUE = 4
    COLOR_CYAN = 6
    COLOR_MAGENTA = 5
    COLOR_YELLOW = 3

    def __init__(self, width=40, height=30, colours=True, cursor_settable=True):
        #: Terminal state, which is the whole point of this object.
        self.echo_on = True
        self.line_buffered = True     # the opposite of cbreak
        self.cursor_visible = True
        self.in_curses_mode = False
        self.now = 0.0                # the virtual clock

        self.colours_available = colours
        self.cursor_settable = cursor_settable
        self.colour_pairs = {}
        self.window = FakeCursesWindow(width, height, self)
        self.initscr_calls = 0

    # -- module-level curses functions ------------------------------------

    def initscr(self):
        self.initscr_calls += 1
        self.in_curses_mode = True
        return self.window

    def endwin(self):
        self.in_curses_mode = False

    def noecho(self):
        self.echo_on = False

    def echo(self):
        self.echo_on = True

    def cbreak(self):
        self.line_buffered = False

    def nocbreak(self):
        self.line_buffered = True

    def curs_set(self, visibility):
        if not self.cursor_settable:
            raise CursesError("this terminal cannot hide its cursor")
        self.cursor_visible = bool(visibility)

    def has_colors(self):
        return self.colours_available

    def start_color(self):
        if not self.colours_available:
            raise CursesError("no colours here")

    def init_pair(self, index, foreground, background):
        self.colour_pairs[index] = (foreground, background)

    def color_pair(self, index):
        return index << 8

    # -- what a test can ask ----------------------------------------------

    @property
    def is_restored(self):
        """True when the terminal has been given back to the player."""
        return (self.echo_on
                and self.line_buffered
                and self.cursor_visible
                and not self.in_curses_mode)

    def describe(self):
        return ("echo={0} line_buffered={1} cursor_visible={2} "
                "in_curses_mode={3}".format(self.echo_on, self.line_buffered,
                                            self.cursor_visible,
                                            self.in_curses_mode))


class FakeSignals(object):
    """A stand-in for the `signal` module that hands handlers back to a test."""

    SIGTERM = 15
    SIGHUP = 1
    SIGINT = 2
    SIG_DFL = 0

    def __init__(self, refuse=()):
        self.handlers = {}
        self.history = []
        self._refuse = set(refuse)

    def signal(self, number, handler):
        if number in self._refuse:
            raise ValueError("signal only works in main thread")
        previous = self.handlers.get(number, self.SIG_DFL)
        self.handlers[number] = handler
        self.history.append((number, handler))
        return previous

    def deliver(self, number):
        """Deliver a signal the way the operating system would."""
        handler = self.handlers.get(number)
        if handler in (None, self.SIG_DFL):
            raise AssertionError(
                "signal {0} has no handler installed; it would have killed the "
                "process outright.".format(number))
        handler(number, None)


class FakeLocale(object):
    LC_ALL = 6

    def __init__(self):
        self.set_to = None

    def setlocale(self, category, value):
        self.set_to = (category, value)
        return "en_GB.UTF-8"
