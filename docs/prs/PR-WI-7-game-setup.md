# WI-7: Game setup

Risk: MEDIUM
It is the plan's floor for WI-7, and I have not raised it. This is pure domain code: no window, no input path, no shared configuration. It stays MEDIUM because WI-10's composer and WI-11's turn resolver both read the game state defined here.

**Branch:** `r8/wi-7-game-setup`, cut from `main` at `796aebe`, with `main` merged in again at `0680c8c` (WI-4, WI-6). **The base for controls is `0680c8c`.** **Lane B**, Dev B. **Realises:** START-1, START-2, START-3, START-4, GAME-1.

## What it is

- `terminal_game/domain/game_state.py` defines `GameState`, an immutable value. It also defines the outcome values `PLAYING = None`, `LOST = "lost"` and `WON = "won"`.
- `terminal_game/domain/game_setup.py` defines `new_game(maze) -> GameState`. It uses no randomness.
  - The player starts on the corridor square nearest the centre `(width // 2, height // 2)`, which is `(9, 14)` on the real maze.
  - The ghost starts on the corridor square furthest from the player, by straight-line distance.
  - Distances are compared as whole-number squared distances. Ties go to the first square in row-by-row order.
  - Every corridor square except the player's gets a dot. The score starts at 0, with no outcome and no ghost heading.
  - A maze with fewer than two corridor squares is refused.

## The game state, for lane A (WI-8, WI-10) and for WI-11 (plan §5.2)

```python
from terminal_game.domain.game_state import GameState, PLAYING, LOST, WON
from terminal_game.domain.game_setup import new_game

@dataclass(frozen=True)
class GameState:
    maze: Maze                          # WI-2's Maze; squares are (col, row) from the north-west
    player: Square                      # (col, row)
    ghost: Square                       # (col, row)
    dots: frozenset[Square]             # squares that still hold a dot
    score: int = 0
    outcome: Optional[str] = PLAYING    # PLAYING (None), LOST ("lost") or WON ("won")
    ghost_heading: Optional[Square] = None   # (dcol, drow), one of maze.DIRECTIONS; None before the ghost's first move
```

- **The composer (WI-10)** reads `maze`, `dots`, `player`, `ghost`, `score` and `outcome`. The outcome values are the same objects as `presentation.status_line`'s, so `status_row(state.score, state.outcome)` works unchanged. `tests/test_game_state.py` pins that seam. A square shows a dot exactly when it is in `state.dots`. The ghost's square keeps its dot, and the composer hides it while the ghost stands there (WI-10/C7).
- **The ghost policy (WI-8)** gets its inputs from `state.maze`, `state.ghost` and `state.ghost_heading`, plus the random source. `ghost_heading` is `None` at the start (WI-8/C6).
- **Turns (WI-11)** make the next state with `dataclasses.replace(state, ...)` and never change a state in place. `dots` is always frozen: a caller's mutable set is copied.

## Claims

Every command runs from the repository root, using `.venv/bin/python` built from `requirements.txt` as in plan §1.2. Generated mazes use seeds 0 to 999. **H** is the harness `evidence/WI-7/setup_claims.py`. It prints one line per claim with its counts and `PASS` or `FAIL`, then draws the C2 hand-built maze, then ends with `ALL PASS` or `SOME FAIL`. It exits 0 only for `ALL PASS`. The tests and H work out nearest, furthest and corridor step counts for themselves from `maze.to_rows()`. They do not take those values from the code under test.

**Control for every claim:** n/a, because this is new code with no counterpart. At the base `0680c8c`, `terminal_game/domain/` holds only `__init__.py`, `maze.py` and `maze_generator.py` (`git ls-tree --name-only 0680c8c terminal_game/domain/`). There is no game state and no setup, and this diff against that base is additions only.

