"""Where the game window lands — WIN-4, and what to do when it cannot be known.

WIN-4 asks for the window to appear *"a little below and to the right of
whatever window the player was last looking at"*.  That has two halves, and
only one of them is settled.

**Settled, and all of it here:** given an anchor rectangle, where the window
goes; what to do when there is no anchor; and how to say a position to the
toolkit without getting it wrong.  None of it needs the desktop, so all of it
is tested against supplied numbers, which is what the plan's bar asks for.

**Not settled, and deliberately not chosen here:** *how the anchor is read*.
S-2 measured three routes and the choice between them is a question with the
user (plan section 9, item 4).  So reading the anchor is a **seam** —
:class:`AnchorReader` — and this module ships with the one implementation
that cannot be wrong, :func:`no_anchor`, which reads nothing and prompts
nobody.  Whichever route is chosen becomes a small, tested substitution
rather than a rewrite.

**So WIN-4 is met under assumption P2 and not in general**, until the user
rules.  With :func:`no_anchor` the window is centred on the main display,
which is a sane default and not WIN-4.

## Two measurements that this module exists to encode

**The coordinate space has negative origins.** S-2 measured three displays:
the main one at ``(0, 0) 1512x982``, and two others at ``(-3509, -1440)`` and
``(-949, -1440)``.  Arithmetic that assumes a screen starts at zero is wrong
on this desk, and a clamp to the "screen" is worse than none: Tk's
``winfo_screenwidth``/``winfo_screenheight`` report the **main display only**
(1512x982, with ``vrootx``/``vrooty`` both 0), so clamping would push a
perfectly good anchor on a second display back onto the first.  **Nothing
here clamps.**

**Tk's geometry string does not spell a negative origin the obvious way.**
Measured on a withdrawn root for WI-15:

===============================  ==========================================
``"+{}+{}".format(-877, -1348)``  ``+-877+-1348`` — x = −877, y = −1348
``"{:+d}{:+d}".format(-877, -1348)``  ``-877-1348`` — 877 from the **right**,
                                  1348 from the **bottom**: a different place
===============================  ==========================================

Both are accepted by Tk and both round-trip; they simply mean different
things.  The second is what falls out of tidy-looking sign formatting, and it
is right on the main display and wrong everywhere else.  :func:`geometry_string`
is the one place that formatting is written.
"""

from __future__ import annotations

from typing import NamedTuple, Optional, Tuple

#: Assumption P3: *"a little below and to the right"* is a fixed pixel offset
#: chosen by eye.  The architect used +40, +40 in his own measurement and that
#: is the starting point.  One constant, one test; cheap to change when a
#: human has looked at it.
OFFSET = (40, 40)  # type: Tuple[int, int]


