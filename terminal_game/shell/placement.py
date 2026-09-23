"""Where the game window goes (WIN-4). Pure: rectangles in, a point out; no toolkit, no platform.

Every rectangle is in global screen points with the origin at the top-left of
the main display and y growing downwards: the space the window server's
window list, Tk's ``+x+y`` geometry and ``GameWindow.place`` all use. A display
to the left of or above the main one has negative coordinates.

The policy (IMPLEMENTATION_PLAN.md WI-9):

* with an anchor, the window's top-left goes :data:`OFFSET` points below and to
  the right of the anchor's top-left (C1), on the display the anchor is on (C4);
* moved just far enough to lie wholly on that display's visible area (C2);
* with no anchor, centred on the main display's visible area (C3).
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

#: A little below and to the right: the plan allows 20 to 60 points each way.
OFFSET = 40


@dataclass(frozen=True)
class Rect:
    """A rectangle in global top-left-origin screen points."""

    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def contains_point(self, px: float, py: float) -> bool:
        return self.x <= px < self.right and self.y <= py < self.bottom

    def overlap(self, other: "Rect") -> float:
        w = min(self.right, other.right) - max(self.x, other.x)
        h = min(self.bottom, other.bottom) - max(self.y, other.y)
        return w * h if w > 0 and h > 0 else 0.0

    def contains(self, other: "Rect") -> bool:
        return self.x <= other.x and self.y <= other.y and other.right <= self.right and other.bottom <= self.bottom


def display_for(anchor: Rect, displays: Sequence[Rect]) -> Rect:
    """The visible area of the display the anchor is on.

    That is the display holding the anchor's top-left corner; failing that,
    the one the anchor overlaps most; failing that, the first (main) display.
    """
    for display in displays:
        if display.contains_point(anchor.x, anchor.y):
            return display
    best = max(displays, key=anchor.overlap)
    return best if anchor.overlap(best) > 0 else displays[0]


def _clamp_axis(value: float, low: float, size: float, high_edge: float) -> int:
    """The whole number nearest ``value`` that keeps [v, v + size] inside [low, high_edge].

    The bounds are rounded inwards (ceil the low one, floor the high one), so
    rounding can never push the window over a fractional edge. When no whole
    number fits (the window is bigger than the area), the low edge wins, so the
    title bar stays reachable.
    """
    lo, hi = math.ceil(low), math.floor(high_edge - size)
    if hi < lo:
        return lo
    return min(max(round(value), lo), hi)


def clamp(x: float, y: float, width: float, height: float, area: Rect) -> tuple[int, int]:
    """Move (x, y) just far enough that a width x height window lies wholly in ``area``, in whole points.

    A window bigger than the area is pinned to the area's top-left, so its
    title bar stays reachable.
    """
    return _clamp_axis(x, area.x, width, area.right), _clamp_axis(y, area.y, height, area.bottom)


def place(anchor: Rect | None, window_size: tuple[float, float], displays: Sequence[Rect]) -> tuple[int, int]:
    """The game window's outer top-left corner.

    ``anchor`` is the window that was frontmost at start-up, or ``None``;
    ``window_size`` is the game window's outer size (title bar included);
    ``displays`` are the visible areas of the displays, main display first.
    """
    if not displays:
        raise ValueError("at least one display is needed")
    width, height = window_size
    if anchor is None:
        main = displays[0]
        return clamp(main.x + (main.width - width) / 2, main.y + (main.height - height) / 2, width, height, main)
    area = display_for(anchor, displays)
    return clamp(anchor.x + OFFSET, anchor.y + OFFSET, width, height, area)
