# WI-8: Ghost movement policy

Risk: MEDIUM
The plan's floor, not raised. WI-11 and WI-12 build on this policy. It is pure domain code that opens no window and touches no state it is not handed.

Lane A, Dev A. Branch `r8/wi-8-ghost-policy`, cut from `origin/main` at `0680c8c` (WI-2 merged). Not stacked. It also carries `r8/m1-dev-a-completion` (`c642bee`), lane A's M1 completion record and post-merge log lines, on the conductor's ruling.

**What it adds:** `terminal_game/domain/ghost.py`.

- `ghost_step(maze, square, heading, rng)` returns `GhostMove(square, heading)`.
- `heading` is the `(dcol, drow)` of the ghost's last move, one of `terminal_game.domain.maze.DIRECTIONS` (the module constant), or `None` before its first move.
- `rng` is anything with `choice`, such as `random.Random(seed)`.
- A ghost whose square has no open neighbour raises `GhostStuck` instead of standing still.

## Where the ghost's state lives (plan §5.2, for Dev B)

**Proposal: keep lane B's shape.** WI-7 (PR #127) already keeps the ghost as two `GameState` fields, `ghost: Square` and `ghost_heading: Optional[Square]`, with `ghost_heading=None` at setup. The policy takes exactly those two values and returns the next pair. So WI-11 applies it in two lines, then decides the collision:

```python
move = ghost_step(state.maze, state.ghost, state.ghost_heading, rng)
state = replace(state, ghost=move.square, ghost_heading=move.heading)
```

The random source is whatever WI-12 hands the resolver. The policy draws from it only when it has a real choice to make: a first move with more than one open neighbour, or a blocked square with more than one way on besides back (WI-8/A2). So the same maze, state and random sequence always give the same ghost path (WI-12/C9). No new state type is introduced. If Dev B would rather have a `Ghost` value inside `GameState`, it is a small change here, and I will make it.

## Claims

Commands run from the repository root with the §1.2 environment. `-v` without `-q` prints each test's name.

**Controls:** every claim is `n/a`. `terminal_game/domain/ghost.py` is a new module, and the base (`0680c8c`) has no ghost policy of any kind: no module, function or behaviour that any claim could be run against. A control there could only fail on `ImportError`.

