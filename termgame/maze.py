"""Maze generation and the text-grid loader — MAZE-1..6.

The maze is a 29 x 19 grid of cells laid over a **9 x 14 node lattice**:

* cell ``(odd, odd)`` is a **node** — 9 x 14 = 126 of them, always corridor;
* cell ``(even, even)`` is a **pillar** — always wall;
* the cell between two adjacent nodes is a **link** — corridor exactly when
  the lattice edge between those nodes is open.

That decomposition is what makes the requirements tractable, because each of
them collapses into a property of the lattice graph:

======  ====================================================================
MAZE-1  19 across x 29 deep — fixed by the lattice being 9 x 14
MAZE-2  corridors one square wide, orthogonal — true by construction: links
        are single cells, and every 2 x 2 block of cells contains exactly
        one ``(even, even)`` pillar, so no 2 x 2 block is all corridor
MAZE-3  solid border — true by construction: row 0, row 28, column 0 and
        column 18 are all even-indexed on at least one axis in a way that
        makes them pillars or links with no node on one side
MAZE-4  a new maze every game — ``generate`` is driven entirely by the
        ``random.Random`` handed to it
MAZE-5  no dead ends — a link cell always has exactly two corridor
        neighbours, so nodes are the only risk; the braid pass guarantees
        every node has lattice degree >= 2
MAZE-6  all corridors reachable — the depth-first search yields a spanning
        tree, and adding edges cannot disconnect anything
======  ====================================================================

The algorithm is a **braided randomised depth-first search**:

1. randomised DFS over the lattice, giving a spanning tree (MAZE-6);
2. a braid pass that gives every degree-1 node one more edge, to a
   uniformly-chosen lattice neighbour it is not already joined to (MAZE-5);
3. paint the lattice onto the 29 x 19 cell grid.

``generate`` takes a ``random.Random`` as a parameter and makes no
module-level ``random`` call, so every maze is reproducible from a seed.
"""

import random
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from termgame.model import MAZE_COLS, MAZE_ROWS, Maze, Position

#: The node lattice is 14 nodes deep and 9 across — cells (1,1) to (27,17).
NODE_ROWS = (MAZE_ROWS - 1) // 2  # 14
NODE_COLS = (MAZE_COLS - 1) // 2  # 9

#: How the loader reads a hand-written board.
CORRIDOR_CHARS = frozenset(". ")
WALL_CHARS = frozenset("#")

Node = Tuple[int, int]
Edge = Tuple[Node, Node]

