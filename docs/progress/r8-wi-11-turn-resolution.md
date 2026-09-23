03:53:09Z  START   WI-11 turn resolution, Dev B, branch r8/wi-11-turn-resolution from origin/main b1adc97
03:53:50Z  READ    WI-11 PR #129 (WI-8, Dev A): ghost_step(maze, square, heading, rng) -> GhostMove(square, heading); raises GhostStuck; proposes keeping ghost and ghost_heading in GameState
03:53:50Z  DECIDE  WI-11 ghost-state boundary -> agreed on #129: GameState.ghost + ghost_heading, applied via ghost_step then replace, then collision; GhostStuck propagates
03:54:18Z  NOTE    WI-11 merged e0768bf (WI-7 completion record) as d5d22b0; merged origin/r8/wi-8-ghost-policy (41ef09c) as 811b378 to stack on WI-8; PR will target r8/wi-8-ghost-policy until #129 merges
03:54:18Z  READ    WI-11 plan §4 WI-11 C1-C11, §1.6 END-3 note, §1.8 Q5; terminal_game/domain/ghost.py (WI-8); presentation/input_translation.py (WI-6 intents are strings)
03:54:18Z  PLAN    WI-11 terminal_game/application/turn_resolution.py: move_player(state, direction) and step_ghost(state, rng), the rules in one fixed order, returning new GameStates
03:54:18Z  DECIDE  WI-11 player moves arrive as (dcol, drow) from DIRECTIONS, not WI-6 intent strings, because mapping keys to directions is session control (WI-12) and the resolver stays in domain terms
03:54:18Z  DECIDE  WI-11 order -> player: decided? wall? then move, collision, eat, win; ghost: decided? then policy, collision (architecture F3/C6), all in one module
03:54:18Z  DECIDE  WI-11 once decided, both functions return the state unchanged (A claim), because a resolver that never plays on past an ending is safer than relying on WI-12 alone
03:56:27Z  DRAFT   WI-11 terminal_game/application/turn_resolution.py; tests/test_turn_resolution.py (C1-C11, A1-A3); evidence/WI-11/turn_claims.py
03:56:27Z  VERIFY  WI-11 harness ALL PASS: C5 0 score drops over 1000x1000, 28421 dots eaten, 787 games lost; C11 509273 squares changed, 0 off-grid/wall/jumps
03:56:27Z  TEST    442 passed, 0 failed, 1 skipped; layer_check PASS (application 2)
03:56:27Z  RISK    WI-11 MEDIUM, because it is the plan's floor; pure application logic, but END-3 order-sensitivity and WI-12 build on it
03:58:00Z  COMMIT  3b710af WI-11: turn resolution in one fixed order, with tests and evidence harness
03:58:00Z  NOTE    WI-11 #129 merged before I opened the PR, so no stacking: merged origin/main c1d6be4; ghost.py identical to 41ef09c; PR targets main
03:58:00Z  TEST    442 passed, 0 failed, 1 skipped (after merging main)
03:58:00Z  CLAIM   WI-11/C1-C11, A1-A3 executable — tests/test_turn_resolution.py -k <id>_; H evidence/WI-11/turn_claims.py for C2, C5, C8-C11
03:58:00Z  DRAFT   WI-11 docs/prs/PR-WI-11-turn-resolution.md
