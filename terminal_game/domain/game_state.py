"""The state of one game: everything the rules change and the frame composer reads.

A ``GameState`` is an immutable value. Setup (``game_setup.new_game``) makes the
first one; turn resolution (WI-11) makes each next one, typically with
``dataclasses.replace``. Nothing mutates a state in place.

Fields:

* ``maze``: the :class:`~terminal_game.domain.maze.Maze`.
* ``player``, ``ghost``: their squares, ``(col, row)``.
* ``ghost_heading``: the direction of the ghost's last move as ``(dcol, drow)``,
  one of ``maze.DIRECTIONS``, or ``None`` before its first move. The ghost's
  policy (WI-8) takes it; turn resolution carries it from step to step.
* ``dots``: the squares that still hold a dot.
* ``score``: dots eaten so far.
* ``outcome``: :data:`PLAYING`, :data:`LOST` or :data:`WON`. The values are the
  same as the status line's (``presentation.status_line``), so the composer can
  hand ``state.outcome`` straight to it.

Pure domain code: standard library only, no clock, no randomness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from terminal_game.domain.maze import Maze, Square

PLAYING = None  # type: Optional[str]
LOST = "lost"
WON = "won"


@dataclass(frozen=True)
class GameState:
    maze: Maze
    player: Square
    ghost: Square
    dots: frozenset[Square]
    score: int = 0
    outcome: Optional[str] = PLAYING
    ghost_heading: Optional[Square] = None

    def __post_init__(self) -> None:
        # Keep our own frozen copy, so a caller's set cannot change the state.
        object.__setattr__(self, "dots", frozenset(self.dots))
