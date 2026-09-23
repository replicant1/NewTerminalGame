# Completion record: M2, Dev A (lane A)

Lane A's M2 items are WI-8 and WI-10. Both have merged.

## WI-8: Ghost movement policy: merged

- **PR:** #129, branch `r8/wi-8-ghost-policy`, cut from `origin/main` at `0680c8c`. It carried lane A's M1 completion record, on the conductor's ruling.
- **Merged:** 2026-09-23 at 03:55:45Z as `c1d6be4`. **Risk:** MEDIUM, the floor, not raised. No human gate.
- **Copilot:** one thread: a bend with a single way on still consumed a random draw. Fixed at `41ef09c` with `_pick`, which draws only at a real choice. This became WI-8/A2.
- **Verifier:** round 1 `APPROVED` at `41ef09c8a38c3d0dbb3657c7458c1669ee6c049b`. C1–C8, A1 and A2 are REPRODUCED. All controls were `n/a` (new module), and the verifier accepted them after confirming that the base stops at `ModuleNotFoundError`.
- **Built:** `terminal_game/domain/ghost.py`, providing `ghost_step(maze, square, heading, rng) -> GhostMove(square, heading)`. The ghost's state lives where WI-7 put it, as `GameState.ghost` and `GameState.ghost_heading`, so WI-11 applies the policy with `dataclasses.replace`. This was proposed to Dev B on #127 and #129.

## WI-10: Frame composer: merged

- **PR:** #130, branch `r8/wi-10-frame-composer`, cut from `origin/main` at `0680c8c`. `main` was merged in at `b1adc97` (WI-7 and AMEND-1) with no conflicts.
- **Merged:** 04:15:15Z as `ebffe07`. **Risk:** MEDIUM, the floor, not raised. No human gate.
- **Copilot:** two threads, both fixed at `d3f3dab`. The A1 tests now cover the height and short-maze branches, and the docstring qualifies the rule about blank roles.
- **Verifier:** round 1 `APPROVED` at `d3f3dab67102025315b1c4ef933aa1dd4f561c79`. C1–C10, A1 and A2 are REPRODUCED. Controls were `n/a` (new module). The verifier accepted the brief's reading of C9: blank cells in the status row take the status role, because C2 makes row 29 exactly WI-5's line. It noted that the lead may want to tighten C9's wording.
- **Built:** `terminal_game/presentation/frame_composer.py`, providing `compose(state)`, which returns 30 × 40 `(character, role)` cells. The specimen is reproduced with 0 differing cells. The composer reads WI-7's `GameState` duck-typed, and a seam test composes `new_game(...)`.

## Suite at the end of M2 for lane A

An export of `origin/main` at `ebffe07`, which includes lane B's WI-7 and WI-11: `.venv/bin/python -m pytest -q` gives **464 passed, 0 failed, 1 skipped**. `python -m tools.layer_check` passes, with shell 1, presentation 6, application 2, domain 6 and entry 1.
