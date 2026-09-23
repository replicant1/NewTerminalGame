"""Judging captures of the game window cell by cell. Test support only; pure.

Two things on the edge of the window belong to macOS, not to the game, and
are measured rather than assumed (2026-09-23, macOS 26, Retina, window 400 x
570 points captured at 800 x 1140 pixels):

* a one-pixel outline, grey ``(25, 25, 25)``, drawn over the left, right and
  bottom edges of the drawing area;
* the window's **rounded bottom corners**, which clip the drawing area and
  show whatever is behind the window. The clipped region is anchored in each
  bottom corner, lies within 24 x 24 points of it, and is a staircase: every
  clipped pixel has clipped pixels between it and the corner.

A capture of an empty picture (the game paints nothing) shows exactly those
pixels and nothing else; :func:`blank_findings` checks that. The pixels it
finds lit are then the **clip mask** for every other capture from the same
window (:func:`clip_mask`), so a glyph judged later is never blamed for the
desktop showing through a corner.
"""

from shell_screen import Image

CORNER_POINTS = 24


def is_black(rgb) -> bool:
    return max(rgb) == 0


def _outline(image: Image, x: int, y: int) -> bool:
    return x in (0, image.width - 1) or y == image.height - 1


def _in_corner_square(image: Image, x: int, y: int, scale: float) -> bool:
    side = round(CORNER_POINTS * scale)
    return y >= image.height - side and (x < side or x >= image.width - side)


def blank_findings(image: Image, scale: float) -> dict:
    """Check a capture of an empty picture. Every list in the result is empty when it holds.

    ``stray``: non-black pixels that are neither the outline nor in a corner square.
    ``not_staircase``: lit corner pixels without lit pixels towards the corner.
    """
    w, h = image.width, image.height
    lit = lambda x, y: not is_black(image.rgb(x, y))  # noqa: E731
    stray = [
        (x, y) for y in range(h) for x in range(w)
        if lit(x, y) and not _outline(image, x, y) and not _in_corner_square(image, x, y, scale)
    ]
    side = round(CORNER_POINTS * scale)
    bad = []
    for y in range(h - side, h):
        for x in range(side):
            if lit(x, y) and ((x > 0 and not lit(x - 1, y)) or (y < h - 1 and not lit(x, y + 1))):
                bad.append((x, y))
            xr = w - 1 - x
            if lit(xr, y) and ((xr < w - 1 and not lit(xr + 1, y)) or (y < h - 1 and not lit(xr, y + 1))):
                bad.append((xr, y))
    corner_lit = sum(
        1 for y in range(h - side, h) for x in list(range(side)) + list(range(w - side, w))
        if lit(x, y) and not _outline(image, x, y)
    )
    return {"stray": stray, "not_staircase": bad, "corner_lit": corner_lit}


def clip_mask(blank: Image, scale: float) -> set[tuple[int, int]]:
    """The pixels macOS owns in this window: the outline, and the lit corner pixels of
    ``blank`` grown by one pixel (a corner's antialiased edge varies with what is behind it)."""
    w, h = blank.width, blank.height
    side = round(CORNER_POINTS * scale)
    mask = {(x, y) for y in range(h) for x in range(w) if _outline(blank, x, y)}
    for y in range(h - side, h):
        for x in list(range(side)) + list(range(w - side, w)):
            if not is_black(blank.rgb(x, y)):
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        mask.add((x + dx, y + dy))
    return mask


def corner_mask(image: Image, scale: float) -> set[tuple[int, int]]:
    """The outline and both whole bottom-corner squares: the mask for a window with no blank capture.

    Coarser than :func:`clip_mask` (it hides the corner squares entirely, not
    just the clipped pixels), for a game window that is never blank.
    """
    return {
        (x, y) for y in range(image.height) for x in range(image.width)
        if _outline(image, x, y) or _in_corner_square(image, x, y, scale)
    }


def shade_error(rgb, colour) -> tuple[float, float]:
    """How far ``rgb`` is from a shade of ``colour`` (``colour`` blended with black).

    Returns ``(alpha, error)``: the blend amount in [0, 1] that fits best, and
    the largest channel difference left over.
    """
    dot = sum(p * c for p, c in zip(rgb, colour))
    norm = sum(c * c for c in colour)
    alpha = min(1.0, max(0.0, dot / norm)) if norm else 0.0
    return alpha, max(abs(p - alpha * c) for p, c in zip(rgb, colour))


def cell_box(col: int, row: int, cell_w: float, cell_h: float, inset: int):
    x0, x1 = round(col * cell_w) + inset, round((col + 1) * cell_w) - inset
    y0, y1 = round(row * cell_h) + inset, round((row + 1) * cell_h) - inset
    return x0, x1, y0, y1


def judge_cell(image: Image, mask: set, col: int, row: int, cell_w: float, cell_h: float,
               colour, inset: int, tolerance: float = 24.0) -> dict:
    """Inspect one cell: how much strong ink it holds, and any ink that is not a shade of ``colour``.

    Masked pixels are skipped, and so are ``inset`` pixels at each side of the
    cell: box-drawing glyphs are designed to overlap their neighbours by a
    fraction of a point so that lines join, and that overlap is not a glyph
    out of its cell.
    """
    x0, x1, y0, y1 = cell_box(col, row, cell_w, cell_h, inset)
    strong = 0
    foreign = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x, y) in mask:
                continue
            rgb = image.rgb(x, y)
            if is_black(rgb):
                continue
            alpha, err = shade_error(rgb, colour)
            if err > tolerance:
                foreign.append((x, y, rgb))
            elif alpha >= 0.5:
                strong += 1
    return {"strong": strong, "foreign": foreign}


def cell_distance(a: Image, b: Image, col: int, row: int, cell_w: float, cell_h: float,
                  mask: set) -> float:
    """Mean absolute channel difference between the same cell in two captures (0-255), mask skipped."""
    x0, x1, y0, y1 = cell_box(col, row, cell_w, cell_h, 0)
    stride = a.width * 4
    if all(
        a.data[y * stride + x0 * 4: y * stride + x1 * 4] == b.data[y * stride + x0 * 4: y * stride + x1 * 4]
        for y in range(y0, y1)
    ):
        return 0.0  # byte-identical, the usual case
    total = n = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x, y) in mask:
                continue
            total += sum(abs(p - q) for p, q in zip(a.rgb(x, y), b.rgb(x, y)))
            n += 3
    return total / n if n else 0.0
