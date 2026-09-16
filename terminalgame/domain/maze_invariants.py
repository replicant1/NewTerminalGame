"""The structural properties a maze must have, as questions anyone may ask.

These are the requirements MAZE-2, MAZE-3, MAZE-5 and MAZE-6 written down as
predicates over a finished grid. The generator runs them before it hands a maze
out (the architect's caution C4: verify, then hand out), and they are testable
on their own against hand-built mazes with known faults.

Each check returns *the squares at fault*, not a bare boolean, so a failure
says where the problem is.
"""

from __future__ import annotations

from typing import List, Set, Tuple

from .maze import Maze, Square

__all__ = [
    "holes_in_border",
    "dead_end_squares",
    "unreachable_corridor_squares",
    "two_wide_corridor_squares",
    "diagonal_only_corridor_pairs",
    "structural_faults",
]


def holes_in_border(maze: Maze) -> Tuple[Square, ...]:
    """MAZE-3: every square of the outside ring must be wall.

    Returns the border squares that are corridor, in row-major order.
    """
    holes: List[Square] = []
    last_column = maze.width - 1
    last_row = maze.height - 1
    for square in maze.squares():
        on_border = (
            square.column == 0
            or square.row == 0
            or square.column == last_column
            or square.row == last_row
        )
        if on_border and maze.is_corridor(square):
            holes.append(square)
    return tuple(holes)


def dead_end_squares(maze: Maze) -> Tuple[Square, ...]:
    """MAZE-5: every corridor square must have at least two corridor neighbours.

    Returns the corridor squares with fewer than two, which includes a wholly
    isolated corridor square with none.
    """
    return tuple(
        square
        for square in maze.corridor_squares()
        if len(maze.corridor_neighbours(square)) < 2
    )


def unreachable_corridor_squares(maze: Maze) -> Tuple[Square, ...]:
    """MAZE-6: every corridor square must be walkable to from every other.

    Flood fills from the first corridor square and returns the corridor squares
    the fill never reached. An empty maze of corridors is vacuously connected.
    """
    corridors = maze.corridor_squares()
    if not corridors:
        return ()
    start = corridors[0]
    reached: Set[Square] = {start}
    frontier = [start]
    while frontier:
        square = frontier.pop()
        for neighbour in maze.corridor_neighbours(square):
            if neighbour not in reached:
                reached.add(neighbour)
                frontier.append(neighbour)
    return tuple(square for square in corridors if square not in reached)


def two_wide_corridor_squares(maze: Maze) -> Tuple[Square, ...]:
    """MAZE-2: corridors are one square wide.

    Returns the top-left square of every two-by-two block that is corridor all
    the way through, which is the only way a corridor can be two squares wide
    on an axis-aligned grid.
    """
    offending: List[Square] = []
    for row in range(maze.height - 1):
        for column in range(maze.width - 1):
            block = (
                Square(column, row),
                Square(column + 1, row),
                Square(column, row + 1),
                Square(column + 1, row + 1),
            )
            if all(maze.is_corridor(square) for square in block):
                offending.append(block[0])
    return tuple(offending)


def diagonal_only_corridor_pairs(maze: Maze) -> Tuple[Tuple[Square, Square], ...]:
    """MAZE-2: corridors run only north-south and east-west.

    A corridor that "runs diagonally" is two corridor squares touching only at
    a corner, with both squares that would join them orthogonally being wall:
    walking the corridor cannot get you from one to the other in a straight
    line, yet the picture reads as a diagonal. Returns each such pair once,
    upper square first.
    """
    offending: List[Tuple[Square, Square]] = []
    for row in range(maze.height - 1):
        for column in range(maze.width - 1):
            top_left = Square(column, row)
            top_right = Square(column + 1, row)
            bottom_left = Square(column, row + 1)
            bottom_right = Square(column + 1, row + 1)
            if (
                maze.is_corridor(top_left)
                and maze.is_corridor(bottom_right)
                and maze.is_wall(top_right)
                and maze.is_wall(bottom_left)
            ):
                offending.append((top_left, bottom_right))
            if (
                maze.is_corridor(top_right)
                and maze.is_corridor(bottom_left)
                and maze.is_wall(top_left)
                and maze.is_wall(bottom_right)
            ):
                offending.append((top_right, bottom_left))
    return tuple(offending)


def structural_faults(maze: Maze) -> Tuple[str, ...]:
    """Every way this maze breaks the structural requirements, one line each.

    An empty result means the maze satisfies MAZE-2, MAZE-3, MAZE-5 and MAZE-6.
    The lines are for a developer reading a failure, not for the player.
    """
    faults: List[str] = []

    holes = holes_in_border(maze)
    if holes:
        faults.append(
            "MAZE-3: the border ring is not solid at %s" % (_squares_as_text(holes),)
        )

    dead_ends = dead_end_squares(maze)
    if dead_ends:
        faults.append(
            "MAZE-5: %d corridor square(s) have fewer than two corridor neighbours: %s"
            % (len(dead_ends), _squares_as_text(dead_ends))
        )

    unreachable = unreachable_corridor_squares(maze)
    if unreachable:
        faults.append(
            "MAZE-6: %d corridor square(s) cannot be walked to: %s"
            % (len(unreachable), _squares_as_text(unreachable))
        )

    two_wide = two_wide_corridor_squares(maze)
    if two_wide:
        faults.append(
            "MAZE-2: corridor is two squares wide at %s" % (_squares_as_text(two_wide),)
        )

    diagonal = diagonal_only_corridor_pairs(maze)
    if diagonal:
        faults.append(
            "MAZE-2: corridor runs diagonally between %s"
            % (
                ", ".join(
                    "%s and %s" % (_square_as_text(one), _square_as_text(two))
                    for one, two in diagonal[:8]
                ),
            )
        )

    return tuple(faults)


def _square_as_text(square: Square) -> str:
    return "(column %d, row %d)" % (square.column, square.row)


def _squares_as_text(squares: Tuple[Square, ...]) -> str:
    shown = ", ".join(_square_as_text(square) for square in squares[:8])
    if len(squares) > 8:
        shown += ", and %d more" % (len(squares) - 8,)
    return shown
