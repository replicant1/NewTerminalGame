"""The seam between the application and the windowing toolkit.

Everything in this module is either a plain value or an abstract description of
what the Shell needs a windowing toolkit to do.  **Nothing here imports a
windowing toolkit.**  The one module in the application that does is
:mod:`terminal_game.shell.tk_toolkit`; everything else — including every test —
talks to :class:`Toolkit`.

That is what lets the whole of WI-3 be exercised without a window ever
appearing on anybody's desktop.
"""

from __future__ import annotations

import abc
from typing import Any, Callable, NamedTuple


class PixelSize(NamedTuple):
    """A size in pixels.

    The window owner is *told* its pixel size (WI-3); working out that 40 x 30
    character cells come to this many pixels is the character grid surface's
    job (WI-2), and the window owner never asks why.
    """

    width: int
    height: int


class ScreenPosition(NamedTuple):
    """A position in screen pixels, measured from the top-left of the screen."""

    x: int
    y: int


class KeyPress(NamedTuple):
    """One key press, as it crossed the toolkit seam, and nothing more.

    ``keysym`` is the toolkit's name for the key — ``"Up"``, ``"q"``,
    ``"Escape"`` — and ``char`` is the character it produced, empty for keys
    that produce none.  The Shell does not interpret either of them: it hands
    the value on unchanged, and the input translator (WI-9, Presentation) is
    what turns it into an intent.  Being a plain value is the point, because
    Presentation may not name the toolkit.
    """

    keysym: str
    char: str = ""


class WindowSpec(NamedTuple):
    """Everything the toolkit needs in order to create the game's window.

    One value rather than six arguments, so that a test can assert the whole of
    what was asked for in one comparison.
    """

    title: str
    size: PixelSize
    position: ScreenPosition
    background: str
    resizable: bool


#: What :meth:`Toolkit.schedule_once` hands back.  Opaque: the Shell only ever
#: passes it straight back to :meth:`Toolkit.cancel_scheduled`.
TimerHandle = Any

#: What :meth:`Toolkit.create_window` hands back: the thing the character grid
#: surface (WI-2) paints into.  Opaque to the Shell, which never draws on it.
DrawingTarget = Any


class Toolkit(abc.ABC):
    """What the Shell needs of a windowing toolkit, and nothing more.

    One instance owns at most one window, for the game's whole life.  WIN-1
    asks for a window of its own and GAME-3 rules out ever wanting a second, so
    there is no window identifier in any of these signatures — the honest
    alternative to a handle nobody would ever pass anything but one value for.
    """

    @abc.abstractmethod
    def create_window(self, spec: WindowSpec) -> DrawingTarget:
        """Create the window described by *spec* and return its drawing target.

        The drawing target is handed to the character grid surface; the Shell
        itself never paints on it.
        """

    @abc.abstractmethod
    def bind_key_handler(self, handler: Callable[[KeyPress], None]) -> None:
        """Call *handler* with a :class:`KeyPress` for every key pressed."""

    @abc.abstractmethod
    def bind_close_request(self, handler: Callable[[], None]) -> None:
        """Call *handler* when the window manager asks for the window to close.

        Without this the window's own close button would take the window away
        and leave the process running, which is the orphan the specification's
        WIN-5 is trying to avoid.
        """

    @abc.abstractmethod
    def schedule_once(self, delay_ms: int, callback: Callable[[], None]) -> TimerHandle:
        """Call *callback* once, *delay_ms* from now, on the event loop."""

    @abc.abstractmethod
    def cancel_scheduled(self, handle: TimerHandle) -> None:
        """Cancel a callback scheduled by :meth:`schedule_once`."""

    @abc.abstractmethod
    def run_event_loop(self) -> None:
        """Hand control to the event loop; return when it has been stopped."""

    @abc.abstractmethod
    def stop_event_loop(self) -> None:
        """Ask the event loop to return.  Harmless if it is not running."""

    @abc.abstractmethod
    def destroy_window(self) -> None:
        """Close the window.  Harmless if there is no window."""
