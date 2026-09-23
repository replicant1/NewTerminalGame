"""The specimen picture in docs/FUNCTIONAL_REQUIREMENTS.md section 3, read from
the document itself so that tests are pinned to what the requirements show.

Not a test module.  Shared by tests that reproduce part of the specimen.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

REQUIREMENTS = Path(__file__).resolve().parents[1] / "docs" / "FUNCTIONAL_REQUIREMENTS.md"

#: The maze is 19 squares across, drawn in cells 0 to 36.
MAZE_WIDTH = 19
MAZE_HEIGHT = 29
MAZE_CELLS = 2 * MAZE_WIDTH - 1

ANNOTATION = re.compile(r"\s+←.*$")


def rows() -> List[str]:
    """All 30 rows of the specimen, annotations removed, trailing blanks kept as written."""
    text = REQUIREMENTS.read_text(encoding="utf-8")
    section = text[text.index("## 3. What is on the screen"):text.index("## 4. The maze")]
    block = re.search(r"^```\n(.*?)^```", section, re.S | re.M).group(1)
    picture = [ANNOTATION.sub("", line) for line in block.splitlines()]
    assert len(picture) == MAZE_HEIGHT + 1, "the specimen should be 30 rows"
    return picture


def maze_rows() -> List[str]:
    """The 29 maze rows, each exactly 37 cells."""
    maze = rows()[:MAZE_HEIGHT]
    assert all(len(row) == MAZE_CELLS for row in maze), [len(r) for r in maze]
    return maze
