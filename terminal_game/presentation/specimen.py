# -*- coding: utf-8 -*-
"""The specimen picture from ``docs/FUNCTIONAL_REQUIREMENTS.md``, as data.

Transcribed character for character from the fenced block in section 3 of the
requirements, with the "<- the player" style annotations that sit outside the
picture removed.  Assumption A6 says this picture is normative for the
grid-to-screen mapping, so it is the source every geometry test measures
against rather than a constant somebody retyped.

Why it lives in the presentation layer
--------------------------------------
It is a **picture**, and this is the layer whose job is to reproduce it:
``frame``, ``wall_glyphs`` and ``frame_composer`` all sit beside it.
Assumption A6 makes it normative for the grid-to-screen mapping, which is
this layer's contract, so the reference and the code obliged to match it
are in one place.

It used to live in ``tests/``, which made ``tools/walking_skeleton.py``
depend on test code — the violation amendment 2 named and WI-10's sixth
rule forbids. Here the dependency runs the right way for everyone: tests
and tools both import *down* into the package, and nothing imports out of
``tests/``.

It is data, not behaviour: string constants, no toolkit, nothing the game
itself reads at run time.
"""

from __future__ import annotations

#: Rows 0..28 of the specimen — the maze.  Every one is 37 characters.
SPECIMEN_MAZE_ROWS = (
    '╔═══════════════════════╦═══════════╗',
    '║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║',
    '║ ▪ ║ ▪ ╔═══════╦════ ▪ ║ ▪ ═════ ▪ ║',
    '║ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║',
    '║ ▪ ║ ▪ ║ ▪ ║ ▪ ║ ▪ ════╣ ▪ ════╗ ▪ ║',
    '║ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║',
    '║ ▪ ║ ▪ ════╣ ▪ ╠════ ▪ ╠════ ▪ ║ ▪ ║',
    '║ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║',
    '║ ▪ ╠════ ▪ ║ ▪ ║ ▪ ╔═══╝ ▪ ════╝ ▪ ║',
    '║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║',
    '║ ▪ ║ ▪ ╔═══════╝ ▪ ║ ▪ ════════╗ ▪ ║',
    '║ ▪ ║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║',
    '║ ▪ ║ ▪ ║ ▪ ╔═══════╩════════ ▪ ║ ▪ ║',
    '║ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪▐█▌▪ ▪ ▪ ▪ ▪ ║ ▪ ║',
    '║ ▪ ║ ▪ ║ ▪ ║ ▪ ════╗ ▪ ║ ▪ ╔═══╝ ▪ ║',
    '║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║ ▪ ║ ▪ ▪ ▪ ║',
    '║ ▪ ╔═══╩═══════╗ ▪ ║ ▪ ║ ▪ ║ ▪ ════╣',
    '║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║ ▪ ║ ▪ ║ ▪ ▪ ▪ ║',
    '║ ▪ ║ ▪ ║ ▪ ■ ▪ ║ ▪ ║ ▪ ║ ▪ ╚═══╗ ▪ ║',
    '║ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║',
    '║ ▪ ║ ▪ ╠════ ▪ ║ ▪ ╠═══════╗ ▪ ║ ▪ ║',
    '║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║',
    '╠═══════╝ ▪ ■ ▪ ║ ▪ ║ ▪ ║ ▪ ╠════ ▪ ║',
    '║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ║',
    '║ ▪ ╔═══════════╩═══════╝ ▪ ║ ▪ ║ ▪ ║',
    '║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║',
    '║ ▪ ║ ▪ ═════════ ▪ ════════════╝ ▪ ║',
    '║▗█▖▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║',
    '╚═══════════════════════════════════╝',
)

#: Row 29 of the specimen — the status line as the picture draws it, with the
#: leading space the STAT-2 literal does not have (contradiction C-3, which is
#: resolved in WI-13 and nowhere else).
SPECIMEN_STATUS_ROW = ' score 0    arrows, q quits'

#: The whole specimen, 30 rows, exactly as printed in the requirements.
SPECIMEN_ROWS = SPECIMEN_MAZE_ROWS + (SPECIMEN_STATUS_ROW,)
