"""Laying out a maze: a carve on the odd lattice, then a braid on the same one.

A new maze every game (MAZE-4), and a reproducible one whenever a seed is
given, so that any maze a test dislikes can be looked at again.

## The odd lattice, and why everything stays on it

Number the squares from `(0, 0)` at the top-left. Call a square a **cell** when
both its coordinates are odd, and a **connector** when exactly one of them is.
Squares with both coordinates even are never opened, by either pass, and that
single rule is what delivers MAZE-2 and MAZE-3 together:

* **MAZE-2, corridors one square wide.** Take any 2 x 2 block of squares. Of
  its two columns one has an even x, and of its two rows one has an even y, so
  exactly one of the four squares has both coordinates even. That square is
  wall. So no 2 x 2 block can be all corridor, and a corridor can therefore
  never be two squares wide — not by measurement over some number of mazes,
  but by construction, on every maze this module will ever produce.
* **MAZE-3, a solid border.** Cells run from 1 to width - 2 and from 1 to
  height - 2, and a connector always lies between two cells, so nothing at
  `x = 0`, `x = width - 1`, `y = 0` or `y = height - 1` is ever opened. The
  border ring is simply the squares the two passes cannot reach.

This is architecture caution C8, which is about the braid specifically: the
carve naturally stays on the lattice, and it is the braid — which is looking
for *any* wall it can open — that would wander off it and make a 2 x 2 block
if it were not held there. It is held there.

## The two passes

1. **Carve.** A depth-first walk from a random cell, opening the connector to
   each unvisited cell as it is first reached. That visits every cell exactly
   once and opens exactly one connector per cell after the first, so the
   corridors form a spanning tree: everything is connected (MAZE-6) and there
   are no loops. Trees have leaves, so this pass leaves dead ends.
2. **Braid.** Every cell with only one way on gets a second connector opened,
   chosen at random from the walled connectors that lead to another cell.
   Opening a connector only ever adds ways on, so this pass cannot create a
   dead end while removing one, and it cannot disconnect anything it has
   already connected. It stops when no dead end is left (MAZE-5).

A connector between two cells has exactly two neighbouring squares that could
ever be corridor — the two cells it joins, both of which are open the moment
the connector is — so a connector is never a dead end either.
"""

from __future__ import annotations

import random

from terminalgame.domain.maze import (
    CORRIDOR,
    DIRECTIONS,
    HEIGHT,
    WALL,
    WIDTH,
    Maze,
    solid,
)


class MazeTooSmall(ValueError):
    """The grid asked for cannot hold a maze with no dead ends.

    A maze needs odd width and height, and at least two cells in each
    direction, or there is a cell with nowhere to go and MAZE-5 cannot be
    satisfied however the squares are opened.
    """


def generate_maze(seed=None, width=WIDTH, height=HEIGHT):
    """A maze, laid out at random.

    `seed` is an integer — or anything else `random.Random` accepts as a
    seed — and the same seed always gives the same maze. `seed=None` asks for
    a fresh layout, which is MAZE-4: a new maze every time a game starts.

    A caller that already owns a random source passes it to
    `generate_maze_with` instead, so that the whole game can be driven from
    one seed.
    """
    return generate_maze_with(random.Random(seed), width=width, height=height)


def generate_maze_with(random_source, width=WIDTH, height=HEIGHT):
    """A maze laid out using the random source handed in.

    This is the only door randomness comes through (implementation plan §3).
    `random_source` is anything with `randrange` and `shuffle` — a
    `random.Random`, normally.
    """
    cells = _cells_of(width, height)
    grid = solid(width, height)
    _carve(grid, cells, random_source)
    _braid(grid, cells, random_source)
    return Maze(grid)


# -- the lattice ----------------------------------------------------------


