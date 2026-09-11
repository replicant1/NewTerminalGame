"""The curses adapter — the one module in this repository that imports curses.

IMPURE, and as thin as it can be made. It holds **no decision about the
game**: which command a key means lives in :mod:`termgame.controls`, when the
ghost is due lives in :mod:`termgame.ticker`, and what the picture looks like
lives in the pure renderer. What is left here is entering and leaving curses
safely, turning a :class:`~termgame.model.Frame` into ``addstr`` calls, and
turning ``getch`` into a key code.

Two things in here are not obvious and both were measured.

**The bottom-right cell.** ``addstr(LINES-1, COLS-1, ch)`` raises
``addwstr() returned ERR``: ncurses writes the character and then cannot
advance the cursor past the end of the screen. ``insstr`` at the same cell
succeeds, because it never moves the cursor. The status line is on the last
row, and a full repaint writes every cell, so :meth:`Screen.paint` uses
``insstr`` for that one cell and ``addstr`` for the other 1199.
(ARCHITECTURE.md C1.)

**The escape delay.** ncurses waits up to a second after a bare ``ESC``
deciding whether an escape sequence follows, which looks to a player like the
game has frozen. ``set_escdelay(25)`` cuts that to 25 ms. Arrow keys are
unaffected — they arrive as one burst. (ARCHITECTURE.md C10.)

The repaint is deliberately naive: one ``addstr`` per cell, then one
``refresh``. ncurses diffs its virtual screen against the physical one, which
is what makes the redraw flicker-free (SCRN-7), and the whole frame was
measured at 0.25 ms against a 143 ms tick. Dirty-rectangle tracking would be
the first thing to introduce a rendering bug and the last thing to be needed
(ARCHITECTURE.md C5).
"""

import contextlib
import curses
import importlib
from typing import Callable, Dict, Iterator, NamedTuple, Optional

from termgame import controls
from termgame.model import STYLE_DEFAULT, Frame

#: How long ncurses waits after a bare ESC, in milliseconds (C10).
ESCAPE_DELAY_MS = 25


class StyleSpec(NamedTuple):
    """How a style identifier looks: a 256-colour index and two attributes.

    ``colour`` is ``None`` for "whatever the terminal's foreground already
    is", which is what the default style wants.
    """

    colour: Optional[int]
    bold: bool = False
    dim: bool = False


#: The attribute names a style may carry. WI-3 states this list is closed:
#: these two, and never a third.
ATTRIBUTE_NAMES = ("bold", "dim")

#: What the adapter paints with **if WI-3's theme is not there to be read.**
#: It is a fallback, not the source of truth — :func:`resolve_palette` prefers
#: ``termgame.theme.STYLES``, so that changing a colour after human check H6
#: is a change to one pure module and never to this one.
#:
#: The colours are the ones the specification names: blue walls (SCRN-3), dim
#: gold dots (SCRN-4), bright yellow player and pink ghost (SCRN-5), cyan
#: status line (SCRN-6).
FALLBACK_PALETTE: Dict[str, StyleSpec] = {
    STYLE_DEFAULT: StyleSpec(colour=None),
    "wall": StyleSpec(colour=33),
    "dot": StyleSpec(colour=178, dim=True),
    "player": StyleSpec(colour=226, bold=True),
    "ghost": StyleSpec(colour=213),
    "status": StyleSpec(colour=51),
}


def resolve_palette(
    module_lookup: Optional[Callable[[str], object]] = None
) -> Dict[str, StyleSpec]:
    """The style table to paint with: WI-3's if it has landed, else the fallback.

    WI-3 owns the identifier vocabulary and the colour numbers; this adapter
    owns only the translation into curses attributes. Reading the table rather
    than copying it means a colour change lives entirely in the pure module
    where a reviewer expects to find it.

    A style the table does not describe, and a table that cannot be read at
    all, both end at the fallback rather than at an exception: a disagreement
    between the two halves must cost colour and never the picture.
    """
    lookup = importlib.import_module if module_lookup is None else module_lookup
    try:
        theme = lookup("termgame.theme")
    except ImportError:
        return dict(FALLBACK_PALETTE)
    styles = getattr(theme, "STYLES", None)
    if not styles:
        return dict(FALLBACK_PALETTE)
    resolved: Dict[str, StyleSpec] = {}
    for name, style in styles.items():
        attributes = tuple(getattr(style, "attributes", ()) or ())
        resolved[name] = StyleSpec(
            colour=getattr(style, "colour", None),
            bold="bold" in attributes,
            dim="dim" in attributes,
        )
    resolved.setdefault(STYLE_DEFAULT, StyleSpec(colour=None))
    return resolved


