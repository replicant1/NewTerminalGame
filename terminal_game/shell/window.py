"""The game's own window: a 40 x 30 grid of characters on black, keys, a tick, and closing.

This is candidate 2's shell (ARCHITECTURE.md §3). One process creates one Tk
window, titles it, sizes it from the chosen typeface's cell metrics, paints
characters into it, hands named key presses and a steady tick to whoever runs
it, and closes it itself.

Lifecycle, as :class:`GameWindow`'s user sees it::

    window = GameWindow()              # built withdrawn: nothing on screen yet
    window.place(x, y)                 # optional, before run()
    window.paint(first_frame)          # optional, before run()
    status = window.run(on_key, on_tick)   # maps, focuses, loops; returns on close
    sys.exit(status)

``run`` returns when the session ends, and by then the window is gone:

* the program calls :meth:`GameWindow.close` (from a key or tick handler): 0;
* the person clicks the title-bar close button, or quits from the
  application menu (or the Dock): 0;
* a key or tick handler raises: the traceback is printed to stderr, the
  window closes, and ``run`` returns 1;
* a handler raises ``SystemExit`` (``sys.exit``), which tkinter lets out of
  its loop rather than reporting: the window closes and the ``SystemExit``
  carries on out of ``run`` with its status.

**Only characters are drawn** (SCRN-2): the canvas holds one text item per
cell and nothing else. See the package docstring.
"""

import sys
import time
import traceback
import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Iterable

from terminal_game.shell.frame import COLUMNS, ROWS, Frame, check_frame
from terminal_game.shell.geometry import geometry_position
from terminal_game.shell.palette import BACKGROUND, colour_of
from terminal_game.shell.ticker import TICK_HZ, TickSchedule
from terminal_game.shell.typeface import FONT_PIXELS, PREFERRED_FAMILIES, choose_family

TITLE = "Terminal Game"

#: Exit statuses ``run`` returns.
EXIT_OK = 0
EXIT_HANDLER_FAILED = 1


