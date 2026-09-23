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