| Claim | Statement (word for word from the plan) | Evidence | What the output shows | Control |
|---|---|---|---|---|
| **WI-8/C1** | While the square ahead in its current heading is corridor, the ghost's next square is that square, at junctions as well as along corridors. | Executable: `.venv/bin/python evidence/WI-8/ghost_probe.py`, and `.venv/bin/python -m pytest -v tests/test_ghost.py -k c1` | The probe draws a crossroads and reports `WI-8/C1 HOLDS`: straight through the junction for all four headings under 200 seeds each, and along a corridor heading east `[(2, 1), (3, 1), … (7, 1)]`. 5 PASSED. | n/a: new module |
| **WI-8/C2** | When the square ahead is wall, the ghost moves to one of its other open neighbours, excluding the square it came from, chosen at random: over 10,000 trials at a square with two such exits, each is chosen at least 40% of the time. | Executable: same probe, and `-k c2` | The probe draws the T-junction: `WI-8/C2 HOLDS: west (1, 1) 49.8%, east (3, 1) 50.2%, back (2, 2) 0 times`. 3 PASSED: the 10,000-trial count (each ≥ 4,000); the new heading is the direction it turned; and at an L-bend it takes the one other way. | n/a: new module |
| **WI-8/C3** | The ghost turns back the way it came only when no other way is open, shown on a hand-built maze with a dead end. | Executable: same probe, and `-k c3` | The probe draws a dead-end corridor. The path is `(2,1) east, (3,1) east, (4,1) east, (3,1) west, (2,1) west, (1,1) west`: it bounces off the end and walks back. At the L-bend it never turns back, over 200 seeds. 2 PASSED. | n/a: new module |
| **WI-8/C4** | The ghost's next square never depends on where the player is: for the same maze, ghost square, heading and random sequence, it is the same wherever the player stands. | Executable: same probe, and `-k c4` | Two 500-move games on one generated maze, with one ghost random sequence and players on different routes (ending at `(7, 3)` and `(13, 11)`): `ghost paths identical: True`. The policy's parameters are `['maze', 'square', 'heading', 'rng']`, so there is nothing through which the player could reach it. 2 PASSED. | n/a: new module |
| **WI-8/C5** | The ghost only ever moves exactly one square north, south, east or west, and never onto a wall. | Executable: same probe, and `-k "c5 or c8"` | `WI-8/C5 HOLDS: 1000000 moves: 0 not one square N/S/E/W, 0 onto a wall` (1,000 generated mazes × 1,000 moves). The test asserts each step, square and returned heading. | n/a: new module |
| **WI-8/C6** | On its first move, having no heading yet, the ghost moves to one of its open neighbours. | Executable: same probe, and `-k c6` | From a crossroads with no heading, 400 seeds' first moves went to `{(1, 2): 95, (2, 1): 109, (2, 3): 100, (3, 2): 96}`: always an open neighbour, and each of the four is reachable. 2 PASSED, the second showing that the returned heading is the direction moved. | n/a: new module |
| **WI-8/C7** | A ghost move never changes the dots: every dot present before it is present after it, including the dot on the square the ghost moves onto. | Executable: same probe, and `-k c7` | The ghost made 2,000 moves over a maze with a dot on every corridor square but the start, landing on a dotted square each time: `dots before 261, after 261, identical: True`. This holds by construction: the policy is not handed the dots and returns only `GhostMove(square, heading)`. Both tests assert that. Applying the move to `GameState` without touching `dots` is WI-11's seam, which WI-11 should test. | n/a: new module |
| **WI-8/C8** | Over 1,000 generated mazes and 1,000 moves in each, the ghost moves on every move and is never stuck. | Executable: same probe, and `-k "c5 or c8"` | `WI-8/C8 HOLDS: 1000000 moves, 0 where the ghost did not move, none raised`. | n/a: new module |
| **WI-8/A1** | A ghost whose square has no open neighbour at all raises `GhostStuck` naming the square, instead of silently staying put, and a heading that is not one of the four single steps (or `None`) is refused with `ValueError`. | Executable: `.venv/bin/python -m pytest -v tests/test_ghost.py -k "no_open or not_a_single"` | 2 PASSED: `GhostStuck` names `(1, 1)` for a walled-in square, and heading `(1, 1)` is refused. | n/a: new module |
| **WI-8/A2** | The policy draws from the random source only at a real choice (a first move with more than one open neighbour, or a blocked square with more than one way on besides back). Going straight on, taking the single way at a bend, turning back at a dead end, or a first move with one open neighbour leaves the source exactly as it was, so a bend never shifts a later random decision in a shared sequence. | Executable: `.venv/bin/python -m pytest -v tests/test_ghost.py -k a2` | 6 PASSED. `random.Random(11).getstate()` is identical before and after a step in each of the four no-choice situations, and it differs after a step at the T-junction and at a first move from a crossroads. | n/a: new module |

Suite at the head: `.venv/bin/python -m pytest -q` gives **388 passed, 1 skipped**. The C5/C8 test takes about 2.4 s. `.venv/bin/python -m tools.layer_check` passes with `domain 4`.

## Diff map

```
terminal_game/domain/ghost.py:1-35    docstring (the rules, and how WI-11 applies them) -> WI-8/C1-C7
terminal_game/domain/ghost.py:37-60   Chooser protocol, GhostMove, GhostStuck -> WI-8/C4, C7 (what goes in and out), WI-8/A1
terminal_game/domain/ghost.py:63-64   _step -> WI-8/C1, C3
terminal_game/domain/ghost.py:67-73   ghost_step: heading check, no-exit refusal -> WI-8/A1
terminal_game/domain/ghost.py:75-76   first move -> WI-8/C6, A2
terminal_game/domain/ghost.py:78-80   straight on -> WI-8/C1
terminal_game/domain/ghost.py:81-84   blocked: other exits at random, else back -> WI-8/C2, C3, A2
terminal_game/domain/ghost.py:85      the returned move and heading -> WI-8/C5
terminal_game/domain/ghost.py:88-94   _pick: draw only at a real choice -> WI-8/A2 (and C2, C6)
tests/test_ghost.py (new)             -> evidence for C1-C8, A1, A2
evidence/WI-8/ghost_probe.py (new)    -> evidence for C1-C8
docs/prs/PR-WI-8-ghost-policy.md      -> this brief
docs/progress/r8-wi-8-ghost-policy.md -> progress log
docs/completions/COMPLETION-M1-DEV-A.md                                   -> M1 completion record (mechanical)
docs/progress/r8-wi-4-wall-glyphs.md, r8-wi-5-status-line.md, r8-wi-6-input-translation.md -> M1 completion record (mechanical): post-merge log lines
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
