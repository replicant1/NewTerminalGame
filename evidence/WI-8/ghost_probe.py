"""WI-8: the ghost policy, driven and measured, one section per claim.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-8/ghost_probe.py

Each section prints what it measured and a verdict line ``WI-8/Cn HOLDS`` or
``WI-8/Cn DOES NOT HOLD``.  The last line says whether all eight hold.
The hand-built mazes are drawn in the output so the situation is visible.
"""

from __future__ import annotations

import inspect
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terminal_game.domain.ghost import GhostMove, ghost_step  # noqa: E402
from terminal_game.domain.maze import DIRECTIONS, Maze  # noqa: E402
from terminal_game.domain.maze_generator import generate_maze  # noqa: E402

NORTH, SOUTH, EAST, WEST = (0, -1), (0, 1), (1, 0), (-1, 0)
NAMES = {NORTH: "north", SOUTH: "south", EAST: "east", WEST: "west", None: "none"}


def draw(maze, ghost_square):
    for row, line in enumerate(maze.to_rows()):
        print("      " + "".join("G" if (col, row) == ghost_square else ch for col, ch in enumerate(line)))


def verdict(claim, ok, detail):
    print("WI-8/%s %s: %s" % (claim, "HOLDS" if ok else "DOES NOT HOLD", detail))
    print()
    return ok


def main() -> int:
    results = []

    crossroads = Maze.from_rows(["#####", "##.##", "#...#", "##.##", "#####"])
    print("C1  crossroads, ghost G at (2, 2); 200 seeds per heading")
    draw(crossroads, (2, 2))
    straight = all(ghost_step(crossroads, (2, 2), h, random.Random(s)).square
                   == ((2 + h[0]), (2 + h[1])) for h in DIRECTIONS for s in range(200))
    corridor = Maze.from_rows(["#########", "#.......#", "#########"])
    g, path = GhostMove((1, 1), EAST), []
    rng = random.Random(1)
    for _ in range(6):
        g = ghost_step(corridor, g.square, g.heading, rng)
        path.append(g.square)
    results.append(verdict("C1", straight and path == [(c, 1) for c in range(2, 8)],
                           "through the junction straight on for every heading and seed: %s; "
                           "along a corridor heading east: %s" % (straight, path)))

    tee = Maze.from_rows(["#####", "#...#", "##.##", "##.##", "#####"])
    print("C2  T-junction, ghost G at (2, 1) heading north (wall ahead, came from (2, 2)); 10,000 trials")
    draw(tee, (2, 1))
    rng = random.Random(8)
    counts = Counter(ghost_step(tee, (2, 1), NORTH, rng).square for _ in range(10_000))
    share = {sq: counts[sq] / 10_000 for sq in ((1, 1), (3, 1), (2, 2))}
    results.append(verdict("C2", share[(1, 1)] >= 0.4 and share[(3, 1)] >= 0.4 and counts[(2, 2)] == 0,
                           "west (1, 1) %.1f%%, east (3, 1) %.1f%%, back (2, 2) %d times"
                           % (100 * share[(1, 1)], 100 * share[(3, 1)], counts[(2, 2)])))

    dead = Maze.from_rows(["######", "#....#", "######"])
    print("C3  dead end, ghost starting at (1, 1) heading east; six moves")
    draw(dead, (1, 1))
    g, path, rng = GhostMove((1, 1), EAST), [], random.Random(3)
    for _ in range(6):
        g = ghost_step(dead, g.square, g.heading, rng)
        path.append((g.square, NAMES[g.heading]))
    bend = Maze.from_rows(["#####", "#...#", "###.#", "#####"])
    at_bend = {ghost_step(bend, (3, 1), EAST, random.Random(s)).square for s in range(200)}
    results.append(verdict("C3", [sq for sq, _ in path] == [(2, 1), (3, 1), (4, 1), (3, 1), (2, 1), (1, 1)]
                           and at_bend == {(3, 2)},
                           "path %s; at an L-bend with one other way it never turns back: %s"
                           % (path, sorted(at_bend))))

    print("C4  one generated maze, one ghost random sequence, two players on different routes; 500 moves")
    maze = generate_maze(random.Random(4))
    corridors = maze.corridor_squares()

    def run(player_seed):
        ghost_rng, player_rng = random.Random(99), random.Random(player_seed)
        ghost, player, trail = GhostMove(corridors[-1], None), corridors[0], []
        for _ in range(500):
            player = player_rng.choice(maze.open_neighbours(player))
            ghost = ghost_step(maze, ghost.square, ghost.heading, ghost_rng)
            trail.append(ghost.square)
        return trail, player

    (a, pa), (b, pb) = run(1), run(2)
    params = list(inspect.signature(ghost_step).parameters)
    results.append(verdict("C4", a == b and pa != pb and params == ["maze", "square", "heading", "rng"],
                           "players ended at %s and %s; ghost paths identical: %s; the policy's "
                           "parameters: %s" % (pa, pb, a == b, params)))

    print("C5, C8  1,000 generated mazes x 1,000 moves")
    moves = bad_step = onto_wall = unmoved = 0
    for seed in range(1000):
        maze = generate_maze(random.Random(seed))
        rng = random.Random(1_000_000 + seed)
        ghost = GhostMove(maze.corridor_squares()[seed % len(maze.corridors)], None)
        for _ in range(1000):
            nxt = ghost_step(maze, ghost.square, ghost.heading, rng)
            step = (nxt.square[0] - ghost.square[0], nxt.square[1] - ghost.square[1])
            moves += 1
            bad_step += step not in DIRECTIONS
            onto_wall += not maze.is_corridor(nxt.square)
            unmoved += nxt.square == ghost.square
            ghost = nxt
    results.append(verdict("C5", bad_step == 0 and onto_wall == 0,
                           "%d moves: %d not one square N/S/E/W, %d onto a wall" % (moves, bad_step, onto_wall)))
    results.append(verdict("C8", unmoved == 0 and moves == 1_000_000,
                           "%d moves, %d where the ghost did not move, none raised" % (moves, unmoved)))

    print("C6  crossroads, ghost with no heading yet; 400 seeds")
    firsts = Counter(ghost_step(crossroads, (2, 2), None, random.Random(s)).square for s in range(400))
    results.append(verdict("C6", set(firsts) == set(crossroads.open_neighbours((2, 2))),
                           "first moves went to %s" % dict(sorted(firsts.items()))))

    print("C7  a generated maze with a dot on every corridor square but the start; 2,000 ghost moves")
    maze = generate_maze(random.Random(7))
    start = maze.corridor_squares()[0]
    dots = frozenset(sq for sq in maze.corridors if sq != start)
    before = set(dots)
    ghost, rng, on_dots = GhostMove(start, None), random.Random(70), 0
    for _ in range(2000):
        ghost = ghost_step(maze, ghost.square, ghost.heading, rng)
        on_dots += ghost.square in dots
    results.append(verdict("C7", dots == before and "dots" not in params,
                           "the ghost landed on a dotted square %d times; dots before %d, after %d, "
                           "identical: %s; the policy is not handed the dots"
                           % (on_dots, len(before), len(dots), dots == before)))

    print("WI-8: %d of 8 claims hold" % sum(results))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