class GameWindow:
    """One window of exactly 40 x 30 character cells, black wherever nothing is painted."""

    def __init__(
        self,
        *,
        title: str = TITLE,
        families: Iterable[str] = PREFERRED_FAMILIES,
        font_pixels: int = FONT_PIXELS,
        tick_hz: float = TICK_HZ,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        root = tk.Tk()
        # Withdrawn before the event loop ever turns, so the window is never
        # seen half-built: it maps once, in run(), already sized and painted.
        root.withdraw()
        self._root = root
        self._clock = clock
        self._tick_hz = tick_hz
        self._closed = False
        self._status = EXIT_OK
        self._tick_job: str | None = None
        self._on_key: Callable[[str], None] | None = None
        self._on_tick: Callable[[], None] | None = None

        fallback = tkfont.nametofont("TkFixedFont", root=root).actual("family")
        family = choose_family(
            families,
            tkfont.families(root),
            lambda f: bool(tkfont.Font(root=root, family=f, size=-font_pixels).metrics("fixed")),
            fallback,
        )
        self._font = tkfont.Font(root=root, family=family, size=-font_pixels)
        self._cell_width = self._font.measure("M")
        self._cell_height = self._font.metrics("linespace")
        width = COLUMNS * self._cell_width
        height = ROWS * self._cell_height
        self._width, self._height = width, height

        root.title(title)
        root.configure(background=colour_of(BACKGROUND), borderwidth=0, highlightthickness=0)
        root.resizable(False, False)
        root.minsize(width, height)
        root.maxsize(width, height)
        root.geometry(f"{width}x{height}")

        canvas = tk.Canvas(
            root,
            width=width,
            height=height,
            background=colour_of(BACKGROUND),
            borderwidth=0,
            highlightthickness=0,
            insertwidth=0,
            takefocus=0,
        )
        canvas.pack(padx=0, pady=0)
        self._canvas = canvas
        self._items = [
            [
                canvas.create_text(
                    c * self._cell_width,
                    r * self._cell_height,
                    anchor="nw",
                    text=" ",
                    fill=colour_of(BACKGROUND),
                    font=self._font,
                )
                for c in range(COLUMNS)
            ]
            for r in range(ROWS)
        ]

        # Every way the person can close it ends the session the same way.
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.createcommand("::tk::mac::Quit", self.close)
        root.bind("<KeyPress>", self._key_pressed)
        # An exception in any key or tick handler (Tk callbacks both) lands here.
        root.report_callback_exception = self._handler_failed

    # -- what the rest of the program may ask ---------------------------------

    @property
    def family(self) -> str:
        """The typeface family actually in use."""
        return self._font.actual("family")

    @property
    def cell_size(self) -> tuple[int, int]:
        """One cell's width and height, in the toolkit's pixels (points on a Mac)."""
        return self._cell_width, self._cell_height

    @property
    def size(self) -> tuple[int, int]:
        """The drawing area's width and height: exactly 40 x 30 cells."""
        return self._width, self._height

    @property
    def root(self) -> tk.Tk:
        """The Tk root, for the shell's own evidence and tests. Not for other layers."""
        return self._root

    @property
    def canvas(self) -> tk.Canvas:
        """The drawing surface, for the shell's own evidence and tests."""
        return self._canvas

    def place(self, x: int, y: int) -> None:
        """Put the window's outer top-left corner, title bar included, at screen point ``(x, y)``.

        Screen points are Tk's (and the window server's) global coordinates,
        origin at the top-left of the main display; they may be negative on a
        display left of or above it. The drawing area then starts one title
        bar lower. Call before :meth:`run`.
        """
        self._root.geometry(f"{self._width}x{self._height}{geometry_position(x, y)}")

    def paint(self, frame: Frame) -> None:
        """Show ``frame``: 30 rows of 40 ``(character, role)`` cells.

        The frame is checked whole before any cell changes, so a malformed
        frame raises ``ValueError`` and leaves the previous picture intact.
        All cells change within one call, and Tk redraws only when control
        returns to its loop, so no half-replaced picture is ever shown.
        """
        cells = check_frame(frame)
        configure = self._canvas.itemconfigure
        for items_row, cells_row in zip(self._items, cells):
            for item, (character, role) in zip(items_row, cells_row):
                configure(item, text=character, fill=colour_of(role))

    def run(self, on_key: Callable[[str], None], on_tick: Callable[[], None]) -> int:
        """Map the window, deliver keys and ticks until the session ends, and return the exit status.

        ``on_key(name)`` receives Tk's name for each key pressed: ``"Up"``,
        ``"Down"``, ``"Left"``, ``"Right"``, ``"q"``, ``"Q"``, and any other
        key by its own name (``"a"``, ``"space"``, ``"Escape"``, ``"F1"``,
        ``"Shift_L"`` ...). ``on_tick()`` is called ``tick_hz`` times a second.
        The window is closed by the time this returns, whatever ended it.
        """
        if self._closed:
            return self._status
        self._on_key = on_key
        self._on_tick = on_tick
        root = self._root
        try:
            root.deiconify()
            root.lift()
            root.focus_force()
            self._canvas.focus_set()
            self._schedule = TickSchedule(self._clock(), self._tick_hz)
            self._arm_tick()
            root.mainloop()
        finally:
            # Whatever brought us out of the loop (close, an interrupt from the
            # terminal, anything), nothing is left on the screen.
            self._shut()
        return self._status

    def close(self) -> None:
        """End the session: the window closes and :meth:`run` returns 0."""
        self._shut()

    # -- inside -----------------------------------------------------------------

    def _arm_tick(self) -> None:
        self._tick_job = self._root.after(self._schedule.delay_ms(self._clock()), self._tick)

    def _tick(self) -> None:
        self._tick_job = None
        if self._closed:
            return
        self._schedule.advance(self._clock())
        self._arm_tick()
        assert self._on_tick is not None
        self._on_tick()

    def _key_pressed(self, event: tk.Event) -> None:
        if self._closed or self._on_key is None:
            return
        self._on_key(event.keysym)

    def _handler_failed(self, exc_type, exc_value, exc_tb) -> None:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)
        sys.stderr.flush()
        self._status = EXIT_HANDLER_FAILED
        self._shut()

    def _shut(self) -> None:
        if self._closed:
            return
        self._closed = True
        root = self._root
        if self._tick_job is not None:
            try:
                root.after_cancel(self._tick_job)
            except tk.TclError:
                pass
            self._tick_job = None
        try:
            root.quit()
            root.destroy()
        except tk.TclError:
            pass  # already destroyed by the toolkit
