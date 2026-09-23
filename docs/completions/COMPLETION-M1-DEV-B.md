# Completion: M1, Dev B (lane B)

## WI-2: Maze generation (MEDIUM)

- **PR:** #121, branch `r8/wi-2-maze-generation`. It was merged by Dev B with `gh pr merge --merge` as `86eca86` on 2026-09-23 at about 03:31Z.
- **Verification:** Copilot left 2 comments, both fixed in `4097a86` and answered. The verifier requested changes in round 1: the Copilot replies lacked the `REVIEW-REPLY` marker, and all 11 claims were reproduced. Round 2 was `APPROVED` at head `3c0f9ce`, with no human gate.
- **Claims:** plan claims C1 to C7, plus A1 (non-vacuity), A2 (no clock and no unhanded randomness), A3 (the `Maze` value's queries) and A4 (connectivity checked before a maze is handed out).
- **Built:** `terminal_game/domain/maze.py`, the `Maze` value; `terminal_game/domain/maze_generator.py`, `generate_maze(rng)` and `ensure_connected(maze)`; `tests/test_maze.py`; `tests/test_maze_generator.py`; `evidence/WI-2/maze_claims.py`.
- **Suite as left**, on landed `main` `86eca86`: `.venv/bin/python -m pytest -q` gave 165 passed, 0 failed, 1 skipped. `.venv/bin/python -m tools.layer_check` gave PASS with 0 violations and 3 domain modules examined.

## The maze interface that WI-7, WI-8 and WI-10 build on

- `Square = tuple[int, int]` is `(col, row)`, counted from 0 at the north-west corner.
- `Maze` has these members: `width`, `height`, `corridors` (a frozenset), `is_wall`, `is_corridor`, `contains`, `neighbours`, `open_neighbours` (ordered N, S, E, W), `corridor_squares` (row by row), `from_rows` (`#` wall, `.` corridor) and `to_rows`.
- A square off the grid is neither wall nor corridor. `DIRECTIONS` lists N, S, E, W as `(dcol, drow)`.
- `generate_maze(random.Random(seed))` is where randomness enters. The same seed gives the same maze.
