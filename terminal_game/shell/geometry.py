"""Tk geometry strings. Pure; no toolkit."""


def geometry_position(x: int, y: int) -> str:
    """Tk's ``+x+y`` for an absolute screen position, including a negative one.

    In Tk's grammar the sign is part of the syntax, not of the number:
    ``-877-1348`` means 877 from the *right* edge and 1348 from the *bottom*,
    while ``+-877+-1348`` is the absolute point (-877, -1348), which is where
    a display left of and above the main one lives (run 7 finding
    WI-15-tk-geometry-signs). So every position is written ``+x+y``.
    """
    return f"+{int(x)}+{int(y)}"
