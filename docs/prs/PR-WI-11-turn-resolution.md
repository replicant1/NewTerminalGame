# WI-11: Turn resolution

Risk: MEDIUM
This is the plan's floor for WI-11, and I have not raised it. The item is pure application logic, with no window, no input path and no shared configuration. It stays MEDIUM because its step order decides END-3 (plan §1.6, architecture C6), and WI-12 builds on it.

**Branch:** `r8/wi-11-turn-resolution`, cut from `main` at `b1adc97`, with `main` merged in again at `c1d6be4` (WI-8, #129). **The base for controls is `c1d6be4`.** The branch was briefly stacked on `r8/wi-8-ghost-policy` at `41ef09c`, and `terminal_game/domain/ghost.py` is identical between that commit and `c1d6be4`. It is not stacked now: it targets `main`. **Lane B**, Dev B. **Realises:** CTRL-1 (the move), CTRL-2, CTRL-3, SCORE-1, SCORE-2, SCORE-3, SCORE-5, END-1, END-2, END-3, GAME-2.

## What it is

`terminal_game/application/turn_resolution.py` holds the rules in one fixed order, as two pure functions from one `GameState` to the next.

- **`move_player(state, direction)`**. The direction is one of `maze.DIRECTIONS`, written `(dcol, drow)`. The steps are:
  1. Decided? Then nothing changes.
  2. Wall? Then the same state comes back.
  3. Move one square.
  4. **Collision**: if the ghost is on that square, the game is lost and the step ends. The dot there is not eaten and the score does not change.
  5. Eat: remove the dot and add 1 to the score.
  6. Win: if that was the last dot, the game is won.
- **`step_ghost(state, rng)`**. The steps are:
  1. Decided? Then nothing changes.
  2. Apply WI-8's `ghost_step(maze, ghost, ghost_heading, rng)`, as agreed with Dev A on #129.
  3. Collision: if the ghost is now on the player's square, the game is lost.

  `GhostStuck` propagates rather than being caught. WI-8/C8 shows it never happens on a generated maze.

**For WI-12 (session control):** WI-6's intents `"up"`, `"down"`, `"left"` and `"right"` map to `(0,-1)`, `(0,1)`, `(-1,0)` and `(1,0)`. The session makes that mapping and calls `move_player`. Each tick calls `step_ghost` with the session's random source.

## Claims

Every command runs from the repository root, with `.venv/bin/python` built from `requirements.txt` as in plan §1.2. **H** is the harness `evidence/WI-11/turn_claims.py`. It runs the C5 and C11 long runs with printed counts. It then prints the before and after states of each ending scenario on the corridor `#.......#`, and ends with `ALL PASS` or `SOME FAIL`. It exits 0 only on `ALL PASS`.

**Control for every claim: n/a.** The turn resolver is new code with no counterpart. At the base `c1d6be4`, `terminal_game/application/` holds only `__init__.py` (`git ls-tree --name-only c1d6be4 terminal_game/application/`), and nothing on the base resolves a move or a ghost step. This diff against the base is additions only.

| Claim | Word for word | Evidence | What the output shows |
|---|---|---|---|
| WI-11/C1 | A move towards a corridor square moves the player exactly one square in that direction. | Executable: `.venv/bin/python -m pytest -v tests/test_turn_resolution.py -k c1_` | 5 `PASSED`. From a crossroads, north, south, east and west each land on the adjacent square. One move east along a seven-square corridor lands on (2, 1), not the far end. |
| WI-11/C2 | A move towards a wall changes nothing at all: the player's square, the dots, the score and the outcome are identical afterwards. | Executable: `-k c2_`, and H | 5 `PASSED` (five wall-facing moves). Each compares player, dots, score, outcome, ghost and heading, then the whole state. H prints the scenario `C2 move north into the wall` with identical before and after states. |
| WI-11/C3 | Moving onto a square that holds a dot removes that dot for the rest of the game and adds exactly one to the score. | Executable: `-k c3_` | `PASSED`: from score 5, a step onto (2, 1) gives dots `{(3, 1)}` and score 6. Moving away and back again leaves the dots at `{(3, 1)}` and the score at 6. |
| WI-11/C4 | Moving onto a square whose dot has already been eaten, including the start square, adds nothing to the score. | Executable: `-k c4_` | 2 `PASSED`. One is hand-built: an eaten square, then the start square, and the score stays at 2. The other uses a real `new_game`: one step away and back to the start adds nothing. |
| WI-11/C5 | Over 1,000 games of random moves and ghost steps, the score never goes down. | Executable: `-k c5_`, and H | `PASSED`, asserting `after.score >= before.score` at every one of the up to 2,000 steps per game. The test fails if fewer than 1,000 dots were eaten in total, and H applies the same floor. H: `C5  1000 games x 1000 (move + ghost step): score decreases 0; dots eaten 28421; ghost moves 431046; games lost 787, won 0  PASS` |
| WI-11/C6 | The player walking onto the ghost's square loses the game. | Executable: `-k c6_` | `PASSED`: the player lands on (4, 1), the ghost's square, and the outcome is `LOST`. |
| WI-11/C7 | The ghost stepping onto the player's square loses the game. | Executable: `-k c7_` | `PASSED`: the ghost at (5, 1), heading west, steps onto the player at (4, 1), and the outcome is `LOST`. The random source fails the test if it is drawn from, so this is the policy's straight-on move. |
| WI-11/C8 | Eating the last dot wins the game. | Executable: `-k c8_`, and H | 2 `PASSED`. Eating the last dot gives no dots, score 10 and `WON`. Eating one of two dots stays `PLAYING`. H prints scenario `C8`. |
| WI-11/C9 | Walking onto the ghost's square when it holds the last dot loses the game, not wins it. That dot is not eaten, and the score stays what it was before the move. | Executable: `-k c9_`, and H | `PASSED`. The outcome is `LOST`, not `WON`, the dots are still `{(3, 1)}`, the score is still 41, and the player is on (3, 1). H: `before: player (2, 1) ghost (3, 1) dots [(3, 1)] score 41 outcome None` / `after: player (3, 1) ghost (3, 1) dots [(3, 1)] score 41 outcome 'lost'`. **This is the consequence test for the order-sensitive step in plan §1.6.** If eating ran before the collision, the dots would be empty, the score 42 and the outcome `WON`. |
| WI-11/C10 | From adjacent squares, the player and the ghost can never pass through each other: a player move towards the ghost, or a ghost step towards the player, loses the game on that step. | Executable: `-k c10_`, and H | 3 `PASSED`. A player move from (3, 1) towards the ghost at (4, 1) gives `LOST` with both on (4, 1). A ghost step from (4, 1) towards the player at (3, 1) gives `LOST` with both on (3, 1). A ghost turning back at a dead end onto an adjacent player also gives `LOST`. H prints both adjacent scenarios. |
| WI-11/C11 | Over 1,000 games of 1,000 random moves each, the player never stands on a wall and never leaves the maze. | Executable: `-k c11_`, and H | `PASSED`, asserting at every move that the player is inside 19 × 29, on corridor, and moved by at most one square north, south, east or west. The test fails if fewer than 100,000 moves changed square, and H applies the same floor. H: `C11  1000 games x 1000 random moves: squares changed 509273; off the grid 0; on a wall 0; jumps of more than one square 0  PASS`. The ghost does not step in these games, so they run longer. A game still ends if the player walks into the ghost. |
| WI-11/A1 | Once the game is won or lost, neither a move nor a ghost step changes anything: the same state comes back, and the random source is not drawn from. | Executable: `-k a1_` | 2 `PASSED` (one `LOST`, one `WON`). All four directions and a ghost step return the identical object, and the random source fails the test if drawn from. |
| WI-11/A2 | A direction that is not one square north, south, east or west is refused with `ValueError`. | Executable: `-k a2_` | 5 `PASSED`: `(1, 1)`, `(0, 0)`, `(2, 0)`, `None` and `"up"`. |
| WI-11/A3 | A ghost step applies exactly the square and heading that WI-8's policy returns for the same maze, ghost, heading and random state, and leaves the dots, the score and the player alone. | Executable: `-k a3_` | `PASSED`. Over 200 steps on a generated maze, two equal random sources give `step_ghost`'s result equal to `ghost_step`'s at every step, with dots, score and player unchanged. This is the seam test WI-8's brief asked of WI-11 under its C7. |

Also at this head: the suite `.venv/bin/python -m pytest -q` gives 442 passed, 0 failed, 1 skipped, and `.venv/bin/python -m tools.layer_check` gives `application 2`, `PASS (0 violation(s), 0 problem(s))`.

## Diff map

```
terminal_game/application/turn_resolution.py:1-40    -> docstring: the fixed order (C1-C11, A1), for WI-12
terminal_game/application/turn_resolution.py:42-48   -> mechanical (imports)
terminal_game/application/turn_resolution.py:51-54   -> WI-11/A2 (direction refused)
terminal_game/application/turn_resolution.py:55-56   -> WI-11/A1 (decided: unchanged)
terminal_game/application/turn_resolution.py:57-59   -> WI-11/C2 (wall: unchanged), C11 (never onto a wall or off the grid)
terminal_game/application/turn_resolution.py:60-61   -> WI-11/C1, C6, C9, C10 (move; collision decided before eating)
terminal_game/application/turn_resolution.py:62-63   -> WI-11/C1, C4 (no dot: nothing scored)
terminal_game/application/turn_resolution.py:64-65   -> WI-11/C3, C5 (eat, +1), C8 (last dot wins)
terminal_game/application/turn_resolution.py:68-71   -> WI-11/A1 (decided: unchanged, no draw)
terminal_game/application/turn_resolution.py:72-74   -> WI-11/A3 (policy applied), C7, C10 (collision)
tests/test_turn_resolution.py (new)                  -> evidence for C1-C11, A1-A3
evidence/WI-11/turn_claims.py (new)                  -> evidence (harness H) for C2, C5, C8-C11
docs/prs/PR-WI-11-turn-resolution.md (new)           -> this brief
docs/progress/r8-wi-11-turn-resolution.md (new)      -> progress log
docs/completions/COMPLETION-M2-DEV-B.md (new)        -> WI-7 completion record (mechanical; conductor's ruling)
docs/progress/r8-wi-7-game-setup.md:+4               -> WI-7 completion record (mechanical; WI-7's final log lines)
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