| Claim | Word for word | Evidence | What the output shows |
|---|---|---|---|
| WI-7/C1 | The player starts on the corridor square nearest the centre square (column 9, row 14, counting from 0), by straight-line distance in grid squares. When several are equally near, the same maze always gives the same one. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k c1`, and H | Four tests `PASSED`. Over 1,000 mazes, the player's squared distance to (9, 14) equals the minimum over all corridor squares. On a hand-built maze the player starts at (4, 5). On a 19 × 29 maze whose centre is wall, with four corridor squares at distance 1, forty calls over two equal maze values all give (9, 13). For 100 seeds, regenerating the maze gives the same start. H: `C1  players not on a nearest-to-centre square: 0/1000; same maze, different start: 0  PASS` |
| WI-7/C2 | The ghost starts on the corridor square furthest from the player's start by straight-line distance in grid squares, not by distance along the corridors. This is shown on a hand-built maze where the two measures pick different squares. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k c2`, and H | Two tests `PASSED`. On the hand-built 9 × 13 maze, the test first confirms the two measures really differ: straight line picks (7, 11), corridors pick (7, 1). It then asserts the ghost is at (7, 11). Over 1,000 mazes, the ghost is at the greatest straight-line distance. H: `C2  ghosts not at the greatest straight-line distance: 0/1000; hand-built maze: straight-line picks (7, 11) (15 steps), corridors pick (7, 1) (19 steps), ghost at (7, 11)  PASS`, followed by the maze drawn with P, G and x. |
| WI-7/C3 | When the centre square is itself corridor, the player starts on it. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k c3`, and H | Two tests `PASSED`. One uses a hand-built maze with an open centre. The other covers every generated maze whose centre is corridor, and fails if fewer than 100 are found (H applies the same floor). H: `C3  mazes with an open centre: 569; player not on it: 0  PASS` |
| WI-7/C4 | Every corridor square holds one dot except the player's start square, which holds none, and no wall square holds a dot. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k c4`, and H | Two tests `PASSED`. Over 1,000 mazes, `dots` equals the corridor squares minus the player's. On a three-square corridor, the dots are exactly the two ends. H: `C4  mazes whose dots are not exactly the corridor squares minus the player's: 0/1000  PASS` |
| WI-7/C5 | The ghost's start square holds a dot. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k c5`, and H | `PASSED`. H: `C5  ghost start squares without a dot: 0/1000  PASS` |
| WI-7/C6 | The score starts at zero and no outcome is decided. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k c6`, and H | `PASSED`: score 0, and the outcome is `PLAYING`, neither `LOST` nor `WON`. H: `C6  starts not at score 0, undecided, no ghost heading: 0/1000  PASS` |
| WI-7/C7 | Over 1,000 generated mazes, the player and the ghost never start on the same square, and neither starts on a wall. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k c7`, and H | `PASSED`. H: `C7  player and ghost on the same square: 0/1000; either on a wall: 0/1000  PASS` |
| WI-7/A1 | The starting state carries the maze it was given, and the ghost starts with no heading (`ghost_heading is None`), as WI-8/C6 expects. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k a1` | Two tests `PASSED`. |
| WI-7/A2 | Setup refuses a maze with fewer than two corridor squares (`ValueError`, naming the count). A tie for the ghost's square goes to the first tied square in row-by-row order. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k a2` | Three tests `PASSED`. Mazes with 0 and with 1 corridor squares are refused with messages ending `this maze has 0` and `this maze has 1`. On a three-square corridor the player is at the centre (2, 1) and the ghost at (1, 1), not (3, 1). |
| WI-7/A3 | Setup uses no randomness: it takes no random source, and the global random state has no effect on it. | Executable: `.venv/bin/python -m pytest -v tests/test_game_setup.py -k a3`, and `.venv/bin/python -m tools.layer_check` | `PASSED`: two different global seeds give equal states. The layer check reports `domain 5` modules examined and `PASS (0 violation(s), 0 problem(s))`. |
| WI-7/A4 | `GameState` is an immutable value. It cannot be assigned to, it keeps a frozen copy of the dots it was built from, and the next state is made with `dataclasses.replace`, which leaves the old one untouched. Its outcome values are the status line's own, so the composer can hand `state.outcome` to WI-5 unchanged. | Executable: `.venv/bin/python -m pytest -v tests/test_game_state.py` | Four tests `PASSED`. The seam test compares `(PLAYING, LOST, WON)` in the domain with WI-5's, and renders `status_text(3, game_state.LOST)` as ` CAUGHT  score 3…`. |

## Diff map

```
terminal_game/domain/game_state.py:1-21             -> docstring: the state's fields, for WI-8/WI-10/WI-11 (A1, A4)
terminal_game/domain/game_state.py:23-32            -> WI-7/C6, A4 (PLAYING/LOST/WON equal to WI-5's)
terminal_game/domain/game_state.py:35-47            -> WI-7/A4 (frozen value, frozen dots), C6 (defaults score 0, PLAYING), A1 (ghost_heading None)
terminal_game/domain/game_setup.py:1-20             -> docstring: centre, measures, ties (C1, C2, C3, A2)
terminal_game/domain/game_setup.py:28-33            -> WI-7/C1, C2, C3 (squared distance; centre (9, 14))
terminal_game/domain/game_setup.py:36-40            -> WI-7/A2 (fewer than two corridor squares refused)
terminal_game/domain/game_setup.py:41-44            -> WI-7/C1, C3 (player), C2 (ghost), C7, A2 (row-by-row ties)
terminal_game/domain/game_setup.py:45-46            -> WI-7/C4, C5 (dots), C6 (score, outcome), A1 (maze, heading)
tests/test_game_setup.py (new)                      -> evidence for C1-C7, A1-A3
tests/test_game_state.py (new)                      -> evidence for A4
evidence/WI-7/setup_claims.py (new)                 -> evidence (harness H) for C1-C7
docs/prs/PR-WI-7-game-setup.md (new)                -> this brief
docs/progress/r8-wi-7-game-setup.md (new)           -> progress log
docs/completions/COMPLETION-M1-DEV-B.md (new)       -> WI-2 completion record (mechanical; conductor's ruling)
docs/progress/r8-wi-2-maze-generation.md:+4         -> WI-2 completion record (mechanical; WI-2's final log lines)
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