class Rect(NamedTuple):
    """A rectangle in the global display space, top-left origin.

    ``x`` and ``y`` may be negative: the displays on this desk are at
    ``(-3509, -1440)`` and ``(-949, -1440)``.  That is not an error case.
    """

    x: int
    y: int
    width: int
    height: int

    @property
    def origin(self) -> "Point":
        return Point(self.x, self.y)

    @property
    def centre(self) -> "Point":
        return Point(self.x + self.width // 2, self.y + self.height // 2)


class Point(NamedTuple):
    """A position in the global display space.  Negative values are legal."""

    x: int
    y: int

    def offset_by(self, dx: int, dy: int) -> "Point":
        return Point(self.x + dx, self.y + dy)


class AnchorReader:
    """The seam: something that can say where the player was last looking.

    Structural, so any object with a ``read`` method will do — including
    whichever route the user eventually permits, and including a test double
    that returns a rectangle nobody had to go to the desktop for.

    ``read`` returns the anchor's rectangle, or ``None`` when there is no
    anchor to be had.  **It must not prompt for anything**, and if it fails it
    may raise: :func:`anchor_from` turns a raising reader into ``None`` rather
    than letting a placement problem stop a game from starting.
    """

    def read(self) -> "Optional[Rect]":  # pragma: no cover - a protocol
        raise NotImplementedError


class NoAnchor(object):
    """The reader that reads nothing, and therefore cannot prompt or crash.

    This is S-2's option C and it is what ships until the user rules on the
    others.  With it, WIN-4 is not met: the window is centred on the main
    display instead of following the player's last window.  That is the
    honest behaviour rather than a guess at the right one.
    """

    def read(self) -> "Optional[Rect]":
        return None

    def __repr__(self) -> str:
        return "<NoAnchor: WIN-4 not met, window centred on the main display>"


def no_anchor() -> NoAnchor:
    """The default reader.  See :class:`NoAnchor`."""
    return NoAnchor()


def anchor_from(reader: "AnchorReader") -> "Optional[Rect]":
    """Ask ``reader`` for the anchor, degrading to ``None`` if it cannot.

    The plan's bar: *"a failure to read the anchor degrades to a sane default
    rather than crashing or prompting."*  A reader that raises — a missing
    permission, a dead process, an unparseable answer — is a reason to place
    the window somewhere sensible, never a reason for the game not to start.

    The exception is swallowed deliberately and broadly.  There is no useful
    distinction here between the ways reading an anchor can fail, and the
    response to all of them is the same one.
    """
    try:
        anchor = reader.read()
    except Exception:
        return None
    if anchor is None:
        return None
    return Rect(*anchor)


def below_and_right_of(anchor: "Rect", offset: "Tuple[int, int]" = OFFSET) -> "Point":
    """WIN-4: a little below and to the right of the anchor's top-left corner.

    Offset from the **origin**, not the centre and not the bottom-right, so
    the game window overlaps the anchor rather than being flung past a large
    one.  No clamping — see the module docstring.
    """
    return anchor.origin.offset_by(offset[0], offset[1])


def centred_on(display: "Rect", window_size: "Tuple[int, int]") -> "Point":
    """The sane default when there is no anchor: the middle of the display.

    Not WIN-4, and honest about it.  Integer division, so a window that
    cannot be centred to the pixel sits half a pixel up and left rather than
    somewhere unpredictable.
    """
    width, height = window_size
    return Point(
        display.x + (display.width - width) // 2,
        display.y + (display.height - height) // 2,
    )


def placement_for(
    reader: "AnchorReader",
    display: "Rect",
    window_size: "Tuple[int, int]",
    offset: "Tuple[int, int]" = OFFSET,
) -> "Point":
    """Where to put the window: beside the anchor, or centred if there is none.

    The whole decision in one place, so that the fallback is not something a
    caller has to remember to apply.
    """
    anchor = anchor_from(reader)
    if anchor is None:
        return centred_on(display, window_size)
    return below_and_right_of(anchor, offset)


def geometry_string(point: "Point") -> str:
    """``point`` as a Tk geometry string, position only.

    **The only place this formatting is written**, because the obvious
    alternative is wrong off the main display — see the table in the module
    docstring. ``"+{}+{}"`` keeps the sign inside the field, so a negative
    coordinate stays an absolute coordinate; ``"{:+d}{:+d}"`` would turn it
    into an offset from the opposite edge.

    Position only, with no ``WxH``: the size belongs to WI-6 and a geometry
    string that carried one would silently overrule it.
    """
    return "+{}+{}".format(point.x, point.y)


def position_in_geometry(geometry: str) -> "Optional[Point]":
    """The absolute position in a Tk geometry string, or ``None`` if it has none.

    The inverse of :func:`geometry_string`, and it carries the same trap the
    other way round.  Tk's geometry grammar is ``WxH±X±Y``, and the sign is
    **part of the grammar, not part of the number**:

    * ``+100`` — 100 from the left.  An absolute coordinate.
    * ``+-100`` — −100 from the left.  Also an absolute coordinate, and the
      one a second display at a negative origin needs.
    * ``-100`` — 100 from the **right** edge.  Not an absolute coordinate at
      all, and not something this function can turn into one without knowing
      the display, so it answers ``None`` rather than guessing.

    Returning ``None`` for the from-the-edge form matters: silently treating
    ``-100`` as ``x = -100`` would be wrong by the width of a display, which
    is exactly the class of mistake S-2 found in Terminal's own AppleScript
    ``position``.
    """
    body = geometry.split("x", 1)[-1] if "x" in geometry else geometry
    # Find the two sign characters that begin the X and Y fields.  Scanning
    # from the right is what makes "+-877+-1348" come apart correctly: the
    # inner minus signs belong to the numbers, the outer plusses to the
    # grammar.
    signs = [i for i, ch in enumerate(body) if ch in "+-"]
    starts = []  # type: list
    for index in signs:
        if index == 0 or body[index - 1] not in "+-":
            starts.append(index)
    if len(starts) < 2:
        return None
    x_at, y_at = starts[-2], starts[-1]
    x_field, y_field = body[x_at:y_at], body[y_at:]
    if x_field.startswith("-") or y_field.startswith("-"):
        return None  # measured from the far edge; not an absolute position
    try:
        return Point(int(x_field[1:]), int(y_field[1:]))
    except ValueError:
        return None
