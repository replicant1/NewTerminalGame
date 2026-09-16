# -*- coding: utf-8 -*-
"""WI-7 — the ghost's movement policy.

One pure function of the maze, the square the ghost is on, and the direction
it is heading.  It is *handed* a random source; it reaches for nothing global,
reads no clock, and names nothing above the Domain layer.

The rule, in the order it is applied (GHOST-2, GHOST-3):

1. **Carry straight on while the corridor allows it.**  At a crossroads with
   three ways onward, the ghost still goes straight: a junction is not a
   reason to choose.
2. **Where it cannot, choose uniformly at random among the other ways on** —
   every way except the one it came from.
3. **Turn back the way it came only when there is no other choice.**

Two things the signature says out loud:

**The player is not a parameter (GHOST-4).**  Not an unused one — absent.  The
ghost cannot hunt the player even by mistake, because it is never told where
the player is.  Anyone tempted to add the argument should read GHOST-4 first.

**Nothing here touches the dot field (SCORE-4).**  A dot under the ghost is
still there to be taken, and the simplest way to guarantee that is for this
module never to have heard of dots.

A note on how much randomness there actually is: when straight on is blocked,
the remaining ways are left, right and back, and back is excluded — so the
random choice is between **one or two** options, never three.  At the start of
a game, when the ghost has no heading yet, all four are possible.
"""

from __future__ import annotations

from typing import List, NamedTuple, Optional

from terminal_game.domain.maze import DIRECTIONS, Direction, Maze, Square

__all__ = ["GhostStep", "next_step", "onward_choices"]


class GhostStep(NamedTuple):
    """Where the ghost goes next, and which way it will then be heading.

    Both, because the heading has to be carried to the next tick: "keeps
    going in a straight line" is only meaningful if something remembers which
    line it was going in.
    """

    direction: Direction
    square: Square


class GhostIsWalledIn(ValueError):
    """The ghost is on a square with no way off it at all.

    A dead end has one way off and the ghost reverses out of it.  A square
    with *none* is not somewhere the ghost could have walked to, so this is a
    defect in whoever placed it rather than a case to be handled.  The real
    generator produces no such square (MAZE-5, MAZE-6).
    """


def onward_choices(
    maze: Maze, square: Square, heading: Optional[Direction]
) -> List[Direction]:
    """The ways on that are not the way the ghost came from.

    In ``DIRECTIONS`` order, so that a choice made from a seeded random source
    is reproducible.  With no *heading* — the first tick of a game, before the
    ghost has moved — nothing has been come from, so every way on is a choice.
    """
    ways_on = maze.ways_on(square)
    came_from = None if heading is None else heading.opposite
    return [
        direction
        for direction in DIRECTIONS
        if direction in ways_on and direction is not came_from
    ]


def next_step(
    maze: Maze,
    square: Square,
    heading: Optional[Direction],
    random_source,
) -> GhostStep:
    """Where the ghost goes from *square*, given it is heading *heading*.

    *random_source* is anything with ``choice(sequence)`` — in a real game a
    freshly seeded :class:`random.Random`, in a test a seeded one, so that the
    same seed gives the same walk.  It is consulted whenever the ghost cannot
    carry straight on, even where only one way is left: a forced turn through
    ``choice`` of a one-element list gives the same answer as special-casing
    it, and one code path is easier to be sure of than two.

    *heading* may be ``None``, meaning the ghost has not moved yet and so has
    not come from anywhere; every way on is then a candidate.

    Raises :class:`GhostIsWalledIn` if the square has no way off it, which the
    maze generator's invariants make unreachable.
    """
    ways_on = maze.ways_on(square)
    if not ways_on:
        raise GhostIsWalledIn(
            "the ghost is on {0!r}, which has no way off it".format(
                tuple(square)
            )
        )

    # GHOST-2: straight on while the corridor allows it, junction or no.
    if heading is not None and heading in ways_on:
        return GhostStep(heading, ways_on[heading])

    # GHOST-3: otherwise one of the other ways on, chosen uniformly.
    choices = onward_choices(maze, square, heading)
    if choices:
        direction = random_source.choice(choices)
        return GhostStep(direction, ways_on[direction])

    # GHOST-3: and back the way it came only when there is nothing else —
    # a dead end, which the real maze does not contain but which this
    # function is still total on.
    back = heading.opposite  # type: ignore[union-attr]
    return GhostStep(back, ways_on[back])
