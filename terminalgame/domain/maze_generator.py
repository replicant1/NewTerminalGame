"""Laying out a maze at random: carve, then repair, then verify.

Domain layer. The generator creates no randomness of its own — it is *handed* a
random source (anything with ``random.Random``'s ``shuffle`` and ``choice``)
and every decision it makes comes from there. Hand it two identically seeded
sources and you get two identical mazes; that is MAZE-4 and it is what makes
the whole system reproducible in a test.

The shape of the grid
---------------------
MAZE-1 asks for 19 squares across and 29 deep. Both are odd, and

    19 = 2 * 9 + 1        29 = 2 * 14 + 1

so the grid is exactly a 9 x 14 arrangement of **cells** at odd coordinates,
separated by the squares between them. Cell ``(i, j)`` lives at square
``(2i + 1, 2j + 1)``; the square halfway between two adjacent cells is the
**connector** that is carved out when those two cells are joined.

Three of the requirements then fall out of the arithmetic rather than needing
to be policed:

* every square with two even coordinates is never carved, so no two-by-two
  block of corridor can exist and corridors are one square wide (MAZE-2);
* the outer ring is entirely even coordinates in at least one axis that is
  never carved, so the border stays solid (MAZE-3);
* every cell square is corridor, so two diagonally touching corridor squares
  always have a corridor square orthogonally between them and no corridor ever
  runs diagonally (MAZE-2 again).

What is left is the part caution C4 warns about, and it is done in three
stages:

1. **Carve** a spanning tree over the cells with a randomised depth-first
   walk. Every cell is reachable from every other, so MAZE-6 holds — but a
   spanning tree is nothing but dead ends, so MAZE-5 does not.
2. **Repair** by braiding: every cell with only one way on gets a second wall
   opened to a randomly chosen neighbour it is not already joined to. Opening
   a wall only ever adds a way through, so the connectivity won in stage 1
   cannot be lost in stage 2.
3. **Verify** the finished grid against every structural requirement and
   refuse to hand out a maze that fails, rather than discovering it later.
"""

from __future__ import annotations

import random
from typing import Dict, List, Set, Tuple

from .maze import DIRECTIONS, Maze, SquareKind
from .maze_invariants import structural_faults

__all__ = [
    "MAZE_WIDTH",
    "MAZE_HEIGHT",
    "CELL_COLUMNS",
    "CELL_ROWS",
    "MazeGenerationError",
    "generate_maze",
]

#: MAZE-1: the grid is 19 squares across and 29 deep.
MAZE_WIDTH = 19
MAZE_HEIGHT = 29

#: The cells those dimensions imply, at the odd coordinates.
CELL_COLUMNS = (MAZE_WIDTH - 1) // 2
CELL_ROWS = (MAZE_HEIGHT - 1) // 2


class MazeGenerationError(RuntimeError):
    """Raised when a generated maze fails a structural requirement.

    Nothing should ever see this. It exists so that a maze which breaks
    MAZE-2, MAZE-3, MAZE-5 or MAZE-6 is never handed to the rest of the
    system, which would otherwise carry the fault silently into the picture.
    """


def generate_maze(
    random_source: random.Random,
    width: int = MAZE_WIDTH,
    height: int = MAZE_HEIGHT,
) -> Maze:
    """Lay out a fresh maze using the random source it is handed.

    ``width`` and ``height`` default to the 19 x 29 of MAZE-1 and are
    parameters only so that the algorithm can be exercised at other sizes.
    Both must be odd and at least 5, which is the smallest grid with room for
    two cells in each direction and therefore the smallest that can have no
    dead ends.
    """
    _require_workable_dimensions(width, height)

    cell_columns = (width - 1) // 2
    cell_rows = (height - 1) // 2

    links = _carve_spanning_tree(random_source, cell_columns, cell_rows)
    _braid_away_dead_ends(random_source, cell_columns, cell_rows, links)
    maze = _grid_from_links(width, height, cell_columns, cell_rows, links)

    faults = structural_faults(maze)
    if faults:
        raise MazeGenerationError(
            "the generated maze is not fit to hand out:\n  " + "\n  ".join(faults)
        )
    return maze