class Screen(object):
    """A curses window, wrapped in the two operations the loop needs.

    It is constructed around an already-initialised curses window, so the
    whole of it can be exercised against a stand-in window object with no
    terminal attached. :func:`session` is what produces the real one.
    """

    def __init__(self, window, attributes: Optional[Dict[str, int]] = None) -> None:
        self._window = window
        self._attributes = {} if attributes is None else dict(attributes)
        self._default = self._attributes.get(STYLE_DEFAULT, 0)

    # -- painting ----------------------------------------------------------

    def attribute(self, style: str) -> int:
        """The curses attribute for a style identifier, or the default."""
        return self._attributes.get(style, self._default)

    def paint(self, frame: Frame) -> None:
        """Draw ``frame`` and show it.

        Clipped to the window if the window is smaller than the picture — a
        game in a window that is not 40 x 30 should look wrong, not crash.
        """
        window = self._window
        height, width = window.getmaxyx()
        rows = min(height, frame.height)
        cols = min(width, frame.width)
        last_row = height - 1
        last_col = width - 1
        for row in range(rows):
            for col in range(cols):
                cell = frame.cell(row, col)
                attribute = self.attribute(cell.style)
                if row == last_row and col == last_col:
                    # C1: addstr here raises; insstr does not move the cursor
                    # and so succeeds.
                    window.insstr(row, col, cell.char, attribute)
                else:
                    window.addstr(row, col, cell.char, attribute)
        window.refresh()

    # -- reading -----------------------------------------------------------

    def read_key(self, timeout_ms: int) -> Optional[int]:
        """Wait up to ``timeout_ms`` for a key; ``None`` if none arrived.

        Returns **as soon as a key arrives**, which is what lets the player be
        answered at keypress latency while the ghost keeps its own deadline
        (GHOST-1, CTRL-2) with no second clock.

        A negative timeout is clamped to zero: ncurses reads a negative
        timeout as "block forever", which would stop the ghost the moment the
        loop ran a hair late.
        """
        window = self._window
        window.timeout(max(0, int(timeout_ms)))
        key = window.getch()
        if key == controls.NO_KEY:
            return None
        return key


def build_attributes(palette: Optional[Dict[str, StyleSpec]] = None) -> Dict[str, int]:
    """Turn the palette into curses attributes, one colour pair per style.

    Called once, inside a curses session. Degrades to plain attributes if the
    terminal has no colour, which is the only way this can fail and is not
    worth refusing to start over.
    """
    specs = resolve_palette() if palette is None else palette
    attributes: Dict[str, int] = {}
    coloured = False
    try:
        curses.start_color()
        curses.use_default_colors()
        coloured = curses.has_colors()
    except curses.error:
        coloured = False

    pair = 0
    for style in sorted(specs):
        spec = specs[style]
        attribute = 0
        if spec.bold:
            attribute |= curses.A_BOLD
        if spec.dim:
            attribute |= curses.A_DIM
        if coloured and spec.colour is not None:
            pair += 1
            try:
                curses.init_pair(pair, spec.colour, -1)
                attribute |= curses.color_pair(pair)
            except curses.error:
                pass
        attributes[style] = attribute
    return attributes


@contextlib.contextmanager
def session(palette: Optional[Dict[str, StyleSpec]] = None) -> Iterator[Screen]:
    """Enter curses, yield a :class:`Screen`, and leave curses whatever happens.

    The teardown runs on the exception path too. A game that dies without
    restoring the terminal leaves the player looking at a window with no
    cursor and no echo, which they cannot type their way out of.
    """
    window = curses.initscr()
    try:
        _set_escape_delay(ESCAPE_DELAY_MS)
        curses.noecho()  # CTRL-5: nothing typed is echoed into the maze
        curses.cbreak()  # keys arrive without waiting for a newline
        _hide_cursor()  # SCRN-7: the text cursor is never visible
        window.keypad(True)  # CTRL-1: arrows arrive as KEY_UP and friends
        yield Screen(window, build_attributes(palette))
    finally:
        try:
            window.keypad(False)
        except curses.error:
            pass
        _show_cursor()
        curses.nocbreak()
        curses.echo()
        curses.endwin()


def _hide_cursor() -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        # A terminal that cannot hide its cursor is not a reason to refuse to
        # play; it is human check H5's problem, not a crash.
        pass


def _show_cursor() -> None:
    try:
        curses.curs_set(1)
    except curses.error:
        pass


def _set_escape_delay(milliseconds: int) -> None:
    setter = getattr(curses, "set_escdelay", None)
    if setter is None:  # pragma: no cover - present on both pinned versions
        return
    try:
        setter(milliseconds)
    except curses.error:  # pragma: no cover
        pass
