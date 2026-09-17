"""GHOST-2, GHOST-3 and GHOST-4 — how the ghost decides where to go.

    *"The ghost keeps going in a straight line for as long as the corridor
    lets it. Where it cannot carry on, it picks one of the other ways on at
    random, and turns back the way it came only when there is no other choice.
    The ghost does not hunt the player and takes no notice of where they are."*

One pure function of the maze, the square the ghost is on, the way it is
heading, and a source of randomness.  **The player is not a parameter**, which
is how GHOST-4 is met: the policy could not hunt if it wanted to, and no test
has to prove a negative about code that cannot express it.

**Randomness arrives as an argument** — ground rule 1.3.  Domain names no
module-level random source, so this module does not import ``random`` and
could not; it takes something that can make a choice and asks it.
:class:`RandomSource` says what that something has to be, and
``random.Random`` satisfies it as it stands, so the Shell can hand one in with
no adapter.

**The order of the candidates is part of the contract.**  A seeded run has to
walk the same maze every time, and ``choice`` over a list is only repeatable
if the list is in a repeatable order — so candidates are always built in
``Direction`` declaration order, never in whatever order a set or a dict
happened to produce.  :func:`candidate_directions` exists so that a caller, or
a test, can see the choice being offered rather than infer it.

**On the reverse clause, which cannot happen in a real game.**  Ruling C-3:
GHOST-3 says the ghost turns back *"only when there is no other choice"*, and
MAZE-5 says every corridor square has at least two ways on — so in any maze
this game generates the non-reversing set is never empty and the clause never
fires.  It is still implemented and still correct, and its test uses a
hand-built maze with a dead end in it, because nothing else can reach it.
Nobody should be puzzled that a generated maze never exercises it.
"""

from __future__ import annotations

from typing import Dict, List, NamedTuple, Protocol, Sequence

from terminal_game.domain.maze import Direction, Maze, Position


class RandomSource(Protocol):
    """Whatever the caller uses to make a random choice.

    Structural on purpose: ``random.Random`` already has this method, so the
    Shell hands one in directly and a test hands in something that chooses
    predictably.  Declaring the shape here rather than importing ``random``
    is what keeps Domain pure — see ground rule 1.3.
    """

    def choice(self, seq: Sequence["Direction"]) -> "Direction":
        """One of ``seq``, chosen uniformly at random."""
        raise NotImplementedError


class GhostMove(NamedTuple):
    """Where the ghost goes, and which way it will then be heading.

    Both, because the square is what the turn resolver needs and the heading
    is what the *next* call to :func:`next_ghost_move` needs.  Returning only
    the square would make the caller re-derive the heading by subtracting two
    positions, which is the sort of arithmetic that goes wrong once.
    """

    direction: Direction
    square: Position


def _ways_on(maze: Maze, square: Position) -> Dict[Direction, Position]:
    """The maze's exits from ``square``, with a corridor square insisted on."""
    if not maze.contains(square):
        raise ValueError("the ghost is at {}, which is off the grid".format(square))
    if not maze.is_corridor(square):
        raise ValueError(
            "the ghost is at {}, which is a wall; a ghost stands on a "
            "corridor square (MAZE-2)".format(square)
        )
    return maze.ways_on_from(square)


def candidate_directions(
    maze: Maze, square: Position, heading: Direction
) -> List[Direction]:
    """The ways on the ghost would choose between, in a repeatable order.

    This is GHOST-3's *"the other ways on"*: every exit except the one it came
    from, which is ``heading.opposite()``.  Straight ahead is not special-cased
    out — :func:`next_ghost_move` only asks for candidates once it knows
    straight ahead is blocked, and a caller inspecting the choice wants to see
    the real set rather than one with a hole in it.

    Empty means the only way on is back the way it came: a dead end, which
    MAZE-5 forbids in a generated maze and ruling C-3 says will therefore
    never be seen in a real game.

    Ordered by ``Direction``'s own declaration order so that the same seed
    always walks the same maze.
    """
    ways = _ways_on(maze, square)
    came_from = heading.opposite()
    return [
        direction
        for direction in Direction
        if direction in ways and direction is not came_from
    ]


def next_ghost_move(
    maze: Maze,
    square: Position,
    heading: Direction,
    random_source: RandomSource,
) -> GhostMove:
    """Where the ghost goes next.  GHOST-2, GHOST-3 and GHOST-4 in one place.

    :param maze: the maze it is walking.
    :param square: the corridor square it is standing on.
    :param heading: the way it is currently going.
    :param random_source: consulted **only** when the ghost cannot carry
        straight on and has more than one way to turn.
    :returns: a :class:`GhostMove` — the direction taken and the square
        reached.
    :raises ValueError: if the ghost is off the grid, on a wall, or on a
        corridor square with no way on at all, none of which is a legal state.

    The player is not a parameter (GHOST-4).

    The order of the three clauses is the requirement's own order and it
    matters: straight ahead wins over a turn even at a junction, and the
    reversal is a last resort rather than one option among several.
    """
    ways = _ways_on(maze, square)
    if not ways:
        raise ValueError(
            "the corridor square {} has no way on at all; MAZE-5 and MAZE-6 "
            "make that impossible in a real maze".format(square)
        )

    # GHOST-2: keep going while the corridor lets it.
    if heading in ways:
        return GhostMove(heading, ways[heading])

    # GHOST-3: otherwise one of the other ways on, at random.
    candidates = candidate_directions(maze, square, heading)
    if candidates:
        chosen = random_source.choice(candidates)
        if chosen not in candidates:
            raise ValueError(
                "the random source returned {}, which was not one of the "
                "choices offered {}".format(chosen, candidates)
            )
        return GhostMove(chosen, ways[chosen])

    # GHOST-3's last clause: back the way it came, and only now.  Unreachable
    # in a generated maze — see ruling C-3 and this module's docstring.
    came_from = heading.opposite()
    return GhostMove(came_from, ways[came_from])