# ----------------------------------------------------------------------
# Stage 1 — carve
# ----------------------------------------------------------------------


def _carve_spanning_tree(
    random_source: random.Random, cell_columns: int, cell_rows: int
) -> Dict[Tuple[int, int], Set[Tuple[int, int]]]:
    """A randomised depth-first walk joining every cell to every other."""
    links: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {
        (column, row): set()
        for row in range(cell_rows)
        for column in range(cell_columns)
    }
    start = (
        random_source.randrange(cell_columns),
        random_source.randrange(cell_rows),
    )
    visited: Set[Tuple[int, int]] = {start}
    stack: List[Tuple[int, int]] = [start]
    while stack:
        cell = stack[-1]
        unvisited = [
            neighbour
            for neighbour in _cell_neighbours(cell, cell_columns, cell_rows)
            if neighbour not in visited
        ]
        if not unvisited:
            stack.pop()
            continue
        chosen = random_source.choice(unvisited)
        links[cell].add(chosen)
        links[chosen].add(cell)
        visited.add(chosen)
        stack.append(chosen)
    return links


# ----------------------------------------------------------------------
# Stage 2 — repair
# ----------------------------------------------------------------------


def _braid_away_dead_ends(
    random_source: random.Random,
    cell_columns: int,
    cell_rows: int,
    links: Dict[Tuple[int, int], Set[Tuple[int, int]]],
) -> None:
    """Open a second way on at every cell that has only one.

    Cells are visited in a fixed order so that the result depends only on the
    random source. A cell reached with one way on is given a second, chosen
    uniformly among the neighbours it is not already joined to; because every
    cell in a grid at least two cells wide and two deep has at least two
    neighbours, a cell with one link always has at least one to choose from.
    Joining also gives the other cell a way on, so the pass never has to
    revisit anything.
    """
    for row in range(cell_rows):
        for column in range(cell_columns):
            cell = (column, row)
            if len(links[cell]) >= 2:
                continue
            candidates = [
                neighbour
                for neighbour in _cell_neighbours(cell, cell_columns, cell_rows)
                if neighbour not in links[cell]
            ]
            if not candidates:
                # Unreachable on any grid this generator accepts; the guard is
                # here so that a future caller passing a degenerate size gets a
                # named failure rather than an IndexError.
                raise MazeGenerationError(
                    "cell %r has one way on and no wall left to open" % (cell,)
                )
            chosen = random_source.choice(candidates)
            links[cell].add(chosen)
            links[chosen].add(cell)


# ----------------------------------------------------------------------
# Stage 3 — the grid itself
# ----------------------------------------------------------------------


def _grid_from_links(
    width: int,
    height: int,
    cell_columns: int,
    cell_rows: int,
    links: Dict[Tuple[int, int], Set[Tuple[int, int]]],
) -> Maze:
    rows = [[SquareKind.WALL for _ in range(width)] for _ in range(height)]
    for row in range(cell_rows):
        for column in range(cell_columns):
            square_column = 2 * column + 1
            square_row = 2 * row + 1
            rows[square_row][square_column] = SquareKind.CORRIDOR
            for other_column, other_row in links[(column, row)]:
                connector_column = square_column + (other_column - column)
                connector_row = square_row + (other_row - row)
                rows[connector_row][connector_column] = SquareKind.CORRIDOR
    return Maze(rows)


# ----------------------------------------------------------------------


def _cell_neighbours(
    cell: Tuple[int, int], cell_columns: int, cell_rows: int
) -> List[Tuple[int, int]]:
    column, row = cell
    neighbours: List[Tuple[int, int]] = []
    for direction in DIRECTIONS:
        next_column = column + direction.column_step
        next_row = row + direction.row_step
        if 0 <= next_column < cell_columns and 0 <= next_row < cell_rows:
            neighbours.append((next_column, next_row))
    return neighbours


def _require_workable_dimensions(width: int, height: int) -> None:
    for name, value in (("width", width), ("height", height)):
        if value % 2 == 0:
            raise ValueError(
                "%s must be odd so the grid divides into cells and walls, got %d"
                % (name, value)
            )
        if value < 5:
            raise ValueError(
                "%s must be at least 5 for a maze with no dead ends, got %d"
                % (name, value)
            )
