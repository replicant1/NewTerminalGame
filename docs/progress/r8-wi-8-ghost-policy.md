03:39:24Z  WI-8 START   WI-8 ghost movement policy (MEDIUM), Dev A, branch r8/wi-8-ghost-policy from origin/main 0680c8c, carrying r8/m1-dev-a-completion c642bee per the conductor's ruling
03:39:24Z  WI-8 NOTE    helper scripts moved from the shared scratchpad into the worktree (.venv/dev-a-tools, ignored), per the conductor's new rule
03:42:22Z  WI-8 READ    lane B's WI-7 (PR 127, worktree): GameState(maze, player, ghost: Square, dots, score, outcome, ghost_heading: Optional[Square]); outcome values match status_line's
03:42:22Z  WI-8 DECIDE  ghost state -> adopt B's shape: the ghost's square and heading stay two GameState fields; the policy is ghost_step(maze, square, heading, rng) -> GhostMove(square, heading), a NamedTuple WI-11 unpacks into replace(state, ghost=..., ghost_heading=...), because B has already built GameState that way and the plan's WI-8 outcome names exactly those inputs
03:44:00Z  WI-8 VERIFY  ghost_probe -> C1-C8 HOLD: T-junction 49.8/50.2 percent, 1,000,000 moves over 1,000 mazes with 0 bad steps, 0 onto walls, 0 unmoved; 1000x1000 run costs about 2.4 s
03:44:00Z  WI-8 RISK    WI-8 MEDIUM, because it is the plan floor; not raised: pure domain
03:44:00Z  WI-8 CLAIM   C1-C8 executable -- evidence/WI-8/ghost_probe.py and pytest -v tests/test_ghost.py -k cN; A1 added (GhostStuck, heading check); controls n/a: new module
03:44:00Z  WI-8 TEST    382 passed, 0 failed, 1 skipped
03:44:14Z  WI-8 COMMIT  0cd40aa WI-8: ghost movement policy over the ghost's square and heading
03:44:14Z  WI-8 NOTE    draft PR opened; posting the ghost-state proposal on WI-7's PR 127 for Dev B; marking ready
03:49:16Z  WI-8 REVIEW  Copilot on PR 129: 1 thread (a single-option bend still consumed rng.choice), valid; fixed with _pick drawing only at a real choice; A2 added; brief DIRECTIONS reference made explicit
03:49:16Z  WI-8 TEST    388 passed, 0 failed, 1 skipped; ghost_probe 8 of 8 hold
03:49:16Z  WI-8 REVIEW  requested WI-8 round 1 (head is the commit carrying this line)
03:56:09Z  WI-8 REVIEW  APPROVED round 1 @41ef09c8a38c3d0dbb3657c7458c1669ee6c049b by newterminalgame-code-reviewer[bot]; no HUMAN-GATE; controls n/a accepted
03:56:09Z  WI-8 MERGE   PR 129 r8/wi-8-ghost-policy merged 03:55:45Z as c1d6be4 (carried the M1 completion record)
03:56:10Z  WI-8 TEST    411 passed, 0 failed, 1 skipped on an export of origin/main c1d6be4; layer check PASS, domain 6
03:56:10Z  WI-8 DONE    WI-8 r8/wi-8-ghost-policy 41ef09c8a38c3d0dbb3657c7458c1669ee6c049b
