"""A fresh maze every game, from a random source that is handed in.

MAZE-4 wants a new layout every run.  MAZE-3, MAZE-5 and MAZE-6 want a solid
border, no dead ends and full connectivity, and MAZE-2 wants corridors exactly
one square wide.  The architect's caution C4 calls this the biggest
algorithmic risk in the project, because the obvious generators — recursive
backtracking, Prim — satisfy connectivity and then produce dead ends by the
dozen.

**Two of the four constraints are made impossible rather than repaired.**
Carving happens on a lattice of cells at odd coordinates: cell ``(i, j)`` is
the square ``Position(2i + 1, 2j + 1)``, and two adjacent cells are joined by
opening the single square between them.  That gives 9 cells across and 14 deep
inside a 19 x 29 grid, since ``19 = 2*9 + 1`` and ``29 = 2*14 + 1``.

From that one choice:

* **MAZE-2 holds by parity.**  Any 2 x 2 block of squares contains one whose
  column and row are both even.  Cells are odd-odd and connectors have exactly
  one even coordinate, so a both-even square is never carved — and a corridor
  two squares wide is not merely unlikely, it cannot be represented.
* **MAZE-3 holds by parity.**  Cells lie at columns 1..17 and rows 1..27.  A
  connector lies strictly between two cells, so at columns 2..16 and rows
  2..26.  Nothing the generator carves can reach column 0 or 18 or row 0 or 28.

That the original maze was built this way is not a guess.  Decoding all 29
rows of the specimen picture in the requirements gives **zero corridor squares
with both coordinates even** — see ``docs/findings/WI-2-odd-cell-lattice.md``.

The remaining two constraints are handled in sequence:

* **MAZE-6** comes from a randomised depth-first carve, which spans every cell
  by construction.
* **MAZE-5** comes from a repair pass afterwards.  A spanning tree is all dead
  ends; the repair gives every cell a second way on by opening one more wall.
  **Adding an edge can only raise degrees, so the repair never creates the
  fault it is removing and never disconnects anything** — which is why this
  converges in one pass and needs no retry loop.  That is the part of caution
  C4 that turned out not to bite, and it is worth knowing why.

Nothing here is impure.  There is no module-level random source: MAZE-4's
randomness **arrives as an argument**, described by :class:`RandomSource`, so
this whole module is testable with no clock and no window.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterable, List, NamedTuple, Protocol, Sequence, Set, Tuple

from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.domain.structure import MINIMUM_WAYS_ON, StructureReport, check

#: Cells across.  ``WIDTH == 2 * CELL_COLUMNS + 1``.
CELL_COLUMNS = (WIDTH - 1) // 2

#: Cells deep.  ``HEIGHT == 2 * CELL_ROWS + 1``.
CELL_ROWS = (HEIGHT - 1) // 2


class RandomSource(Protocol):
    """The whole of what the generator needs from a source of randomness.

    One method, deliberately.  ``random.Random`` satisfies it, and so does any
    test double, but nothing here imports ``random`` — the domain may not name
    a module-level random source, and a generator that reached for one could
    not be replayed.

    Shuffling is done from ``randrange`` rather than taken from the source, so
    that a maze depends only on the sequence of integers it was given and not
    on the shuffling algorithm of whatever library supplied them.
    """

    def randrange(self, stop: int) -> int:
        """An integer in ``range(stop)``."""
        ...


class Cell(NamedTuple):
    """A place on the carving lattice, not a square on the grid.

    Kept distinct from :class:`~terminal_game.domain.maze.Position` on purpose:
    confusing lattice coordinates with grid coordinates is the mistake this
    whole module is arranged to make impossible to write by accident.
    """

    column: int
    row: int


#: Two cells joined by an opened wall, held in a fixed order so that the same
#: join is the same value however it was discovered.
Edge = Tuple[Cell, Cell]


class GenerationFailed(Exception):
    """A maze was built that does not satisfy MAZE-3, MAZE-5 and MAZE-6.

    Raised by :func:`verified` rather than returned, because a maze that fails
    its own structural check must never reach a player: an unreachable dot
    makes the game unwinnable and a pocket traps them.
    """


# --------------------------------------------------------------------------
# The lattice, and how it maps onto the grid
# --------------------------------------------------------------------------


def all_cells() -> Tuple[Cell, ...]:
    """Every cell, in reading order."""
    return tuple(
        Cell(column, row)
        for row in range(CELL_ROWS)
        for column in range(CELL_COLUMNS)
    )


def cell_position(cell: Cell) -> Position:
    """The grid square a cell occupies: odd column, odd row."""
    return Position(2 * cell.column + 1, 2 * cell.row + 1)


def cell_neighbours(cell: Cell) -> Tuple[Cell, ...]:
    """The cells orthogonally adjacent on the lattice, in reading order.

    Two for a corner cell, three along an edge, four inside — which is why
    every cell can always be given the two ways on that MAZE-5 asks for.
    """
    candidates = (
        Cell(cell.column, cell.row - 1),
        Cell(cell.column - 1, cell.row),
        Cell(cell.column + 1, cell.row),
        Cell(cell.column, cell.row + 1),
    )
    return tuple(
        other
        for other in candidates
        if 0 <= other.column < CELL_COLUMNS and 0 <= other.row < CELL_ROWS
    )


def edge_between(one: Cell, other: Cell) -> Edge:
    """The join between two adjacent cells, in a fixed order."""
    return (one, other) if one <= other else (other, one)


def connector_position(edge: Edge) -> Position:
    """The single grid square opened by an edge — the wall between two cells."""
    one, other = edge
    return Position(one.column + other.column + 1, one.row + other.row + 1)


# --------------------------------------------------------------------------
# Randomness, used through one method so a maze is replayable
# --------------------------------------------------------------------------


def _shuffled(items: Sequence, rng: RandomSource) -> List:
    """A new list holding ``items`` in a random order (Fisher-Yates)."""
    shuffled = list(items)
    for index in range(len(shuffled) - 1, 0, -1):
        swap = rng.randrange(index + 1)
        shuffled[index], shuffled[swap] = shuffled[swap], shuffled[index]
    return shuffled


def _one_of(items: Sequence, rng: RandomSource):
    return items[rng.randrange(len(items))]


# --------------------------------------------------------------------------
# Carving
# --------------------------------------------------------------------------


def spanning_tree(rng: RandomSource) -> FrozenSet[Edge]:
    """A randomised depth-first carve joining every cell to every other.

    Every cell is reached, so MAZE-6 holds of the result and of anything built
    from it by adding more edges.  It is a tree, so it is also nothing but
    dead ends — which :func:`without_dead_ends` then fixes.

    The stack is explicit rather than recursive: 126 cells would not trouble
    the recursion limit, but a carve that cannot overflow is one less thing
    for anyone to wonder about.
    """
    cells = all_cells()
    start = _one_of(cells, rng)
    visited = {start}  # type: Set[Cell]
    stack = [start]  # type: List[Cell]
    edges = set()  # type: Set[Edge]

    while stack:
        current = stack[-1]
        unvisited = [
            neighbour
            for neighbour in cell_neighbours(current)
            if neighbour not in visited
        ]
        if not unvisited:
            stack.pop()
            continue
        chosen = _one_of(unvisited, rng)
        edges.add(edge_between(current, chosen))
        visited.add(chosen)
        stack.append(chosen)

    return frozenset(edges)


def degrees(edges: Iterable[Edge]) -> Dict[Cell, int]:
    """How many ways on each cell has.  Cells with none are absent."""
    counted = {}  # type: Dict[Cell, int]
    for one, other in edges:
        counted[one] = counted.get(one, 0) + 1
        counted[other] = counted.get(other, 0) + 1
    return counted


def without_dead_ends(edges: FrozenSet[Edge], rng: RandomSource) -> FrozenSet[Edge]:
    """Give every cell at least two ways on, by opening further walls.

    MAZE-5 says *"from any corridor square there are always at least two ways
    on"*, and a spanning tree gives most cells exactly one.  Each shortfall is
    made up by joining the cell to neighbours it is not already joined to.

    **This converges in a single pass and cannot undo itself.**  Adding an edge
    only ever raises two degrees, so it never creates a dead end while removing
    one, and it never disconnects anything it has already joined.  Every cell
    has at least two lattice neighbours, so a cell short of ways on always has
    a spare one to use.  Caution C4 expected a repair loop that might not
    settle; on this lattice there is nothing for it to fight with.
    """
    opened = set(edges)
    degree = degrees(opened)

    for cell in _shuffled(all_cells(), rng):
        shortfall = MINIMUM_WAYS_ON - degree.get(cell, 0)
        if shortfall <= 0:
            continue
        spare = _shuffled(
            [
                neighbour
                for neighbour in cell_neighbours(cell)
                if edge_between(cell, neighbour) not in opened
            ],
            rng,
        )
        for neighbour in spare[:shortfall]:
            opened.add(edge_between(cell, neighbour))
            degree[cell] = degree.get(cell, 0) + 1
            degree[neighbour] = degree.get(neighbour, 0) + 1

    return frozenset(opened)


def maze_from_edges(edges: Iterable[Edge]) -> Maze:
    """Turn a set of lattice edges into a maze.

    Every cell is carved whether or not it has edges, so that a cell can never
    be silently dropped; the edges add the squares between them.
    """
    carved = [cell_position(cell) for cell in all_cells()]
    carved.extend(connector_position(edge) for edge in edges)
    return Maze.all_walls().with_corridors_at(carved)


# --------------------------------------------------------------------------
# The gate, and the whole thing
# --------------------------------------------------------------------------


def verified(maze: Maze) -> Maze:
    """Return ``maze`` if it is structurally sound, or refuse to hand it out.

    The plan asks for connectivity to be verified *before* a maze is handed
    out, and this is that gate.  It asks WI-1's checker, which is the same
    oracle the tests use, so the generator cannot be sound by its own
    definition and broken by everyone else's.
    """
    report = check(maze)  # type: StructureReport
    if not report.is_sound:
        raise GenerationFailed(
            "generated maze is not fit to play: {}".format(report.describe())
        )
    return maze


def generate(rng: RandomSource) -> Maze:
    """A fresh maze, laid out at random, fit to play.

    MAZE-4: two runs with different numbers out of ``rng`` give different
    mazes, and two runs with the same numbers give the same maze.
    """
    return verified(maze_from_edges(without_dead_ends(spanning_tree(rng), rng)))
