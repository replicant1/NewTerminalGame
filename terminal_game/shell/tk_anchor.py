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

from .anchor import Anchor, ScreenBounds
from .toolkit import ScreenPosition

__all__ = ["pointer_anchor"]


def pointer_anchor() -> Optional[Anchor]:
    """Where the mouse pointer is, and how big its screen is.

    Returns ``None`` rather than raising if the toolkit is not there or
    cannot answer — a machine with no display is a machine where the
    fallback is the right answer, not a reason to fail to start.
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
        pointer_x, pointer_y = root.winfo_pointerxy()
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

    if pointer_x < 0 or pointer_y < 0:
        # Tk answers -1, -1 when it cannot say where the pointer is.
        return None
    return Anchor(
        position=ScreenPosition(x=int(pointer_x), y=int(pointer_y)),
        screen=screen,
    )
