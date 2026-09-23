"""Lay out a random 19 x 29 maze (MAZE-1 to MAZE-6) from a random source it is handed.

The method is carve-then-repair (architecture caution C4), on a lattice:

* A *room* is a square whose column and row are both odd. There are 9 x 14 of
  them. A square with one odd and one even coordinate is the *link* between the
  two rooms either side of it. A square with both coordinates even is a
  *pillar*.
* **Carve.** A randomised depth-first search over the rooms opens the link to
  each room it reaches for the first time. The result is a spanning tree: every
  room is corridor and reachable from every other.
* **Repair.** Each room left with only one open link is a dead end. For each,
  in a fixed order, one more of its links is opened, chosen at random. Every
  room has at least two neighbouring rooms, so there is always one to open.

What the construction guarantees, which the tests then check over many seeds:

* Pillars and the outer ring are never opened, so every 2 x 2 block holds a
  pillar (corridors one square wide) and the outer ring is solid wall.
* An open link has exactly two corridor neighbours, the rooms it joins; after
  the repair every room has at least two. So there are no dead ends.
* Opening a link only ever adds a way through, so the spanning tree's
  connectivity survives the repair.
* Carving visits each room once and the repair is a single pass, so generation
  always finishes, in a bounded number of steps. There is no retry loop.

Pure domain code: no clock, and the only randomness is the ``rng`` passed in.
The same ``rng`` state always gives the same maze. The module does not import
``random``: a ``random.Random(seed)`` is what callers pass.
"""

from __future__ import annotations

from typing import Protocol, Sequence, TypeVar

from terminal_game.domain.maze import DIRECTIONS, HEIGHT, WIDTH, Maze, Square

T = TypeVar("T")


class RandomSource(Protocol):
    """What the generator needs from a random source. ``random.Random`` fits."""

    def randrange(self, stop: int) -> int: ...

    def choice(self, seq: Sequence[T]) -> T: ...


_ROOMS: tuple[Square, ...] = tuple(
    (col, row) for row in range(1, HEIGHT - 1, 2) for col in range(1, WIDTH - 1, 2)
)


def _neighbouring_rooms(room: Square) -> tuple[Square, ...]:
    col, row = room
    return tuple(
        (col + 2 * dc, row + 2 * dr)
        for dc, dr in DIRECTIONS
        if 1 <= col + 2 * dc <= WIDTH - 2 and 1 <= row + 2 * dr <= HEIGHT - 2
    )


def _link(a: Square, b: Square) -> Square:
    return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)


def generate_maze(rng: RandomSource) -> Maze:
    """Return a new 19 x 29 maze laid out using ``rng`` and nothing else random."""
    corridors: set[Square] = set()

    # Carve: randomised depth-first search, iterative so depth is no concern.
    start = _ROOMS[rng.randrange(len(_ROOMS))]
    corridors.add(start)
    stack = [start]
    while stack:
        room = stack[-1]
        unvisited = [n for n in _neighbouring_rooms(room) if n not in corridors]
        if unvisited:
            nxt = rng.choice(unvisited)
            corridors.add(_link(room, nxt))
            corridors.add(nxt)
            stack.append(nxt)
        else:
            stack.pop()

    # Repair: give every dead-end room a second way out.
    for room in _ROOMS:
        links = [_link(room, n) for n in _neighbouring_rooms(room)]
        closed = [link for link in links if link not in corridors]
        if len(links) - len(closed) < 2:
            corridors.add(rng.choice(closed))

    return Maze(WIDTH, HEIGHT, frozenset(corridors))
