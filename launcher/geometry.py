"""Pure geometry for the window launcher.

Nothing in here does any I/O, starts a process, reads a clock or knows that
AppleScript exists. It is ordinary arithmetic over screen coordinates, which is
why the whole of WIN-4's placement rule can be checked without a desktop.

Coordinates are macOS window coordinates as the terminal application reports
them: the origin is the top-left of the main display, x grows to the right and
y grows *downwards*. A display placed to the left of the main one therefore has
negative x, and this was measured on the development machine — a terminal window
sitting at x = -879. Any clamp that assumes coordinates start at zero would
teleport the game window onto a different screen.
"""

import collections


class Point(collections.namedtuple("Point", "x y")):
    """A position on the desktop, in window coordinates."""

    __slots__ = ()


class Size(collections.namedtuple("Size", "width height")):
    """A width and height in points."""

    __slots__ = ()


class Offset(collections.namedtuple("Offset", "dx dy")):
    """How far down and to the right of the reference window to sit."""

    __slots__ = ()


class Rect(collections.namedtuple("Rect", "left top right bottom")):
    """A rectangle given by its edges, ``right`` and ``bottom`` exclusive."""

    __slots__ = ()

    @classmethod
    def from_origin_and_size(cls, origin, size):
        return cls(
            origin.x,
            origin.y,
            origin.x + size.width,
            origin.y + size.height,
        )

    @property
    def origin(self):
        return Point(self.left, self.top)

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def size(self):
        return Size(self.width, self.height)

    def contains_point(self, point):
        return (
            self.left <= point.x < self.right
            and self.top <= point.y < self.bottom
        )


#: WIN-4 asks for "a little below and to the right". Architecture assumption A4
#: leaves the number to the implementer; this is it. Thirty-two points is a
#: little over one title-bar height, so the reference window stays readable
#: behind the new one and the new one is unmistakably offset from it.
DEFAULT_OFFSET = Offset(32, 32)

#: Used only when the desktop cannot tell us how big the screen is. Deliberately
#: small: a rectangle smaller than the real screen can only ever pull a window
#: further inside it, which is the safe direction to be wrong in.
DEFAULT_SCREEN = Rect(0, 0, 1024, 768)

#: Used only when the desktop cannot tell us where the reference window was, so
#: there is nothing to be "below and to the right of" (architecture assumption
#: A2 — the permission may be refused). Far enough from the corner to clear the
#: menu bar and to be grabbable.
DEFAULT_POSITION = Point(120, 120)


def target_position(reference, size, screen, offset=DEFAULT_OFFSET):
    """Where to put a window of ``size``, given the window the player was last
    looking at.

    Three rules, applied in this order, each of which can only move the window
    and never grow it:

    1. Start a little below and to the right of the reference window.
    2. Prefer to keep the new window's top-left corner inside the reference
       window's own frame. The reference window is the one the player was just
       looking at, so every point inside it is over a real display — which
       means a corner placed there, with its title bar and its close button,
       is somewhere the player can see and reach.
    3. Then pull the window back so the whole of it fits on the screen, where
       the screen is large enough to hold it; if it is not, pin the corner to
       the screen's own top-left rather than letting it drift off the top or
       the left, where the title bar would be unreachable.

    **Rule 3 wins, and rule 2 is a preference rather than a guarantee.** They
    conflict whenever the reference window sits near an edge and the game
    window is large next to the room that is left, and because rule 3 is
    applied last it is the one that holds. On a 1440 x 900 screen with the
    reference window at ``(1300, 800)-(1440, 900)``, a 357 x 558 game window is
    placed at ``(1083, 342)`` — fully on screen, and 217 points to the *left*
    of the reference window it was supposed to sit below and right of.

    This was chosen deliberately, and it costs something worth naming. The
    screen rectangle comes from :func:`launcher.script.visible_screen_bounds`,
    which on a machine with more than one display is the *union* of them all —
    measured here as ``-3509,-1440,1611,982``, a rectangle much of which is
    over no display at all. So "on the screen rectangle" is a weaker promise
    than "on a display", and in the corner case above, on a multi-display
    desktop, rule 3 can put the corner somewhere rule 2 would not have. What it
    reliably prevents is the window drifting somewhere absurd, and in every
    ordinary case — a reference window with room around it — the two rules
    agree and the question does not arise.

    Reversing the order would make rule 2 the guarantee, at the price of
    letting the window overhang a screen edge. It is not obviously wrong; it is
    simply not what this does. If it is ever wanted, swap the two blocks below
    and clamp rule 2 on both sides rather than only the upper one.

    WIN-4's "so it always lands visible" therefore rests on rule 3 — and on
    macOS, which constrains a window to the display it is on when
    ``set position`` is applied. :meth:`launcher.lifecycle.WindowLauncher.open`
    records where the window actually *went* rather than where it was asked to
    go, for exactly that reason.
    """
    x = reference.left + offset.dx
    y = reference.top + offset.dy

    # 2 — stay inside the reference window's frame.
    x = min(x, reference.left + max(reference.width - 1, 0))
    y = min(y, reference.top + max(reference.height - 1, 0))

    # 3 — fit the whole window on the screen if the screen allows it, and never
    # above or to the left of it.
    x = min(x, screen.right - size.width)
    y = min(y, screen.bottom - size.height)
    x = max(x, screen.left)
    y = max(y, screen.top)

    return Point(x, y)
