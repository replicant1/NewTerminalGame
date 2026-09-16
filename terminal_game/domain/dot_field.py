"""WI-6 — the dots laid along the corridors, and what happens when one is taken.

A :class:`DotField` says which squares still hold a dot.  It is a value:
taking a dot returns a new field rather than changing this one, which is what
lets a test assert that a move into a wall changed *nothing* by comparing two
whole game states.

The requirements this module owns:

* **START-3** — every corridor square holds one dot except the player's.
* **SCORE-1** — taking a dot removes it for the rest of the game.
* **SCORE-3** — a square whose dot has gone reports no dot, so moving onto it
  again scores nothing.

It knows nothing about the score, the player or the ghost.  Whether taking a
dot adds a point is the turn resolver's business (WI-11), not the dot field's:
that separation is what keeps SCORE-3 from being two rules in two places.
"""

from __future__ import annotations

from typing import FrozenSet, Iterable

from .maze import Maze, Square

__all__ = ["DotField"]


class DotField:
    """The squares that still hold a dot."""

    __slots__ = ("_squares",)

    def __init__(self, squares: Iterable[Square]) -> None:
        frozen = frozenset(squares)
        for square in frozen:
            if not isinstance(square, Square):
                raise ValueError("a dot must sit on a Square, got %r" % (square,))
        self._squares = frozen

    # ------------------------------------------------------------------
    # Laying the dots out
    # ------------------------------------------------------------------

    @classmethod
    def over_corridors_except(cls, maze: Maze, empty_square: Square) -> "DotField":
        """START-3: a dot on every corridor square but one.

        ``empty_square`` is the square the player starts on, which begins
        empty.  It must be a corridor square of this maze; a wall square would
        mean the field held a dot on every corridor after all, which is not
        what START-3 says and is worth failing over rather than ignoring.
        """
        if not maze.is_corridor(empty_square):
            raise ValueError(
                "the empty square %r must be a corridor square" % (tuple(empty_square),)
            )
        return cls(
            square for square in maze.corridor_squares() if square != empty_square
        )

    # ------------------------------------------------------------------
    # Asking
    # ------------------------------------------------------------------

    def has_dot(self, square: Square) -> bool:
        """Is there still a dot here?"""
        return square in self._squares

    def squares(self) -> FrozenSet[Square]:
        """Every square that still holds a dot."""
        return self._squares

    @property
    def remaining(self) -> int:
        """How many dots are left to eat."""
        return len(self._squares)

    @property
    def is_empty(self) -> bool:
        """True once every dot has been taken — END-2's condition."""
        return not self._squares

    # ------------------------------------------------------------------
    # Taking
    # ------------------------------------------------------------------

    def without_dot_at(self, square: Square) -> "DotField":
        """The field as it is once the dot here has been taken.

        Returns a field with one fewer dot, or **this same field** when there
        was no dot to take — so taking twice takes once (SCORE-1, SCORE-3).
        The caller decides whether a point was scored, by asking
        :meth:`has_dot` first.
        """
        if square not in self._squares:
            return self
        return DotField(self._squares - {square})

    # ------------------------------------------------------------------
    # Value semantics
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DotField):
            return NotImplemented
        return self._squares == other._squares

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash(self._squares)

    def __repr__(self) -> str:
        return "DotField(%d dots)" % (len(self._squares),)
