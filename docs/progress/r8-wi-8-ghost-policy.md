03:39:24Z  WI-8 START   WI-8 ghost movement policy (MEDIUM), Dev A, branch r8/wi-8-ghost-policy from origin/main 0680c8c, carrying r8/m1-dev-a-completion c642bee per the conductor's ruling
03:39:24Z  WI-8 NOTE    helper scripts moved from the shared scratchpad into the worktree (.venv/dev-a-tools, ignored), per the conductor's new rule
03:42:22Z  WI-8 READ    lane B's WI-7 (PR 127, worktree): GameState(maze, player, ghost: Square, dots, score, outcome, ghost_heading: Optional[Square]); outcome values match status_line's
03:42:22Z  WI-8 DECIDE  ghost state -> adopt B's shape: the ghost's square and heading stay two GameState fields; the policy is ghost_step(maze, square, heading, rng) -> GhostMove(square, heading), a NamedTuple WI-11 unpacks into replace(state, ghost=..., ghost_heading=...), because B has already built GameState that way and the plan's WI-8 outcome names exactly those inputs
03:44:00Z  WI-8 VERIFY  ghost_probe -> C1-C8 HOLD: T-junction 49.8/50.2 percent, 1,000,000 moves over 1,000 mazes with 0 bad steps, 0 onto walls, 0 unmoved; 1000x1000 run costs about 2.4 s
03:44:00Z  WI-8 RISK    WI-8 MEDIUM, because it is the plan floor; not raised: pure domain
03:44:00Z  WI-8 CLAIM   C1-C8 executable -- evidence/WI-8/ghost_probe.py and pytest -v tests/test_ghost.py -k cN; A1 added (GhostStuck, heading check); controls n/a: new module
03:44:00Z  WI-8 TEST    382 passed, 0 failed, 1 skipped
