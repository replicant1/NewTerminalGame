"""The one place WI-14 actually looks at the screen.

``anchor.py`` is the arithmetic and the policy; this is the query, and it is
the only module in this item that names the windowing toolkit.  Same shape as
``toolkit.py`` / ``tk_toolkit.py``, for the same reason: everything above the
seam stays testable with no window.

What this does, and what it deliberately does not
-------------------------------------------------
**It asks Tk where the mouse pointer is, and how big the screen is.**  Both
are answered by the toolkit about the machine, need **no permission of any
kind**, and cannot raise a dialog.

**It does not ask about another application's window**, and there is no code
here that could.  On this machine that needs Accessibility or Automation
permission — an `osascript` to *System Events*, or a Quartz window list —
which only the user can grant, which nobody has granted, and whose first use
puts a modal dialog on the screen.  A modal dialog blocks AppleScript, so it
would hang the next scripted call anyone makes.  **Assumption A2 says use
what the game can see without a prompt; the pointer is what that is.**  See
``docs/findings/WI-14-anchor-query.md``.

The pointer is a proxy for "whatever window the player was last looking at",
and it is a deviation from A2's wording — A2 says *window*.  It is recorded
as one; WIN-4's purpose is that the window "always lands somewhere visible",
and the pointer serves that better than a fixed corner while asking nobody
for anything.

Why the root is withdrawn before anything else happens
------------------------------------------------------
:class:`tkinter.Tk` creates a toplevel, but Tk does not map it until the
event loop runs.  Withdrawing it first and never entering a loop means
**nothing appears on the screen and nothing takes keyboard focus** — the same
technique WI-2's metrics measurements used.  The root is destroyed in a
``finally`` before this function returns, on the failure path as well as the
success path.

**Nothing in the automated suite calls this.**  It constructs a Tk
interpreter, and WI-10's rule 5 forbids the suite doing that.  It is called
by the real entry point (WI-18) and by ``tools/probe_anchor_query.py``.
"""

from __future__ import annotations

from typing import Optional

from .anchor import Anchor, ScreenBounds, is_on_screen
from .toolkit import ScreenPosition

__all__ = ["pointer_anchor"]


def pointer_anchor() -> Optional[Anchor]:
    """Where the mouse pointer is, and how big the screen it is on is.

    ``None`` when there is no usable answer, and there are three ways to get
    one — no toolkit, a toolkit that will not answer, and the interesting
    one below.  All three mean the same thing to the caller: use the
    fallback.  A machine that cannot say where its pointer is is not a
    reason to fail to start.

    **A pointer on a second display is treated as nothing seen, and that is
    measured rather than assumed.**  Tk reports the pointer in the whole
    desktop's coordinates, but ``winfo_screenwidth``/``winfo_screenheight``
    and ``winfo_vrootwidth``/``winfo_vrootheight`` all report the **primary
    display alone**.  On this machine, with Tk 8.5.9 on aqua:

    ==============================  ===================
    ``winfo_pointerxy()``           ``(-175, -448)``
    ``winfo_screenwidth/height``    ``1512 x 982``
    ``winfo_vrootwidth/height``     ``1512 x 982``
    ``maxsize()``                   ``(5120, 2422)``
    ==============================  ===================

    The pointer was on a display up and to the left of the primary, and
    nothing Tk offers gives that display's rectangle: ``maxsize`` knows the
    desktop is bigger but not where it starts, so it cannot bound anything.

    An anchor we cannot bound is an anchor we cannot keep a window inside
    of, and **WIN-4's purpose is that the window lands somewhere visible**.
    Placing it at an unbounded pointer risks a window half off the edge of a
    display; falling back puts it at a fixed position on the primary, where
    it is certainly visible. Visibility is the requirement, so the fallback
    wins.

    This replaces a guard first written on a guess — that Tk answers
    ``-1, -1`` when it cannot say. It does not; it answers with real
    coordinates that happen to be negative, and the guess would have been
    right by accident on this machine and wrong on the next one.
    """
    try:
        import tkinter
    except Exception:
        return None

    root = None
    try:
        root = tkinter.Tk()
        # Before anything can be mapped: no window, no focus, no flash.
        root.withdraw()
        pointer = ScreenPosition(
            x=int(root.winfo_pointerx()), y=int(root.winfo_pointery())
        )
        screen = ScreenBounds(
            width=int(root.winfo_screenwidth()),
            height=int(root.winfo_screenheight()),
        )
    except Exception:
        return None
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass

    if not is_on_screen(pointer, screen):
        return None
    return Anchor(position=pointer, screen=screen)
