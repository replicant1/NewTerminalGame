"""WI-14 — where the game's window goes (WIN-4).

*"A little below and to the right of whatever window the player was last
looking at, so it always lands somewhere visible."*

This module is the arithmetic and the policy, and it names no windowing
toolkit.  The one thing that actually looks at the screen is
:mod:`terminal_game.shell.tk_anchor`, exactly as ``toolkit.py`` is the seam
and ``tk_toolkit.py`` is the one module that meets Tk.

Assumption A2, and why it bites here
------------------------------------
Seeing *another application's* window means a privileged query — on this
machine, Accessibility or Automation permission, which **only the user can
grant and nobody has**.  A2 confines that to this item: anchor on what the
game can see **without triggering a permission prompt**, and fall back to a
fixed screen offset when there is nothing to anchor to or the query fails.

So an :class:`Anchor` is *whatever permission-free thing we managed to see*,
not necessarily a window.  :func:`terminal_game.shell.tk_anchor.pointer_anchor`
is the one this project actually has; what it returns and why is written up
in ``docs/findings/WI-14-anchor-query.md``.

Three properties the tests own, because each is a way this goes wrong
quietly:

* **The query is attempted exactly once.**  :class:`WindowAnchor` remembers
  the answer, so asking where the window goes twice does not go and look
  twice.  A repeated privileged query is a repeated chance of a dialog.
* **A query that fails is a query that returned nothing.**  It never
  propagates.  A game that will not start because it could not work out
  where to put its window is a worse outcome than a game in the wrong place.
* **A window placed past the edge of the screen is brought back.**  The whole
  point of WIN-4 is that it lands somewhere visible, and an anchor near the
  bottom-right corner plus an offset is exactly how that fails.

**No permission dialog may ever appear during a test**, which is why nothing
in this module looks at anything: the query is a collaborator, and every test
supplies one.
"""

from __future__ import annotations

from typing import Callable, NamedTuple, Optional

from .toolkit import PixelSize, ScreenPosition
from .window_owner import DEFAULT_WINDOW_POSITION

__all__ = [
    "ScreenBounds",
    "Anchor",
    "AnchorQuery",
    "ANCHOR_OFFSET",
    "FALLBACK_POSITION",
    "no_anchor",
    "is_on_screen",
    "brought_onto_screen",
    "WindowAnchor",
]


class ScreenBounds(NamedTuple):
    """How much screen there is to land on, in pixels."""

    width: int
    height: int


class Anchor(NamedTuple):
    """What the game managed to see, and the screen it was on.

    The screen travels with the anchor because whatever could tell us one
    could tell us the other, and without it there is nothing to bring a
    window back onto.
    """

    position: ScreenPosition
    screen: ScreenBounds


#: A query returns an :class:`Anchor`, or ``None`` when it saw nothing.  It is
#: allowed to raise; :class:`WindowAnchor` treats that as ``None``.
AnchorQuery = Callable[[], Optional[Anchor]]


#: "A little below and to the right."  Small enough that the new window reads
#: as sitting on top of what was there, large enough that the thing behind is
#: still identifiable.
ANCHOR_OFFSET = ScreenPosition(x=30, y=30)

#: Where the window goes when there is nothing to anchor to.  This is WI-3's
#: own default, imported rather than retyped: two spellings of one position
#: is the shape of mistake the first-lander rule exists for.
FALLBACK_POSITION = DEFAULT_WINDOW_POSITION


def no_anchor() -> Optional[Anchor]:
    """A query that sees nothing, every time.

    Not a placeholder.  It is the honest answer for *another application's
    window* on a machine where that needs a permission nobody has granted,
    and it is the query to hand :class:`WindowAnchor` when the fallback is
    what you want.  Naming it makes "we deliberately look at nothing"
    something a reader can see rather than infer.
    """
    return None


def is_on_screen(position: ScreenPosition, screen: ScreenBounds) -> bool:
    """Is *position* a point on the screen *screen* describes?

    Sounds trivial and is not.  Tk reports the pointer in the whole
    desktop's coordinates, which on a machine with more than one display can
    be **negative or past the far edge** of the display it can tell you the
    size of — measured on this machine at ``(-175, -448)`` against a primary
    of 1512 x 982.  A point outside the only bounds we have is a point we
    cannot keep a window inside of, which is what makes it worth a name.
    """
    return (
        0 <= position.x < screen.width and 0 <= position.y < screen.height
    )


def brought_onto_screen(
    position: ScreenPosition, size: PixelSize, screen: ScreenBounds
) -> ScreenPosition:
    """*position*, moved the least distance that puts the window on screen.

    The window's whole width and height must fit, so the right-hand limit is
    the screen's width less the window's.  A window wider or taller than the
    screen has no good answer; it is put at the top-left corner, where at
    least the title and the first rows are readable.
    """
    furthest_x = max(0, screen.width - size.width)
    furthest_y = max(0, screen.height - size.height)
    return ScreenPosition(
        x=min(max(0, position.x), furthest_x),
        y=min(max(0, position.y), furthest_y),
    )


class WindowAnchor:
    """Works out where the window goes, asking the screen at most once.

    Hand it a query and it will use it the first time it is asked and not
    again.  Hand it :func:`no_anchor` and it will always give you the
    fallback.
    """

    __slots__ = (
        "_query",
        "_offset",
        "_fallback",
        "_asked",
        "_answer",
        "_failure",
    )

    def __init__(
        self,
        query: AnchorQuery = no_anchor,
        offset: ScreenPosition = ANCHOR_OFFSET,
        fallback: ScreenPosition = FALLBACK_POSITION,
    ) -> None:
        self._query = query
        self._offset = ScreenPosition(*offset)
        self._fallback = ScreenPosition(*fallback)
        self._asked = False
        self._answer: Optional[Anchor] = None
        self._failure: Optional[BaseException] = None

    @property
    def offset(self) -> ScreenPosition:
        return self._offset

    @property
    def fallback(self) -> ScreenPosition:
        return self._fallback

    def anchor(self) -> Optional[Anchor]:
        """What the query saw, asked for at most once in this object's life.

        A query that raises is a query that saw nothing: the game starts at
        the fallback rather than not starting.  What went wrong is not
        swallowed silently — it is available as :attr:`failure` — but it
        never reaches the caller as an exception.
        """
        if not self._asked:
            self._asked = True
            try:
                seen = self._query()
            except Exception as failure:  # noqa: BLE001 - deliberate, see above
                self._failure = failure
                seen = None
            self._answer = seen if isinstance(seen, Anchor) else None
        return self._answer

    @property
    def asked(self) -> bool:
        """Has the query been attempted?  It happens at most once."""
        return self._asked

    @property
    def failure(self) -> Optional[BaseException]:
        """What the query raised, if it raised.

        Kept rather than swallowed, so that the findings document and a
        person debugging a window in the wrong place can both see why the
        fallback was used.  It is never re-raised.
        """
        return self._failure

    def position_for(self, size: PixelSize) -> ScreenPosition:
        """Where a window of *size* goes.

        The anchor plus the offset, brought back onto the screen the anchor
        was found on; or the fallback when there was no anchor.  The fallback
        is not clamped, because a query that saw nothing told us nothing
        about the screen either — and the fallback is a fixed position chosen
        to be safe rather than a computed one that might not be.
        """
        seen = self.anchor()
        if seen is None:
            return self._fallback
        placed = ScreenPosition(
            x=seen.position.x + self._offset.x,
            y=seen.position.y + self._offset.y,
        )
        return brought_onto_screen(placed, PixelSize(*size), seen.screen)