def _cells_of(width, height):
    """Every cell of the odd lattice, in reading order.

    Raises rather than returning something that cannot satisfy MAZE-5: an
    even dimension would put the last cell hard against the border and leave
    no room for its ring of wall, and a lattice only one cell wide has cells
    with a single neighbour that no amount of braiding can give a second way
    on.
    """
    if width % 2 == 0 or height % 2 == 0:
        raise MazeTooSmall(
            "a maze needs an odd width and an odd height so that the border "
            "ring closes; got {0} x {1}".format(width, height))
    across = (width - 1) // 2
    down = (height - 1) // 2
    if across < 2 or down < 2:
        raise MazeTooSmall(
            "a maze needs at least two cells in each direction or it has a "
            "dead end nothing can open out; {0} x {1} gives {2} x {3} cells"
            .format(width, height, across, down))
    return [(x, y)
            for y in range(1, height - 1, 2)
            for x in range(1, width - 1, 2)]


def _cell_neighbours(x, y, width, height):
    """The cells two squares away, and the connector square between.

    Yields `(connector_x, connector_y, cell_x, cell_y)` for each of the four
    sides where the far cell is still on the lattice. Both coordinates
    returned are on the lattice or between two of its cells, so a caller that
    only ever opens what this yields can never open an `(even, even)` square.
    """
    for direction in DIRECTIONS:
        cx, cy = x + direction.dx, y + direction.dy
        fx, fy = x + 2 * direction.dx, y + 2 * direction.dy
        if 1 <= fx <= width - 2 and 1 <= fy <= height - 2:
            yield (cx, cy, fx, fy)


# -- pass one: the carve --------------------------------------------------


def _carve(grid, cells, random_source):
    """A depth-first spanning tree over the cells.

    Iterative rather than recursive: 19 x 29 is only 126 cells, but the
    recursion depth of a depth-first carve is the length of its longest path,
    and there is no reason to spend stack on it.
    """
    height = len(grid)
    width = len(grid[0])
    start = cells[random_source.randrange(len(cells))]
    visited = set([start])
    grid[start[1]][start[0]] = CORRIDOR
    stack = [start]
    while stack:
        x, y = stack[-1]
        unvisited = [step for step in _cell_neighbours(x, y, width, height)
                     if (step[2], step[3]) not in visited]
        if not unvisited:
            stack.pop()
            continue
        connector_x, connector_y, cell_x, cell_y = unvisited[
            random_source.randrange(len(unvisited))]
        grid[connector_y][connector_x] = CORRIDOR
        grid[cell_y][cell_x] = CORRIDOR
        visited.add((cell_x, cell_y))
        stack.append((cell_x, cell_y))


# -- pass two: the braid --------------------------------------------------


def _ways_on(grid, x, y):
    """How many of the four adjacent squares are corridor."""
    height = len(grid)
    width = len(grid[0])
    count = 0
    for direction in DIRECTIONS:
        nx, ny = x + direction.dx, y + direction.dy
        if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == CORRIDOR:
            count += 1
    return count


def _braid(grid, cells, random_source):
    """Open out every dead end, staying on the lattice (caution C8).

    Only cells can be dead ends — a connector's two possible ways on are the
    two cells it joins, and both are corridor by the time it is — so walking
    the cells is walking every square that could need opening out.

    This terminates: each step opens a connector that was wall, there are
    finitely many connectors, and opening one never takes a way on away from
    anything.
    """
    height = len(grid)
    width = len(grid[0])
    while True:
        dead_ends = [(x, y) for (x, y) in cells if _ways_on(grid, x, y) < 2]
        if not dead_ends:
            return
        for (x, y) in dead_ends:
            if _ways_on(grid, x, y) >= 2:
                continue  # opened out by an earlier dead end in this pass
            closed = [step for step in _cell_neighbours(x, y, width, height)
                      if grid[step[1]][step[0]] == WALL]
            if not closed:
                # Unreachable while every cell has two lattice neighbours,
                # which `_cells_of` guarantees. Loud rather than looping.
                raise MazeTooSmall(
                    "the square at ({0}, {1}) is a dead end with no wall left "
                    "to open on the lattice".format(x, y))
            connector_x, connector_y, _, _ = closed[
                random_source.randrange(len(closed))]
            grid[connector_y][connector_x] = CORRIDOR
