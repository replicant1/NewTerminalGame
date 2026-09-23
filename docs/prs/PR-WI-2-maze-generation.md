# WI-2: Maze generation

Risk: MEDIUM
It is the plan's floor for WI-2. It is not raised: the change is pure domain code with no window, no input path and no shared configuration. It is still MEDIUM rather than LOW because WI-7, WI-8 and WI-10 all build on this maze's interface.

**Branch:** `r8/wi-2-maze-generation`, cut from `main` at `8bc9496`, with `main` merged in at `75723e7` (WI-1). The base for controls is `75723e7`. **Lane B**, Dev B. **Realises:** MAZE-1 (the grid), MAZE-2, MAZE-3, MAZE-4, MAZE-5, MAZE-6.

## What it is

- `terminal_game/domain/maze.py`: `Maze`, an immutable value: `width`, `height`, and the frozenset of corridor squares. A square is a `(col, row)` tuple counted from 0 at the north-west corner (col 0–18 west to east, row 0–28 north to south). It answers `is_wall`, `is_corridor`, `contains`, `neighbours`, `open_neighbours` (north, south, east, west, in that order) and `corridor_squares` (row by row). A square off the grid is neither wall nor corridor. `Maze.from_rows(["#####", "#...#", ...])` builds one by hand (`#` wall, `.` corridor), and `to_rows()` is its inverse. It accepts any rectangle and does **not** enforce the generator's invariants, so other items can hand-build small or broken mazes (WI-7/C2, WI-8/C3).
- `terminal_game/domain/maze_generator.py`: `generate_maze(rng) -> Maze`. It uses only the source it is handed (anything with `randrange` and `choice`, e.g. `random.Random(seed)`). Carve, then repair, on a lattice. Rooms sit at odd (col, row). A randomised depth-first search opens a spanning tree over the 9 × 14 rooms. Each room left with one open link then gets one more, chosen at random. Squares with both coordinates even, and the outer ring, are never opened. Last, `ensure_connected` floods the result and refuses it unless every corridor square is reached. The module docstring explains why each invariant holds by construction. The tests check each one over 1,000 seeds anyway.

## Claims

The run used seeds 0 to 999 and `.venv/bin/python` built from `requirements.txt` as in plan §1.2. The branch has `main` merged in at `75723e7` (WI-1), so the package markers are WI-1's and are not in this diff. WI-1's layer check `.venv/bin/python -m tools.layer_check` reports `domain 3` modules examined and `PASS (0 violation(s), 0 problem(s))` with the maze in place. Every command runs from the repository root. The harness `evidence/WI-2/maze_claims.py` is referred to below as **H**. It prints one line per claim, with the counts it took and `PASS` or `FAIL`, then a sample maze, then `ALL PASS` or `SOME FAIL`. It exits 0 only for `ALL PASS`.

