"""WI-7 — the walking skeleton: one window, one frame, and ``q``.

The first thing this project does that a person can see. It opens the
application's own window, paints **exactly one** frame composed from a
**fixture** maze with fixture actor positions and a fixture status row, and
closes on ``q``.

**No generator, no timer, no rules.**  There is no maze generation here, no
session, no turn resolution and no repeating tick — WI-14 brings all of those
and supersedes every fixture below.  The whole purpose of this module is to
prove the vertical slice: that what
:func:`~terminal_game.presentation.frame.compose_frame` produces is what
reaches the glass, unaltered, through a real native window.

**The fixture is the specification's own picture.**  ``docs/FUNCTIONAL_REQUIREMENTS.md``
shows a game in progress; assumption P5 makes it normative, and these are its
19 x 29 squares, its player at (10, 13), its ghost at (1, 27), its dots and
its status line.  Choosing it over an invented maze costs nothing and buys
two things: what appears on the screen can be held against the specification
side by side, and it is dense with long wall runs — which is what human item 8
needs somebody to look at.

**On the exit path, which is not this module's to invent.**  WI-6 guarantees
it: a ``GameWindow`` wires the close button to :meth:`~terminal_game.shell.window.GameWindow.close`
in its constructor, and ``close()`` leaves the event loop before destroying
the window, so :meth:`~terminal_game.shell.window.GameWindow.run` returns
whoever owns the interpreter.  **A window can never be left with no way out
even if this module binds nothing at all.**  What is here is the *policy* —
that ``q`` is the key — and one belt-and-braces watchdog, described on
:func:`run_skeleton`.
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

from terminal_game.domain.maze import Maze, Position
from terminal_game.presentation import palette
from terminal_game.presentation.field import Cell, Field
from terminal_game.presentation.frame import compose_frame
from terminal_game.presentation.keys import Intent, intent_for
from terminal_game.presentation.metrics import COLUMNS
from terminal_game.shell.window import GameWindow

# --------------------------------------------------------------------------
# The fixtures, all of which WI-14 replaces
# --------------------------------------------------------------------------

#: The specimen picture's maze, as ``#`` wall and ``.`` corridor.  A fixture:
#: WI-2 generates a fresh one per run and WI-14 is what asks it to.
FIXTURE_MAZE_ROWS = (
    "###################",
    "#...........#.....#",
    "#.#.#######.#.###.#",
    "#.#.#...#...#.....#",
    "#.#.#.#.#.###.###.#",
    "#.#...#.#...#...#.#",
    "#.#.###.###.###.#.#",
    "#.#...#.#...#...#.#",
    "#.###.#.#.###.###.#",
    "#.#.....#.#.......#",
    "#.#.#####.#.#####.#",
    "#.#.#.....#.....#.#",
    "#.#.#.#########.#.#",
    "#.#...#.........#.#",
    "#.#.#.#.###.#.###.#",
    "#...#.....#.#.#...#",
    "#.#######.#.#.#.###",
    "#.#.....#.#.#.#...#",
    "#.#.#.#.#.#.#.###.#",
    "#.#.#...#.#.....#.#",
    "#.#.###.#.#####.#.#",
    "#...#...#.#...#...#",
    "#####.#.#.#.#.###.#",
    "#.......#...#.#...#",
    "#.###########.#.#.#",
    "#.#.............#.#",
    "#.#.#####.#######.#",
    "#.................#",
    "###################",
)

#: Where the specimen picture puts the player.  A fixture: WI-8 works out the
#: real opening position and WI-14 asks it to.
FIXTURE_PLAYER = Position(10, 13)

#: Where the specimen picture puts the ghost.  A fixture, as above.
FIXTURE_GHOST = Position(1, 27)

#: The specimen picture's status line, left-justified into row 29.  **A
#: fixture, and not WI-12's answer** — WI-12 decides what row 29 says, in one
#: place, and WI-14 is what asks it.  This module composes none of it; it is a
#: literal, copied, so that the slice has something to draw there.
FIXTURE_STATUS_TEXT = " score 0    arrows, q quits"


def fixture_maze() -> Maze:
    """The fixture maze, as a :class:`~terminal_game.domain.maze.Maze`."""
    return Maze.from_rows(FIXTURE_MAZE_ROWS)


def fixture_status_row() -> Tuple[Cell, ...]:
    """Row 29 as 40 cells of cyan text on the ground, padded with blanks."""
    text = FIXTURE_STATUS_TEXT.ljust(COLUMNS)
    return tuple(Cell(character, palette.STATUS) for character in text)


def fixture_frame() -> Field:
    """The one frame the skeleton paints.

    Pure: no toolkit, no window, nothing to clean up.  Kept separate from the
    wiring so that the join test can compare what the composer produced with
    what reached the surface, without a window being involved in producing
    either.
    """
    maze = fixture_maze()
    dots = frozenset(maze.corridors()) - {FIXTURE_PLAYER, FIXTURE_GHOST}
    return compose_frame(
        maze=maze,
        dots=dots,
        player=FIXTURE_PLAYER,
        ghost=FIXTURE_GHOST,
        status_row=fixture_status_row(),
    )


# --------------------------------------------------------------------------
# The wiring
# --------------------------------------------------------------------------


def build_skeleton(
    master: "Optional[object]" = None,
    on_close: "Optional[Callable[[], None]]" = None,
) -> GameWindow:
    """Make the window, paint the one frame, and wire ``q`` to closing it.

    :param master: passed straight to :class:`~terminal_game.shell.window.GameWindow`.
        ``None`` in production, where the game owns the one Tk interpreter;
        a test's own root otherwise, because **a second ``tkinter.Tk()`` in
        one process can still crash this build** and every window must
        therefore be a ``Toplevel`` on the one root.
    :param on_close: called when the window closes, before it is destroyed.
    :returns: the window, **withdrawn**. Nothing has reached the screen yet;
        :meth:`~terminal_game.shell.window.GameWindow.show` is what does that.

    The frame is presented *before* the window is shown, so the first thing a
    person sees is the finished picture and never an empty black rectangle.
    """
    window = GameWindow(master=master, on_close=on_close)
    window.present(fixture_frame())
    _bind_quit(window)
    return window


def quit_on_key(window: GameWindow) -> "Callable[[object], None]":
    """The key handler: CTRL-4 closes the window, everything else is ignored.

    The mapping from a key to a meaning is **WI-13's and is not repeated
    here** — this asks :func:`~terminal_game.presentation.keys.intent_for`
    and acts only on ``QUIT``.  The skeleton has no rules, so a move intent
    is read and deliberately dropped; WI-14 is what routes it into a session.

    Returned rather than merely bound so that **this decision can be tested
    without a window on the screen.**  Whether Tk delivers a key event to a
    binding is WI-6's and is already pinned by its own ``needs_window`` test;
    what happens *when it arrives* is WI-7's, and that is this function.
    """

    def on_key(event: "object") -> None:
        keysym = getattr(event, "keysym", "")
        if intent_for(keysym) is Intent.QUIT:
            window.close()

    return on_key


def _bind_quit(window: GameWindow) -> None:
    """Bind :func:`quit_on_key` to every key press.

    One binding on ``<Key>`` rather than one per key, so that CTRL-5 is a
    consequence of the translation returning ``None`` rather than of this
    module having listed the keys it likes.
    """
    window.bind_key("<Key>", quit_on_key(window))


def run_skeleton(
    master: "Optional[object]" = None,
    watchdog_ms: "Optional[int]" = None,
) -> GameWindow:
    """Open the window, show it, and run until it closes.

    :param watchdog_ms: if given, close the window unconditionally after this
        many milliseconds.
    :returns: the window, closed, so a caller can ask what happened to it.

    **Why a watchdog when WI-6 already guarantees a way out.**  WI-6's
    guarantee is that a way out *exists* — the close button and
    :meth:`~terminal_game.shell.window.GameWindow.close` both work. It does
    not guarantee that anybody *takes* it. A key binding that silently fails
    to fire would leave a window on a real person's desk with the process
    waiting for a key that can never arrive, and plan section 1.5 forbids
    exactly that. The watchdog turns that failure from a hang into a closed
    window and a failed assertion.

    It goes through :meth:`~terminal_game.shell.window.GameWindow.after`, so
    it runs inside ``mainloop`` and never touches ``update()``, which does not
    return on a mapped window on this build.

    **In production it is not set.** A player's game must not close itself
    after a timer — that would be a time limit, and GAME-3 forbids one.
    """
    window = build_skeleton(master=master)
    window.show()
    if watchdog_ms is not None:
        window.after(watchdog_ms, window.close)
    window.run()
    return window


def main() -> None:
    """The entry point. Opens the window and returns when it closes.

    Nothing follows :meth:`~terminal_game.shell.window.GameWindow.run`, which
    is what makes closing the window end the process (WIN-5 under assumption
    P1). No watchdog: see :func:`run_skeleton`.
    """
    run_skeleton()


if __name__ == "__main__":  # pragma: no cover - the entry point itself
    main()
