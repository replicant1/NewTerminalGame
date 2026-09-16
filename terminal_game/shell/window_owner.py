"""The process's own native window, and the event loop that drives it.

WI-3.  Under the adopted architecture (candidate 2) the application owns its
window rather than dressing somebody else's: it sets the title, the size, the
position and the background, and it closes the window itself.  That is what
makes WIN-3 exact — nothing composes anything around a title the process sets
on its own window.

**The boundary with WI-2, stated once here because the two items were built
side by side:** WI-3 owns the window, the timer and key delivery; WI-2 owns
everything inside the pixels.  The surface works out how many pixels 40 x 30
character cells need and the window owner is *told* that number; the window
owner tells the surface nothing about the game.  The one thing that crosses is
the drawing target :meth:`WindowOwner.open` returns.
"""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - typing.Protocol is present from Python 3.8
    from typing import Protocol
except ImportError:  # pragma: no cover
    Protocol = object  # type: ignore[assignment,misc]

from .cadence import TICK_INTERVAL_MS
from .tick_timer import TickTimer
from .toolkit import (
    DrawingTarget,
    KeyPress,
    PixelSize,
    ScreenPosition,
    Toolkit,
    WindowSpec,
)

#: WIN-3.  The window is titled *Terminal Game*, and under candidate 2 this is
#: the whole of the title: the process owns the window, so nothing else
#: composes parts onto it.
WINDOW_TITLE = "Terminal Game"

#: WIN-2.  A black background.
WINDOW_BACKGROUND = "black"

#: WIN-4, provisionally.  "A little below and to the right of whatever window
#: the player was last looking at" needs a privileged query of another
#: application's windows, and that is confined to WI-14.  Until WI-14 lands the
#: window goes at this fixed screen offset, which WI-14 keeps as its fallback
#: for when the query returns nothing.
DEFAULT_WINDOW_POSITION = ScreenPosition(x=120, y=120)


class SessionCollaborator(Protocol):  # pragma: no cover - a description, not code
    """What the window owner delivers ticks and keys to.

    Structural on purpose.  The session controller (WI-15) lives in the
    Application layer, which may not name the Shell, so it cannot be asked to
    inherit from anything declared here.
    """

    def on_tick(self) -> None:
        """One tick of the ghost's cadence has elapsed."""

    def on_key(self, key: KeyPress) -> None:
        """A key was pressed.  The value arrives exactly as it crossed the seam."""


class WindowOwner:
    """Creates the game's window, drives it, and closes it exactly once.

    Nothing in this class draws, and nothing in it knows what a maze is.  It
    creates a window of the size it was given, delivers ticks and key presses
    to the collaborator it was given, and takes the window away again.
    """

    def __init__(
        self,
        toolkit: Toolkit,
        size: PixelSize,
        collaborator: SessionCollaborator,
        *,
        title: str = WINDOW_TITLE,
        position: ScreenPosition = DEFAULT_WINDOW_POSITION,
        background: str = WINDOW_BACKGROUND,
        tick_interval_ms: int = TICK_INTERVAL_MS,
    ) -> None:
        self._toolkit = toolkit
        self._collaborator = collaborator
        self._spec = WindowSpec(
            title=title,
            size=PixelSize(*size),
            position=ScreenPosition(*position),
            background=background,
            # WIN-2: 40 x 30 cells and nothing else, so the window cannot be
            # dragged into some other shape.
            resizable=False,
        )
        self._timer = TickTimer(toolkit, tick_interval_ms, self._deliver_tick)
        self._drawing_target: Optional[DrawingTarget] = None
        self._is_open = False
        self._session_ended = False

    @property
    def spec(self) -> WindowSpec:
        """Exactly what the window was, or will be, asked to be."""
        return self._spec

    @property
    def tick_interval_ms(self) -> int:
        return self._timer.interval_ms

    @property
    def is_open(self) -> bool:
        return self._is_open

    @property
    def session_ended(self) -> bool:
        return self._session_ended

    @property
    def drawing_target(self) -> DrawingTarget:
        """What the character grid surface paints into.

        Available once the window has been opened.
        """
        if self._drawing_target is None:
            raise RuntimeError("the window has not been opened")
        return self._drawing_target

    def open(self) -> DrawingTarget:
        """Create the window and return the surface's drawing target.

        Opening an already-open window is not an error and does not create a
        second one; WIN-1 asks for a window, singular.
        """
        if self._session_ended:
            raise RuntimeError("the session has ended; the window cannot be reopened")
        if self._is_open:
            return self.drawing_target
        self._drawing_target = self._toolkit.create_window(self._spec)
        self._toolkit.bind_key_handler(self._deliver_key)
        self._toolkit.bind_close_request(self.end_session)
        self._is_open = True
        return self._drawing_target

    def run(self) -> None:
        """Start ticking and hand control to the event loop.

        Returns when the session has ended, by whatever route.  The window is
        reaped on the way out whether the event loop returned normally or the
        session fell over, which is the whole reason the body is in a
        ``try``/``finally``: a window left holding a live process raises a
        dialog only a person can dismiss.
        """
        if not self._is_open:
            self.open()
        try:
            self._timer.start()
            self._toolkit.run_event_loop()
        finally:
            self.end_session()

    def end_session(self) -> None:
        """Stop the timer, leave the event loop, and close the window.

        In that order, and exactly once.  Calling it a second time does
        nothing at all, which matters because the ordinary route out of a
        finished game — ``q``, then the event loop returning — goes through
        here twice.
        """
        if self._session_ended:
            return
        self._session_ended = True
        self._timer.stop()
        self._toolkit.stop_event_loop()
        if self._is_open:
            self._is_open = False
            self._toolkit.destroy_window()

    def _deliver_tick(self) -> None:
        self._guarded(lambda: self._collaborator.on_tick())

    def _deliver_key(self, key: KeyPress) -> None:
        self._guarded(lambda: self._collaborator.on_key(key))

    def _guarded(self, call) -> None:
        """Run *call*, and reap the window if it raises.

        The exception is re-raised rather than swallowed.  A defect that took
        the window away silently would look exactly like a clean exit.
        """
        try:
            call()
        except BaseException:
            self.end_session()
            raise