| Claim | Word for word | Evidence | What the output shows | Control |
|---|---|---|---|---|
| WI-2/C1 | Every generated maze is 19 grid squares across and 29 deep, and every square is either wall or corridor. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py::test_c1_every_maze_is_19_by_29_and_every_square_is_wall_or_corridor` and H | `PASSED`. H: `C1  1000/1000 mazes are 19 x 29; squares that are neither '#' nor '.': 0  PASS`. The test also asserts `is_wall != is_corridor` on all 551 squares of every maze. | n/a: the maze is new code with no counterpart. At the base for controls, `75723e7` (the merge-base with `main`, after WI-1), `terminal_game/` holds only WI-1's five package markers. There is no `maze.py`, no `maze_generator.py` and no maze test (`git ls-tree -r --name-only 75723e7 terminal_game tests`), and this diff against that base is additions only. |
| WI-2/C2 | Over at least 1,000 mazes from distinct seeds, every square of the outer ring is wall, so nothing can leave the maze and there are no tunnels through the sides. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py::test_c2_the_outer_ring_is_wall_in_every_maze` and H | `PASSED`. H: `C2  outer-ring squares checked: 92000; corridor among them: 0  PASS`, that is 92 ring squares × 1,000 mazes. On failure the test names the seed and the open squares. | n/a: new code, as for C1 |
| WI-2/C3 | Over the same mazes, every corridor square has at least two corridor neighbours among north, south, east and west: there are no dead ends. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py::test_c3_no_corridor_square_has_fewer_than_two_corridor_neighbours` and H | `PASSED`. H: `C3  corridor squares checked: 265297; fewest corridor neighbours of any: 2; with fewer than 2: 0  PASS` | n/a: new code |
| WI-2/C4 | Over the same mazes, every corridor square can be reached from every other corridor square by steps north, south, east and west. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py::test_c4_every_corridor_square_reaches_every_other` and H | `PASSED`. H: `C4  mazes whose every corridor square is reached from one: 1000/1000  PASS`. A breadth-first flood from one corridor square reaches the whole corridor set. Steps are undirected, so reaching everything from one square means every square reaches every other. | n/a: new code |
| WI-2/C5 | Over the same mazes, corridors are one square wide: no 2 × 2 block of squares is all corridor. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py::test_c5_no_two_by_two_block_is_all_corridor` and H | `PASSED`. H: `C5  2 x 2 blocks checked: 504000; all-corridor: 0  PASS`, that is 18 × 28 blocks × 1,000 mazes. | n/a: new code |
| WI-2/C6 | The same seed always gives the same maze, and 1,000 distinct seeds give 1,000 distinct mazes. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py -k c6` and H | Two tests `PASSED`: each seed regenerated gives an equal maze with identical rows, and the set of 1,000 row-tuples has 1,000 members. H: `C6  seeds reproducing the same maze: 1000/1000; distinct mazes: 1000 of 1000  PASS` | n/a: new code |
| WI-2/C7 | Generation always finishes: over the same 1,000 seeds, no maze takes longer than one second to generate. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py::test_c7_no_maze_takes_as_long_as_a_second` and H | `PASSED`. H: `C7  slowest generation: 0.39 ms (limit 1000 ms); mean 0.34 ms  PASS` (my run; the figures vary by machine). By construction there is no retry loop: carving visits each of the 126 rooms once and the repair is one pass. | n/a: new code |
| WI-2/A1 | Every generated maze has corridor on every row and every column inside the outer ring, so C2–C5 cannot hold of an empty or partial maze. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py::test_a1_every_row_and_column_inside_the_ring_has_corridor` and H | `PASSED`. H: `A1  interior rows/columns with no corridor: 0; fewest corridor squares in a maze: 259  PASS` | n/a: new code |
| WI-2/A2 | The generator draws randomness only from the source it is handed and reads no clock: the same source state gives the same maze whatever the global random state, and the two maze modules import nothing beyond `__future__`, `dataclasses`, `typing` and each other. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py -k a2` | Two tests `PASSED`. One reseeds the global `random` differently before two generations from `random.Random(42)` and gets equal mazes. The other parses both modules' imports and finds nothing outside the allowed set, and it fails if it scanned nothing. | n/a: new code |
| WI-2/A3 | The `Maze` value answers the game's questions. Squares are `(col, row)` from the north-west. `is_wall` and `is_corridor` are exact inside the grid and both false off it. `neighbours` and `open_neighbours` list north, south, east, west in that order and never a square off the grid. `corridor_squares` runs row by row from the north. Text round-trips through `from_rows` and `to_rows`. Malformed text, an out-of-grid corridor and an empty grid are refused. A maze cannot be changed, not even through the set it was built from, and two are equal exactly when every square matches. A hand-built maze may contain a dead end. | Executable: `.venv/bin/python -m pytest -v tests/test_maze.py` | 22 tests `PASSED`. Each test's expected values are read off a hand-drawn 5 × 5 or smaller maze, not computed by the code under test. | n/a: new code |
| WI-2/A4 | Before it hands a maze out, the generator checks that every corridor square can be reached from every other, and refuses a maze where one cannot: `ensure_connected` raises `ValueError` naming the unreachable squares for a disconnected maze, and hands a connected maze back unchanged. `generate_maze` returns only what `ensure_connected` has passed. | Executable: `.venv/bin/python -m pytest -v tests/test_maze_generator.py -k a4`. Walk-through for the last sentence: `terminal_game/domain/maze_generator.py:117` is `generate_maze`'s only `return`, and it returns `ensure_connected(Maze(...))`. | Two tests `PASSED`. One is a hand-built maze in two pockets, refused with the message `unreachable from (1, 1): [(4, 1), (5, 1), (4, 2), (5, 2)]`. The other is a connected loop, and a maze with no corridor at all, each returned as the same object. C4 above shows no generated maze is refused. Added in answer to Copilot's second comment. | n/a: new code |

## Diff map

```
terminal_game/domain/maze.py:1-30                   -> WI-2/A3 (square convention, off-grid rule), C1 (WIDTH 19, HEIGHT 29), A2 (imports)
terminal_game/domain/maze.py:33-49                  -> WI-2/A3 (immutable value incl. frozen copy of the caller's set, equality, refusals), C6 (equality is what "same maze" is judged by)
terminal_game/domain/maze.py:51-74                  -> WI-2/A3 (from_rows/to_rows), C1 (every square is '#' or '.')
terminal_game/domain/maze.py:76-100                 -> WI-2/A3 (contains, is_wall, is_corridor, neighbours, open_neighbours, corridor_squares), C1 (is_wall != is_corridor)
terminal_game/domain/maze_generator.py:1-34         -> docstring: why C2-C5 and C7 hold by construction, and A4
terminal_game/domain/maze_generator.py:36-51        -> WI-2/A2 (RandomSource protocol; no random import)
terminal_game/domain/maze_generator.py:53-68        -> WI-2/C1, C2, C5 (room lattice inside the ring; pillars never opened)
terminal_game/domain/maze_generator.py:71-88        -> WI-2/A4 (ensure_connected), C4
terminal_game/domain/maze_generator.py:91-108       -> WI-2/C4, C6, C7 (spanning-tree carve, deterministic in rng, bounded)
terminal_game/domain/maze_generator.py:110-117      -> WI-2/C3 (dead-end repair), C4 (only adds links), A4 (checked before return)
tests/test_maze_generator.py (new)                  -> evidence for C1-C7, A1, A2, A4
tests/test_maze.py (new)                            -> evidence for A3
evidence/WI-2/maze_claims.py (new)                  -> evidence (harness H) for C1-C7, A1
docs/prs/PR-WI-2-maze-generation.md (new)           -> this brief
docs/progress/r8-wi-2-maze-generation.md (new)      -> progress log
```

## Settled interface, for the items that build on it (WI-7, WI-8, WI-10)

- `from terminal_game.domain.maze import Maze, Square, WIDTH, HEIGHT, DIRECTIONS`. `from terminal_game.domain.maze_generator import generate_maze`. (`ensure_connected` is public in the generator module too, for anyone who hand-builds a maze and wants it checked.)
- `Square = tuple[int, int]` is `(col, row)`. `DIRECTIONS` is `((0,-1), (0,1), (1,0), (-1,0))`: north, south, east, west, as `(dcol, drow)`.
- `maze.is_wall(sq)`, `maze.is_corridor(sq)`: both are `False` off the grid, which is what WI-4/C3 wants ("beyond the edge counts as not wall") and what movement wants (impassable).
- `maze.open_neighbours(sq)` is always in N, S, E, W order, so a seeded policy that picks from it is reproducible.
- `generate_maze(random.Random(seed))` is the only way randomness enters. The same seed gives the same maze.

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
