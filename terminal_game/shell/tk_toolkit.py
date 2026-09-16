"""The one module in the application that names the windowing toolkit.

Everything above this file talks to :class:`terminal_game.shell.toolkit.Toolkit`.
This is where that description meets Tk, and it is deliberately the thinnest
translation that will do the job: no game logic, no drawing, no decisions.

Importing this module is harmless — it opens nothing.  A window exists only
once :meth:`TkToolkit.create_window` has been called, and the automated suite
never calls it.
"""

from __future__ import annotations

import tkinter
from typing import Callable, Optional

from .toolkit import DrawingTarget, KeyPress, TimerHandle, Toolkit, WindowSpec


def key_press_from_event(event) -> KeyPress:
    """Turn a Tk key event into the plain value that crosses the seam.

    This is the whole of the translation, kept out here where it can be read
    and tested without a window.  ``keysym`` names the key and ``char`` is
    what it typed, empty for keys that type nothing; neither is interpreted
    here, because interpreting them is WI-9's job in the Presentation layer.
    """
    return KeyPress(keysym=event.keysym, char=event.char)


class TkToolkit(Toolkit):
    """Tk, behind the Shell's seam.  One instance owns at most one window."""

    def __init__(self) -> None:
        self._root: Optional[tkinter.Tk] = None
        self._canvas: Optional[tkinter.Canvas] = None
        self._key_handler: Optional[Callable[[KeyPress], None]] = None
        self._close_handler: Optional[Callable[[], None]] = None
        self._pending_exception: Optional[BaseException] = None

    # -- the window ----------------------------------------------------

    def create_window(self, spec: WindowSpec) -> DrawingTarget:
        if self._root is not None:
            raise RuntimeError("this toolkit already owns a window")

        root = tkinter.Tk()
        # WIN-3: the title, set directly on our own window, with nothing
        # composing anything around it.
        root.title(spec.title)
        root.configure(background=spec.background)
        root.resizable(width=spec.resizable, height=spec.resizable)
        root.geometry(
            "{0}x{1}+{2}+{3}".format(
                spec.size.width, spec.size.height, spec.position.x, spec.position.y
            )
        )

        # The drawing target.  ``highlightthickness`` and ``borderwidth`` are
        # zero so that the canvas is exactly the window's pixel size: WIN-2's
        # 40 x 30 cells are derived from font metrics, and a two-pixel border
        # would silently eat into them.
        canvas = tkinter.Canvas(
            root,
            width=spec.size.width,
            height=spec.size.height,
            background=spec.background,
            highlightthickness=0,
            borderwidth=0,
            takefocus=0,
        )
        canvas.pack()

        # The window's own close button must end the session rather than take
        # the window away and leave the process running.
        root.protocol("WM_DELETE_WINDOW", self._on_close_request)
        root.bind("<Key>", self._on_key)
        canvas.focus_set()

        # Measured on this machine (docs/findings/WI-3-tk-window-probe.md):
        # Tk catches anything raised inside a callback, prints a traceback and
        # carries on.  Left alone, a session that fell over would look like a
        # session that ended.  This hook makes a failed callback stop the loop
        # and come back out of run_event_loop, which is what the Shell's seam
        # promises and what the recording double does.
        root.report_callback_exception = self.note_callback_exception

        self._root = root
        self._canvas = canvas
        return canvas

    def destroy_window(self) -> None:
        if self._root is None:
            return
        root = self._root
        self._root = None
        self._canvas = None
        root.destroy()

    # -- events --------------------------------------------------------

    def bind_key_handler(self, handler: Callable[[KeyPress], None]) -> None:
        self._key_handler = handler

    def bind_close_request(self, handler: Callable[[], None]) -> None:
        self._close_handler = handler

    def _on_key(self, event) -> None:
        if self._key_handler is None:
            return
        self._key_handler(key_press_from_event(event))

    def _on_close_request(self) -> None:
        if self._close_handler is not None:
            self._close_handler()

    # -- a callback that fell over --------------------------------------

    @property
    def pending_callback_exception(self) -> Optional[BaseException]:
        """The first exception a callback raised, if one has and it is unread."""
        return self._pending_exception

    def note_callback_exception(self, exc_type, exc_value, exc_traceback) -> None:
        """Tk's hook: a callback raised.  Remember it and leave the loop.

        The *first* exception is the one kept.  Reaping the window may well
        provoke further noise, and the failure that started it is the one
        worth reporting.
        """
        if self._pending_exception is None:
            self._pending_exception = (
                exc_value
                if isinstance(exc_value, BaseException)
                else exc_type(exc_value)
            )
        self.stop_event_loop()

    # -- the clock -----------------------------------------------------

    def schedule_once(self, delay_ms: int, callback: Callable[[], None]) -> TimerHandle:
        if self._root is None:
            raise RuntimeError("there is no window to schedule against")
        return self._root.after(delay_ms, callback)

    def cancel_scheduled(self, handle: TimerHandle) -> None:
        if self._root is None:
            return
        self._root.after_cancel(handle)

    # -- the event loop ------------------------------------------------

    def run_event_loop(self) -> None:
        if self._root is None:
            raise RuntimeError("there is no window to run an event loop for")
        self._pending_exception = None
        self._root.mainloop()
        if self._pending_exception is not None:
            failure, self._pending_exception = self._pending_exception, None
            raise failure

    def stop_event_loop(self) -> None:
        if self._root is None:
            return
        self._root.quit()
