"""Which fixed-width typeface the window uses, and at what size. Pure; no toolkit.

The window is 40 x 30 *cells*, and a cell is whatever the chosen face
measures (WIN-2, WI-3/C2, C4). So the choice must never land on a
proportional face: asked for a family it does not have, Tk silently hands
back ``.AppleSystemUIFont``, which is proportional (measured 2026-09-23,
Tk 9.0.4). The chooser therefore takes the first preferred family that is
both installed and reports fixed metrics, and falls back to the toolkit's
own fixed font only when none of them is.
"""

from collections.abc import Callable, Iterable

#: In order of preference. Menlo owns every glyph the game draws at its own
#: advance; the others were measured present on this machine, and borrow some
#: box and block glyphs from Menlo (2026-09-23, Tk 9.0.4).
PREFERRED_FAMILIES = ("Menlo", "Monaco", "Courier New", "Andale Mono", "PT Mono")

#: Type size in pixels (Tk's negative size), so ``tk scaling`` cannot move it.
#: 16 px Menlo gives a 10 x 19 cell and a 400 x 570 window. It is the largest
#: Menlo size at which Tk's per-character advance equals the font's own
#: layout advance, so box-drawing glyphs placed one per cell tile exactly as
#: they would in a string (measured 2026-09-23: sizes 12-16 px exact, 17-32 not).
#: Whether it is comfortable to read is WI-3/C15, for a person to judge.
FONT_PIXELS = 16


def choose_family(
    preferred: Iterable[str],
    installed: Iterable[str],
    is_fixed: Callable[[str], bool],
    fallback: str,
) -> str:
    """The first of ``preferred`` that is installed and fixed-width, else ``fallback``.

    ``installed`` is the toolkit's family list; ``is_fixed(family)`` asks the
    toolkit whether that family has fixed metrics; ``fallback`` is the
    toolkit's own fixed-width family, used only when no preference qualifies.
    """
    available = set(installed)
    for family in preferred:
        if family in available and is_fixed(family):
            return family
    return fallback
