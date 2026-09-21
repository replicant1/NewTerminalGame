"""The application's own native window — WIN-1, WIN-2, WIN-3 and WIN-5.

    *"The game opens in a window of its own, so it does not disturb whatever
    else the player has on screen."* (WIN-1)

    *"The window is exactly 40 characters wide and 30 rows deep, in a
    fixed-width typeface large enough to read comfortably, on a black
    background."* (WIN-2)

    *"The window is titled Terminal Game."* (WIN-3)

    *"The window closes by itself as soon as the game ends."* (WIN-5)

This is the Shell layer, which may import anything.  It owns the window and
nothing else: **what goes in the window is
:class:`~terminal_game.presentation.surface.GridSurface`'s**, and **where the
window goes is WI-15's** — placement is deliberately absent here, and WI-15 is
the only later writer.

Under candidate 2 three of those four requirements stop being caveats.  The
title is whatever this process says it is, with nothing composing around it;
the size is a pixel rectangle this process asks for; the window closes because
the process that owns it closes it.  The architect's assumptions A1 and A5 and
his caution C2 all fall away with the terminal they were about.

What "closes itself and ends the process" means here
----------------------------------------------------

**This module does not exit the process, and that is deliberate.**
:meth:`GameWindow.close` destroys the toplevel; destroying the toplevel is
what makes :meth:`GameWindow.run` — that is, ``mainloop()`` — return; and when
the entry point's call to :meth:`run` returns, there is nothing left to do and
the process ends on its own.

Calling ``sys.exit`` in here would end the process in the middle of a test as
readily as in the middle of a game, and would make WIN-5 impossible to check
without a subprocess.  Ending by *running out of work* is both the honest
mechanism and the testable one.

This follows assumption **P1** (the architect's A3, contradiction C-1): WIN-5's
"as soon as the game ends" is read as *when the session ends*, not *when the
outcome is decided*, so that END-5 and END-6 can also be true.  That reading is
unanswered by the user and is human item 1.  Nothing here depends on which way
it goes — this window closes when it is asked to, and WI-11 decides when to
ask.

Never ``update()``
------------------

``root.update()`` **blocks forever** on Tcl/Tk 8.5 under macOS 26 once the
window is mapped — measured under S-2, bisected with ``faulthandler``, pinned
at ``tkinter/__init__.py`` line 1314.  Nothing in this module calls it, and
WI-5's surface does not either.

**AMEND-6: that defect belongs to the toolkit that was replaced.**  On the
Tcl/Tk 9.0.4 the project now pins, ``update()`` on a mapped window returns.
**The prohibition stays**, because nothing here needs to lift it — every
repaint path is built on ``update_idletasks()``, which was never the problem —
and because a rule that costs nothing to keep is cheaper than a second
measurement of a hang.

The obvious worry was that the event loop shared that path, in which case the
first item to show a real window would hang with it on the user's desk.  **It
does not.**  Measured for WI-6 on a real mapped window: ``mainloop()`` ran,
``after()`` fired inside it, ``destroy()`` from inside that callback made
``mainloop()`` return after 629 ms, and ``update_idletasks()`` on the mapped
window returned in 10.6 ms.
"""

from __future__ import annotations

import tkinter
from typing import Callable, List, Optional, Tuple

from terminal_game.presentation import palette
from terminal_game.presentation.field import Field
from terminal_game.presentation.metrics import COLUMNS, ROWS, CellMetrics
from terminal_game.presentation.surface import GridSurface
from terminal_game.shell import placement
from terminal_game.shell.placement import Point

#: WIN-3's title, exactly.  Nothing is appended to it and nothing composes
#: around it; the application sets it and the application is the only thing
#: that has a say.
TITLE = "Terminal Game"


