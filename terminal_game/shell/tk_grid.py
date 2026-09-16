# -*- coding: utf-8 -*-
"""WI-2 — the Tk binding for the character grid surface.

This module is deliberately tiny and deliberately the only place in the
project that imports the windowing toolkit for the surface.  Everything with
a decision in it lives in :mod:`terminal_game.shell.grid_surface`, which names
no toolkit and is unit-tested with a recording double.

**Nothing here may be called from an automated test.**  Constructing a font
probe or a canvas needs a live toolkit interpreter, and the suite never
creates one.  What is here is exercised by the walking skeleton (WI-4) and
looked at by a person (WI-16).

The interpreter is ``/usr/bin/python3`` — 3.9.6 with Tk 8.5.9.  The other
interpreter on this machine has no ``_tkinter`` at all and this import fails
outright on it, which is the loud failure we want rather than a mystery.
"""

from __future__ import annotations

import tkinter
import tkinter.font

from terminal_game.shell.grid_surface import (
    FONT_FAMILY,
    FONT_POINT_SIZE,
    GROUND,
    CellMetrics,
    CharacterGridSurface,
    font_specification,
    measure_cell_metrics,
)

__all__ = ["TkFontProbe", "create_surface"]


class TkFontProbe:
    """Answers the four questions :func:`measure_cell_metrics` asks of a font.

    It needs a toolkit interpreter — a ``Tk`` root, or any widget — but it
    does **not** need a mapped window: a root that has been withdrawn before
    the event loop is entered measures perfectly well and never appears on
    anybody's screen.
    """

    __slots__ = ("_master", "_cache")

    def __init__(self, master) -> None:
        self._master = master
        self._cache = {}

    def _font(self, family: str, point_size: int):
        key = (family, point_size)
        if key not in self._cache:
            self._cache[key] = tkinter.font.Font(
                root=self._master, family=family, size=point_size
            )
        return self._cache[key]

    def families(self):
        return tkinter.font.families(self._master)

    def resolved_family(self, family: str, point_size: int) -> str:
        return self._font(family, point_size).actual("family")

    def advance(self, family: str, point_size: int, glyph: str) -> int:
        return self._font(family, point_size).measure(glyph)

    def linespace(self, family: str, point_size: int) -> int:
        return self._font(family, point_size).metrics("linespace")


def create_surface(
    master,
    family: str = FONT_FAMILY,
    point_size: int = FONT_POINT_SIZE,
) -> CharacterGridSurface:
    """Build the real surface inside *master*, or raise.

    Raises a :class:`~terminal_game.shell.grid_surface.SurfaceFontError` if
    the pinned font is missing, substituted, or not fixed width — see that
    module for why a quiet substitution is the worst outcome available.

    The canvas is created but not placed: where it sits in the window is the
    window owner's business (WI-3), not the surface's.  Ask the returned
    surface for :meth:`~CharacterGridSurface.pixel_size` to size the window.
    """
    metrics: CellMetrics = measure_cell_metrics(
        TkFontProbe(master), family, point_size
    )
    canvas = tkinter.Canvas(master, background=GROUND, highlightthickness=0)
    return CharacterGridSurface(
        canvas, metrics, font=font_specification(family, point_size)
    )
