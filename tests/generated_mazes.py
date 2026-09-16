"""The seeded mazes every Domain property sweep shares.

Caution C4 asks for the maze's properties to be checked over **many seeds**,
and WI-6's start-square rules want the same mazes. Laying 200 of them out once
per suite run rather than once per test keeps that sweep affordable: it is
about a second of the suite, and it was five before this module existed.

Deliberately **not** named ``test_*``, so unittest discovery never treats it
as a test module.
"""

import random
from typing import Dict, Tuple

from terminal_game.domain.maze import Maze
from terminal_game.domain.maze_generator import generate_maze

#: Many seeds, not one.
SEEDS: Tuple[int, ...] = tuple(range(200))

_LAID_OUT: Dict[int, Maze] = {}


def mazes_for_every_seed() -> Dict[int, Maze]:
    """Every seed's maze, laid out on first use and kept."""
    if not _LAID_OUT:
        _LAID_OUT.update((seed, generate_maze(random.Random(seed))) for seed in SEEDS)
    return _LAID_OUT


def maze_for(seed: int) -> Maze:
    """One seed's maze, from the shared set where it is one of them."""
    if seed in SEEDS:
        return mazes_for_every_seed()[seed]
    return generate_maze(random.Random(seed))
