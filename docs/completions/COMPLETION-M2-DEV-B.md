# Completion: M2, Dev B (lane B)

## WI-7: Game setup (MEDIUM)

- **PR:** #127, branch `r8/wi-7-game-setup`. It was merged by Dev B with `gh pr merge --merge` as `056ea1e` on 2026-09-23 at about 03:51Z.
- **Verification:** Copilot's review was "Needs a closer look", with no findings and no inline threads. Its one substantive note, a C3 floor that differed between the test and the harness, is fixed in `b2944c1`: both now require at least 100. The verifier `APPROVED` it in round 1 at head `b2944c1`, with no human gate.
- **Claims:** the plan's C1 to C7, plus:
  - A1: the ghost starts with no heading, and the maze is carried through.
  - A2: a maze with fewer than two corridor squares is refused, and a tie for the ghost goes to the first square in row-by-row order.
  - A3: setup uses no randomness.
  - A4: `GameState` is immutable, and its outcome values are WI-5's own.
- **Built:** `terminal_game/domain/game_state.py`, `terminal_game/domain/game_setup.py`, `tests/test_game_setup.py`, `tests/test_game_state.py` and `evidence/WI-7/setup_claims.py`.
- **Suite as left**, on landed `main` `056ea1e`: `.venv/bin/python -m pytest -q` gave 386 passed, 0 failed, 1 skipped.

## The game state that WI-8, WI-10 and WI-11 read

`GameState(maze, player, ghost, dots, score=0, outcome=PLAYING, ghost_heading=None)` is frozen. Each next state is made with `dataclasses.replace`. The outcome is `PLAYING` (`None`), `LOST` (`"lost"`) or `WON` (`"won"`), the same values as `presentation.status_line`. The ghost's start square keeps its dot. `docs/prs/PR-WI-7-game-setup.md` has the full description.

## WI-11: Turn resolution (MEDIUM)

- **PR:** #131, branch `r8/wi-11-turn-resolution`. It was merged by Dev B with `gh pr merge --merge` as `2641e5b` on 2026-09-23 at about 04:14Z.
- **Verification:** Copilot left one thread: the harness's non-vacuity floors were weaker than the tests'. They are fixed in `97feb5f`. Its overview also remarked on the order of the validation checks, with no thread; I disputed it on the PR, because a malformed direction is refused in every state on purpose. The verifier `APPROVED` it in round 1 at head `97feb5f`, with all 14 claims reproduced and no human gate.
- **Claims:** the plan's C1 to C11, plus:
  - A1: once the game is decided, neither a move nor a ghost step changes anything.
  - A2: a malformed direction is refused.
  - A3: a ghost step applies exactly what WI-8's policy returns, and leaves the dots and the score alone.
- **Built:** `terminal_game/application/turn_resolution.py` (`move_player(state, direction)` and `step_ghost(state, rng)`), `tests/test_turn_resolution.py` and `evidence/WI-11/turn_claims.py`.
- **Suite as left**, on landed `main` `2641e5b`: `.venv/bin/python -m pytest -q` gave 442 passed, 0 failed, 1 skipped.
- **For WI-12:** the session maps WI-6's `"up"`, `"down"`, `"left"` and `"right"` to `(0,-1)`, `(0,1)`, `(-1,0)` and `(1,0)` and calls `move_player`. Each tick calls `step_ghost(state, rng)`.
