"""WI-6 — the vocabulary a game is carried in.

Everything a game is, at any single moment: the maze, the dots still on it,
where the player and the ghost stand, the score, and which of the two endings
has happened, if either.

It is a **value**.  Nothing here changes in place; every ``with_...`` method
returns a new state.  Two consequences the later work items lean on:

* a rule that must change nothing — a move into a wall (CTRL-3), a tick after
  the game has ended (END-5) — is asserted by comparing the whole state
  before with the whole state after, in one line, rather than by checking
  each field and hoping none was missed;
* the session controller can keep the last picture standing simply by not
  replacing the state it holds.

The order in which the rules of a turn are applied is **not** here.  That is
the turn resolver's, in one named readable place (WI-11, caution C6). This
module only offers the atomic moves a rule can make.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from .dot_field import DotField
from .maze import Maze, Square

__all__ = ["Score", "Outcome", "GameState"]


class Score:
    """The score: starts at zero and can only ever rise (START-4, SCORE-5).

    There is deliberately no way to lower it.  The only operation is
    :meth:`plus_one`, because SCORE-2 says each dot eaten adds exactly one —
    so a score cannot be set, added to in bulk, reset or decremented, and a
    defect that tried to would have nothing to call.
    """

    __slots__ = ("_points",)

    def __init__(self, points: int = 0) -> None:
        if not isinstance(points, int) or isinstance(points, bool):
            raise TypeError("a score is a whole number of points, got %r" % (points,))
        if points < 0:
            raise ValueError("a score can never be negative, got %d" % (points,))
        self._points = points

    @classmethod
    def zero(cls) -> "Score":
        """START-4: where every game starts."""
        return cls(0)

    @property
    def points(self) -> int:
        return self._points

    def plus_one(self) -> "Score":
        """SCORE-2: one dot eaten, one point."""
        return Score(self._points + 1)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Score):
            return NotImplemented
        return self._points == other._points

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash(("Score", self._points))

    def __repr__(self) -> str:
        return "Score(%d)" % (self._points,)


class Outcome(Enum):
    """GAME-2: a game is won or lost, and until then neither.

    There are exactly three members and there is deliberately no fourth: no
    abandoned, no draw, no restart.  GAME-3 says one maze, one ghost, one
    outcome.
    """

    UNDECIDED = "undecided"
    CAUGHT = "caught"    # END-1: the player and the ghost met
    CLEARED = "cleared"  # END-2: the last dot was eaten

    @property
    def is_decided(self) -> bool:
        """Has the game ended? True for both endings, false while playing."""
        return self is not Outcome.UNDECIDED


@dataclasses.dataclass(frozen=True)
class GameState:
    """Everything a game is, at one moment."""

    maze: Maze
    dots: DotField
    player: Square
    ghost: Square
    score: Score
    outcome: Outcome = Outcome.UNDECIDED

    # ------------------------------------------------------------------
    # Asking
    # ------------------------------------------------------------------

    @property
    def is_over(self) -> bool:
        """END-5: once this is true, nothing moves again."""
        return self.outcome.is_decided

    @property
    def actors_share_a_square(self) -> bool:
        """END-1's condition, asked of a state rather than decided by it."""
        return self.player == self.ghost

    # ------------------------------------------------------------------
    # The atomic moves a rule may make
    # ------------------------------------------------------------------

    def with_player_at(self, square: Square) -> "GameState":
        return dataclasses.replace(self, player=square)

    def with_ghost_at(self, square: Square) -> "GameState":
        return dataclasses.replace(self, ghost=square)

    def with_dots(self, dots: DotField) -> "GameState":
        return dataclasses.replace(self, dots=dots)

    def with_score(self, score: Score) -> "GameState":
        return dataclasses.replace(self, score=score)

    def with_outcome(self, outcome: Outcome) -> "GameState":
        return dataclasses.replace(self, outcome=outcome)