class GameWindow(object):
    """The one window this game has.

    Built **withdrawn**, so it is never on the screen half-formed: the title,
    the size, the ground and the first frame can all be set before anybody
    sees it.  :meth:`show` is what puts it there, and WI-15 will place it
    immediately before that.

    ``on_close`` is called once, when the window closes, whether that was
    :meth:`close`, the window manager's close button, or the session ending.
    It is how the Shell tells the rest of the game that it is over.
    """

    def __init__(
        self,
        master: "Optional[tkinter.Misc]" = None,
        on_close: "Optional[Callable[[], None]]" = None,
        title: str = TITLE,
        ground: str = palette.GROUND,
    ) -> None:
        if not palette.is_colour(ground):
            raise ValueError(
                "the ground must be an #rrggbb triple, not {!r}".format(ground)
            )

        self._closed = False
        self._on_close = on_close
        self._owns_interpreter = master is None

        # **One Tk interpreter per process.**  The game creates it, because
        # the game is the only thing running; a test passes its own, because
        # a suite runs many windows in one process and creating a second
        # interpreter is what makes this build unstable.  Measured for WI-6:
        # a ``mainloop()`` entered after other roots had been created and
        # destroyed in the same process segfaulted under the suite, and
        # stopped doing so the moment every window became a Toplevel on one
        # root.  Either way this is a real native window of its own, which is
        # what WIN-1 asks for.
        root = (
            tkinter.Tk() if master is None else tkinter.Toplevel(master)
        )  # type: tkinter.Misc
        # Withdraw before the first turn of the event loop.  Tk defers mapping
        # a toplevel to idle time, so one withdrawn here never maps at all —
        # it is not shown and then hidden, it is never shown.  Measured by
        # S-1; it is also what keeps the default suite off the user's screen.
        root.withdraw()  # type: ignore[attr-defined]
        self._root = root

        root.title(title)
        root.configure(background=ground)

        self._surface = GridSurface(root, ground=ground)
        self._surface.widget.pack(fill="none", expand=False)

        width, height = self._surface.pixel_size
        root.geometry("{}x{}".format(width, height))
        # WIN-2 says *exactly* 40 x 30.  A window the player can drag larger
        # would have rows and columns the game does not know about.
        root.resizable(False, False)

        # The close button is a close request like any other, so it goes
        # through the same door.  Without this, the button destroys the window
        # behind the game's back and `on_close` never fires.
        root.protocol("WM_DELETE_WINDOW", self.close)

        root.update_idletasks()

    # -- what is in the window --------------------------------------------

    @property
    def surface(self) -> GridSurface:
        """The character grid this window contains."""
        return self._surface

    def present(self, field: Field) -> None:
        """Show ``field``.  The window's only route to a picture."""
        self._require_open("present a frame on")
        self._surface.present(field)

    # -- WIN-2 and WIN-3, as the window reports them ----------------------

    @property
    def title(self) -> str:
        """WIN-3's title, as the toolkit has it.

        Whether the *titlebar* shows exactly this and nothing else is a
        different question, and not one an agent can answer — it is human
        item 2 of plan section 9.  Under candidate 2 it should be a
        formality, because nothing composes around what this process sets.
        """
        return self._root.title()

    @property
    def pixel_size(self) -> Tuple[int, int]:
        """WIN-2's size in pixels, as WI-5's metrics computed it for 40 x 30."""
        return self._surface.pixel_size

    @property
    def requested_size(self) -> Tuple[int, int]:
        """The size the window asks the window manager for.

        This is the number to check while the window is withdrawn: an unmapped
        toplevel reports ``winfo_width`` of 1, because it has not been given a
        size by anybody yet.  Measured for WI-6.
        """
        return (self._root.winfo_reqwidth(), self._root.winfo_reqheight())

    @property
    def ground(self) -> str:
        """WIN-2's black background."""
        return str(self._root.cget("background"))

    @property
    def metrics(self) -> CellMetrics:
        """The cell metrics the window was sized from."""
        return self._surface.metrics

    @property
    def grid_size(self) -> Tuple[int, int]:
        """WIN-2's grid: 40 columns by 30 rows, in cells."""
        return (COLUMNS, ROWS)

    def is_resizable(self) -> bool:
        """Whether the player could drag the window to a different size.

        ``resizable()`` answers with the Tcl string ``"0 0"`` rather than a
        pair of booleans, and every character of that string is truthy — so
        the obvious ``any(bool(flag) for flag in ...)`` reports *True* for a
        window that cannot be resized at all.  Measured for WI-6, after
        writing exactly that bug.
        """
        value = self._root.resizable()
        flags = value.split() if isinstance(value, str) else list(value)
        return any(int(flag) for flag in flags)

    # -- being on the screen, or not --------------------------------------

    def show(self) -> None:
        """Put the window on the screen.

        Everything about it is already right by this point — WI-15 places it
        immediately before this call, and the first frame can already have
        been presented.  Nothing after this changes its size or its title.
        """
        self._require_open("show")
        self._root.deiconify()
        self._root.update_idletasks()

    def is_on_screen(self) -> bool:
        """Whether the window is actually visible.

        Asks ``winfo_ismapped``, not ``state()``: on Tk 8.5 Aqua a mapped,
        non-resizable toplevel reports ``state() == "zoomed"`` rather than
        ``"normal"``, which is measured for WI-6 and is a trap worth not
        walking into twice.
        """
        return self.is_open and bool(self._root.winfo_ismapped())

    # -- WIN-5 -------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        """Whether the window still exists.

        A destroyed Tk root raises rather than answering, which is why this is
        a method and not a call to ``winfo_exists`` at the call site.
        """
        if self._closed:
            return False
        try:
            return bool(self._root.winfo_exists())
        except tkinter.TclError:
            # "application has been destroyed" — measured for WI-6.  Something
            # destroyed the root without going through close(); it is gone
            # either way.
            self._closed = True
            return False

    def close(self) -> None:
        """Close the window, and with it end the session.

        Idempotent: the close button, a quit intent and the session ending can
        all arrive, and only the first does anything.  ``on_close`` is called
        **before** the window is destroyed, so a handler can still look at it.

        The process is not exited here.  Destroying the toplevel is what makes
        :meth:`run` return, and when the entry point's call to :meth:`run`
        returns there is nothing left to do — see the module docstring.
        """
        if self._closed:
            return
        self._closed = True

        if self._on_close is not None:
            self._on_close()

        # Leave the loop *before* destroying, and unconditionally.
        #
        # ``mainloop`` belongs to the Tk **interpreter**, not to a window.
        # When this object owns the interpreter, destroying its root is
        # enough to end the loop.  When it does not — a Toplevel on somebody
        # else's root — destroying it leaves the interpreter running and
        # **mainloop never returns**: a window gone from the screen and a
        # process that will not end.
        #
        # Measured for WI-6, by hitting it: a ``needs_window`` run hung with
        # a window on the screen until it was killed.  Quitting first makes
        # the guarantee in :meth:`run` — that there is always a way out —
        # true regardless of who constructed the window, rather than true
        # only in production and documented everywhere else.
        try:
            self._root.quit()
        except tkinter.TclError:
            pass

        try:
            self._root.destroy()
        except tkinter.TclError:
            pass  # already gone; closing something twice is not an error

    # -- the event loop ----------------------------------------------------

    def run(self) -> None:
        """Run the event loop until the window closes.

        Returns when the window is destroyed and not before, which is what
        makes :meth:`close` end the process: the entry point has nothing after
        this call.

        **There is always an exit path.**  A ``mainloop`` with no way out is
        the thing plan section 1.5 forbids, and here the way out is
        :meth:`close` — reachable from the window manager's close button, from
        a quit intent, and from the session.  Measured on a real mapped window
        for WI-6: ``mainloop`` returns when the window is destroyed from inside
        an ``after`` callback.
        """
        if self._closed:
            return
        self._root.mainloop()

    def stop(self) -> None:
        """Leave the event loop without closing the window.

        :meth:`run` returns; the window and everything on it survive, and
        :meth:`run` may be entered again.  This is the seam WI-14 and WI-16
        need — the plan asks for the timer to be drivable "from a test
        without waiting", and something has to end the loop when the test has
        seen what it came for.

        Measured for WI-6, and it is the reason the loop can be exercised in
        the default suite at all: **``mainloop()`` runs on a withdrawn root,
        ``after`` callbacks fire inside it, and ``quit()`` returns from it —
        with nothing ever reaching the screen.**
        """
        if self.is_open:
            self._root.quit()

    def after(self, milliseconds: int, callback: "Callable[[], None]") -> str:
        """Call ``callback`` once, later, on the event loop.

        The Shell owns the timer as it owns the loop.  WI-14's tick goes
        through here, and so does anything that needs the loop running before
        it happens.
        """
        self._require_open("schedule work on")
        return self._root.after(milliseconds, callback)

    def cancel(self, handle: str) -> None:
        """Cancel work scheduled by :meth:`after`."""
        if self.is_open:
            self._root.after_cancel(handle)

    def bind_key(self, sequence: str, callback: "Callable[..., None]") -> None:
        """Route a key event to ``callback``.

        Bound on the **toplevel**, not on the canvas: the surface refuses the
        keyboard focus so that no text caret can ever appear (SCRN-7), which
        means keys have to be caught here.  WI-13 turns the events into
        intents; this only carries them.
        """
        self._require_open("bind a key on")
        self._root.bind(sequence, callback)

    # -- placement, added by WI-15 -----------------------------------------

    def move_to(self, point: "Point") -> None:
        """Put the window's top-left corner at ``point`` (WIN-4).

        The only thing WI-15 adds to the window owner, and it adds nothing
        else. *Where* the window goes is
        :mod:`terminal_game.shell.placement`'s decision; this carries it out.

        Position only. The geometry string has no ``WxH`` in it, so the size
        WI-6 asked for is not disturbed — a geometry string carrying a size
        would silently overrule it.

        Negative coordinates are ordinary: the displays on this desk are at
        ``(-3509, -1440)`` and ``(-949, -1440)``, and
        :func:`~terminal_game.shell.placement.geometry_string` is what makes
        sure a negative value stays an absolute coordinate rather than
        becoming an offset from the opposite edge.
        """
        self._require_open("move")
        self._root.wm_geometry(placement.geometry_string(point))

    def position(self) -> "Optional[Point]":
        """Where Tk says the window's top-left corner is, or ``None``.

        Parsed back out of the geometry string rather than read from
        ``winfo_x``/``winfo_y``, because those answer 0 for a window that has
        never been mapped and this has to be usable before :meth:`show`.

        **A window always has a position**, whether or not anything has
        placed it: Tk gives a fresh toplevel one of its own choosing — ``(5,
        38)`` on this build, measured for WI-15. So this answering something
        does not mean the window was deliberately placed.

        ``None`` only when the window is closed, or when Tk has expressed the
        position as an offset from the right or bottom edge, which is not an
        absolute coordinate and is not guessed at — see
        :func:`~terminal_game.shell.placement.position_in_geometry`.
        """
        if not self.is_open:
            return None
        return placement.position_in_geometry(self._root.wm_geometry())

    def bound_key_sequences(self) -> "List[str]":
        """Every key sequence bound on the window, for a test to check the wiring.

        In Tk's own normalised spelling, which is not always the one the
        binding was made with: ``<Key-q>`` comes back as ``q``.  Measured for
        WI-6.  This is a diagnostic — what actually matters is that a key
        reaches its callback, and that is a different test.
        """
        if not self.is_open:
            return []
        return sorted(str(name) for name in self._root.bind())

    # -- housekeeping ------------------------------------------------------

    def _require_open(self, doing: str) -> None:
        if not self.is_open:
            raise RuntimeError(
                "cannot {} a window that has been closed; WIN-5 says the "
                "window closes when the game ends, and it has".format(doing)
            )

    def __repr__(self) -> str:
        if not self.is_open:
            return "GameWindow(closed)"
        width, height = self.pixel_size
        return "GameWindow({!r}, {} x {} cells, {} x {} px, {})".format(
            self.title, COLUMNS, ROWS, width, height,
            "on screen" if self.is_on_screen() else "not shown yet",
        )
