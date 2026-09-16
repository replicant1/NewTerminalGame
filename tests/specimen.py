# -*- coding: utf-8 -*-
"""The specimen picture from ``docs/FUNCTIONAL_REQUIREMENTS.md``, as data.

Transcribed character for character from the fenced block in section 3 of the
requirements, with the "<- the player" style annotations that sit outside the
picture removed.  Assumption A6 says this picture is normative for the
grid-to-screen mapping, so it is the source every geometry test measures
against rather than a constant somebody retyped.

This module is deliberately *not* named ``test_*``: it is shared test data,
not a test case.
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
