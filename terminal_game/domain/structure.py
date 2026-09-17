"""Three questions about the shape of a maze, answered independently.

This is WI-2's oracle.  WI-2 carves a maze at random and then has to know
whether what it carved is sound before it hands it out, and "sound" is three
separate properties from three separate requirements:

* **MAZE-3** — is the border ring solid, so nothing can leave the maze?
* **MAZE-5** — has any corridor square fewer than two ways on, so the player
  could be trapped in a pocket?
* **MAZE-6** — can every corridor square be walked to from every other, so no
  dot is unreachable?

**The three answers are independent and each is computed without reference to
the others.**  That matters more than it looks.  A carve-then-repair loop
opens a wall to remove a dead end and thereby changes connectivity; a
generator that only ever heard "sound" or "not sound" would have no way to
tell whether its last repair helped.  So each question returns *which squares*
fail it, not merely whether any do.

The checker is deliberately ignorant of how a maze was made.  It reads a
:class:`~terminal_game.domain.maze.Maze` and says what is true of it, which is
why it can be trusted about a maze WI-2 produced and about a maze a test drew
by hand.
"""

from __future__ import annotations

from typing import List, NamedTuple, Set, Tuple

from terminal_game.domain.maze import Maze, Position, Square

#: MAZE-5.  A corridor square with fewer ways on than this is a dead end.
#: *"From any corridor square there are always at least two ways on."*
MINIMUM_WAYS_ON = 2


def border_breaches(maze: Maze) -> Tuple[Position, ...]:
    """MAZE-3: the border squares that are not wall, in reading order.

    Empty means the wall runs right around the outside and nothing can leave
    the maze.  Naming the squares rather than returning a flag is what lets a
    generator fill exactly those back in.
    """
    return tuple(p for p in maze.border() if maze.square_at(p) is Square.CORRIDOR)


def dead_ends(maze: Maze) -> Tuple[Position, ...]:
    """MAZE-5: the corridor squares with fewer than two ways on, in reading order.

    Empty means the player is never trapped in a pocket.  A lone corridor
    square with no neighbours at all counts here, with zero ways on — it is
    the most dead of dead ends, and a checker that only looked for *exactly*
    one would miss it.
    """
    return tuple(
        p
        for p in maze.corridors()
        if len(maze.corridor_neighbours(p)) < MINIMUM_WAYS_ON
    )


def unreachable_corridors(maze: Maze) -> Tuple[Position, ...]:
    """MAZE-6: the corridor squares cut off from the rest, in reading order.

    Reachability is walked, not measured: two squares are connected when there
    is a path between them through orthogonally adjacent corridor squares.
    The search starts from the first corridor square in reading order, so the
    answer is the same every run and a failure names the same squares twice.

    A maze with no corridors at all, and a maze with exactly one, are both
    fully connected — vacuously, but truthfully.  Whether either is a *good*
    maze is MAZE-5's question and this one does not borrow its answer.
    """
    corridors = maze.corridors()
    if not corridors:
        return ()

    start = corridors[0]
    seen = {start}  # type: Set[Position]
    frontier = [start]  # type: List[Position]
    while frontier:
        position = frontier.pop()
        for neighbour in maze.corridor_neighbours(position):
            if neighbour not in seen:
                seen.add(neighbour)
                frontier.append(neighbour)

    return tuple(p for p in corridors if p not in seen)


class StructureReport(NamedTuple):
    """What is wrong with a maze's shape, one field per question.

    Each field lists the squares that fail its own requirement.  All three
    empty is a sound maze; anything else says precisely where to look.
    """

    breaches: Tuple[Position, ...]
    pockets: Tuple[Position, ...]
    islands: Tuple[Position, ...]

    @property
    def border_is_solid(self) -> bool:
        """MAZE-3 holds."""
        return not self.breaches

    @property
    def has_no_dead_ends(self) -> bool:
        """MAZE-5 holds."""
        return not self.pockets

    @property
    def is_fully_connected(self) -> bool:
        """MAZE-6 holds."""
        return not self.islands

    @property
    def is_sound(self) -> bool:
        """All three hold, and the maze may be handed out."""
        return self.border_is_solid and self.has_no_dead_ends and self.is_fully_connected

    def describe(self) -> str:
        """A sentence per failing requirement, for a failure somebody has to read.

        A generator that gives up after too many attempts, and a test that
        rejects a hand-built maze, both end with somebody looking at this
        string and needing to know which of the three went wrong.
        """
        if self.is_sound:
            return "sound: border solid, no dead ends, fully connected"
        lines = []  # type: List[str]
        if self.breaches:
            lines.append(
                "MAZE-3 border is breached at {}".format(_squares(self.breaches))
            )
        if self.pockets:
            lines.append(
                "MAZE-5 dead ends (fewer than {} ways on) at {}".format(
                    MINIMUM_WAYS_ON, _squares(self.pockets)
                )
            )
        if self.islands:
            lines.append(
                "MAZE-6 corridor squares cut off from the rest at {}".format(
                    _squares(self.islands)
                )
            )
        return "; ".join(lines)


def _squares(positions: Tuple[Position, ...], limit: int = 8) -> str:
    shown = ", ".join(str(p) for p in positions[:limit])
    if len(positions) > limit:
        shown += " and {} more".format(len(positions) - limit)
    return "{} square(s): {}".format(len(positions), shown)


def check(maze: Maze) -> StructureReport:
    """Answer all three questions about ``maze``.

    The whole oracle in one call, for a generator that wants to know whether
    it is finished.  A generator that wants to know what to *fix* asks the
    three functions above, or reads the three fields.
    """
    return StructureReport(
        breaches=border_breaches(maze),
        pockets=dead_ends(maze),
        islands=unreachable_corridors(maze),
    )