# The four lattice steps, in a fixed order. Randomness is applied by
# shuffling a copy of this, never by iterating a set, so a seeded run is
# reproducible.
_STEPS: Tuple[Tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


def node_cell(node: Node) -> Position:
    """The cell a lattice node occupies."""
    return Position(2 * node[0] + 1, 2 * node[1] + 1)


def link_cell(a: Node, b: Node) -> Position:
    """The cell lying between two adjacent lattice nodes."""
    if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
        raise ValueError("%r and %r are not adjacent nodes" % (a, b))
    return Position(a[0] + b[0] + 1, a[1] + b[1] + 1)


def _lattice_neighbours(node: Node) -> Tuple[Node, ...]:
    row, col = node
    found = []
    for dr, dc in _STEPS:
        nr, nc = row + dr, col + dc
        if 0 <= nr < NODE_ROWS and 0 <= nc < NODE_COLS:
            found.append((nr, nc))
    return tuple(found)


def _edge(a: Node, b: Node) -> Edge:
    return (a, b) if a <= b else (b, a)


def _spanning_tree(rng: random.Random) -> Set[Edge]:
    """A randomised depth-first spanning tree of the whole lattice."""
    start = (rng.randrange(NODE_ROWS), rng.randrange(NODE_COLS))
    visited = {start}
    edges: Set[Edge] = set()
    stack: List[Node] = [start]
    while stack:
        node = stack[-1]
        unvisited = [n for n in _lattice_neighbours(node) if n not in visited]
        if not unvisited:
            stack.pop()
            continue
        nxt = unvisited[rng.randrange(len(unvisited))]
        edges.add(_edge(node, nxt))
        visited.add(nxt)
        stack.append(nxt)
    return edges


def _braid(edges: Set[Edge], rng: random.Random) -> None:
    """Give every degree-1 node one more edge, in place — MAZE-5.

    A lattice leaf always has a spare neighbour: the poorest node, a corner,
    has two lattice neighbours and a tree leaf uses only one. So this never
    fails. Adding edges cannot disconnect anything, so MAZE-6 survives.
    """
    degree: Dict[Node, int] = {
        (r, c): 0 for r in range(NODE_ROWS) for c in range(NODE_COLS)
    }
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1

    for row in range(NODE_ROWS):
        for col in range(NODE_COLS):
            node = (row, col)
            if degree[node] >= 2:
                continue
            spare = [
                n for n in _lattice_neighbours(node) if _edge(node, n) not in edges
            ]
            if not spare:
                raise AssertionError(
                    "node %r has degree %d and no spare neighbour"
                    % (node, degree[node])
                )
            other = spare[rng.randrange(len(spare))]
            edges.add(_edge(node, other))
            degree[node] += 1
            degree[other] += 1


def _paint(edges: Iterable[Edge]) -> Maze:
    """Paint the lattice onto the 29 x 19 cell grid."""
    grid = [[False] * MAZE_COLS for _ in range(MAZE_ROWS)]
    for row in range(NODE_ROWS):
        for col in range(NODE_COLS):
            cell = node_cell((row, col))
            grid[cell.row][cell.col] = True
    for a, b in edges:
        cell = link_cell(a, b)
        grid[cell.row][cell.col] = True
    return Maze(tuple(tuple(row) for row in grid))


def generate(rng: random.Random) -> Maze:
    """A new 29 x 19 maze satisfying MAZE-1..6, driven by ``rng``.

    The same seeded ``random.Random`` always yields the identical maze, which
    is what makes every other test in this project reproducible.
    """
    edges = _spanning_tree(rng)
    _braid(edges, rng)
    return _paint(edges)


def from_text(text: str) -> Maze:
    """A maze read from a hand-written text grid.

    ``'.'`` and ``' '`` are corridor, ``'#'`` is wall. Blank lines at the
    start and end are ignored; every remaining line must be the same length.

    It reads a **string, not a file** — the caller does any file reading, so
    the core touches no filesystem.
    """
    lines = text.split("\n")
    # Only wholly empty lines are stripped: a line of spaces is a legal
    # all-corridor row and must survive.
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        raise ValueError("no maze in the text")
    width = len(lines[0])
    grid: List[Tuple[bool, ...]] = []
    for index, line in enumerate(lines):
        if len(line) != width:
            raise ValueError(
                "row %d is %d characters wide, expected %d"
                % (index, len(line), width)
            )
        row: List[bool] = []
        for ch in line:
            if ch in CORRIDOR_CHARS:
                row.append(True)
            elif ch in WALL_CHARS:
                row.append(False)
            else:
                raise ValueError("%r is neither corridor nor wall" % (ch,))
        grid.append(tuple(row))
    return Maze(tuple(grid))


def to_text(maze: Maze) -> str:
    """A maze written back out in the form :func:`from_text` reads."""
    return "\n".join(maze.rows())


# --------------------------------------------------------------------------
# Invariant checks — the same properties the tests assert, available to any
# later work item that wants to lean on them.
# --------------------------------------------------------------------------


def has_solid_border(maze: Maze) -> bool:
    """MAZE-3 — nothing can leave the maze."""
    last_row = maze.height - 1
    last_col = maze.width - 1
    for col in range(maze.width):
        if maze.is_corridor((0, col)) or maze.is_corridor((last_row, col)):
            return False
    for row in range(maze.height):
        if maze.is_corridor((row, 0)) or maze.is_corridor((row, last_col)):
            return False
    return True


def dead_ends(maze: Maze) -> Tuple[Position, ...]:
    """MAZE-5 — the corridor cells with fewer than two ways on."""
    return tuple(
        sorted(cell for cell in maze.corridors() if maze.corridor_degree(cell) < 2)
    )


def open_blocks(maze: Maze) -> Tuple[Position, ...]:
    """MAZE-2 — the top-left cells of any 2 x 2 block that is all corridor."""
    found = []
    for row in range(maze.height - 1):
        for col in range(maze.width - 1):
            if all(
                maze.is_corridor(p)
                for p in (
                    (row, col),
                    (row, col + 1),
                    (row + 1, col),
                    (row + 1, col + 1),
                )
            ):
                found.append(Position(row, col))
    return tuple(found)


def reachable_from(maze: Maze, start: Position) -> Set[Position]:
    """Every corridor cell that can be walked to from ``start``."""
    if not maze.is_corridor(start):
        return set()
    seen = {Position(*start)}
    stack: List[Position] = [Position(*start)]
    while stack:
        here = stack.pop()
        for nxt in maze.open_neighbours(here):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def is_fully_connected(maze: Maze) -> bool:
    """MAZE-6 — every corridor cell is reachable from every other one."""
    corridors = maze.corridors()
    if not corridors:
        return True
    start = min(corridors)
    return reachable_from(maze, start) == set(corridors)


def check(maze: Maze) -> Sequence[str]:
    """Every MAZE requirement this maze fails, as readable strings.

    Empty means the maze is legal.
    """
    problems: List[str] = []
    if (maze.height, maze.width) != (MAZE_ROWS, MAZE_COLS):
        problems.append(
            "MAZE-1: maze is %d x %d, expected %d x %d"
            % (maze.height, maze.width, MAZE_ROWS, MAZE_COLS)
        )
    blocks = open_blocks(maze)
    if blocks:
        problems.append("MAZE-2: 2x2 corridor block(s) at %s" % (blocks[:5],))
    if not has_solid_border(maze):
        problems.append("MAZE-3: the border is not solid wall")
    ends = dead_ends(maze)
    if ends:
        problems.append("MAZE-5: dead end(s) at %s" % (ends[:5],))
    if not is_fully_connected(maze):
        problems.append("MAZE-6: not every corridor cell is reachable")
    return tuple(problems)
