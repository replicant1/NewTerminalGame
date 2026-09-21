"""Read what actually reached the screen, rather than what Tk was told.

Every other test in this suite asserts the model, or the toolkit's record of
the model.  Neither can see a pixel: Tk faithfully reports ``text='╔'`` on a
canvas item it never draws, so a window showing nothing passes all of them.
That gap is how a game that renders a blank window shipped with 996 tests
green, and it is what this module closes.

Standard library only.  ``screencapture`` ships with macOS, BMP is a header
and a block of BGRA, and neither Pillow nor numpy joins ``requirements.txt``
for this.

**Take the geometry from Tk, never from AppleScript.**  ``winfo_rootx`` and
``winfo_rooty`` are the window's own answer.  AppleScript's ``position`` is
wrong by a display height on a secondary display — measured, and recorded in
amendment 1 of the plan — and capturing a screen rectangle derived from it
photographs whatever else happens to be there, which on a developer's desk
means their windows rather than the one under test.
"""

from __future__ import annotations

import collections
import struct
import subprocess
from typing import Dict, Optional, Tuple

Colour = Tuple[int, int, int]


def capture(widget, path) -> "Optional[str]":
    """Photograph ``widget`` exactly. Returns why it could not, or ``None``.

    Call it from inside a running event loop — an ``after`` callback — the way
    the application draws. Never call ``update()`` to force a paint first:
    this project measured that it does not return on a mapped window.
    """
    widget.update_idletasks()
    if not widget.winfo_ismapped():
        return "the widget is not on the screen"
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    w, h = widget.winfo_width(), widget.winfo_height()
    if w <= 1 or h <= 1:
        return "the widget has no size yet (%dx%d)" % (w, h)
    done = subprocess.run(
        ["screencapture", "-x", "-t", "bmp", "-R",
         "%d,%d,%d,%d" % (x, y, w, h), str(path)],
        capture_output=True,
    )
    if done.returncode != 0:
        return "screencapture failed: %s" % done.stderr.decode().strip()
    return None


def histogram(path, sample_every: int = 53) -> "Dict[Colour, int]":
    """The colours in a BMP, as ``{(r, g, b): count}``.

    Sampled rather than exhaustive: a Retina capture of the board is 800×1140
    and the question here is "what is on the screen", which a sample answers
    as well as a census and far faster.
    """
    data = open(str(path), "rb").read()
    offset, = struct.unpack_from("<I", data, 10)
    depth, = struct.unpack_from("<H", data, 28)
    step = depth // 8
    counts = collections.Counter()  # type: collections.Counter
    for i in range(offset, len(data) - step, step * sample_every):
        counts[(data[i + 2], data[i + 1], data[i])] += 1
    return counts


def near(counts, colour: Colour, tolerance: int = 24) -> int:
    """How many sampled pixels are within ``tolerance`` of ``colour``.

    Exact equality is the wrong test. A Retina capture goes through a colour
    profile, and antialiasing puts a fringe around every glyph, so the blue a
    wall is drawn in arrives as a spread rather than one value.
    """
    want_r, want_g, want_b = colour
    return sum(
        n for (r, g, b), n in counts.items()
        if abs(r - want_r) <= tolerance
        and abs(g - want_g) <= tolerance
        and abs(b - want_b) <= tolerance
    )


def blank(counts, threshold: float = 0.98) -> bool:
    """Whether the capture is one flat colour — a window that drew nothing."""
    total = sum(counts.values())
    return bool(total) and max(counts.values()) / total >= threshold
