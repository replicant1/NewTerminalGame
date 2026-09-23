03:33:11Z  START   WI-7 game setup, Dev B, branch r8/wi-7-game-setup from origin/main 796aebe (main has moved past 86eca86: WI-4 and WI-5 landed)
03:33:54Z  NOTE    WI-7 merged 679b89d (WI-2 completion record) into the branch as 1aaa7f5, per the conductor's ruling; diff map will list it as mechanical
03:33:54Z  READ    WI-7 docs/IMPLEMENTATION_PLAN.md §4 WI-7 claims C1-C7, §1.8 Q6, §1.10 X5, §5.2 (A and B agree the game state WI-10 reads)
03:33:54Z  READ    WI-7 terminal_game/presentation/status_line.py (WI-5): outcome is PLAYING=None, LOST='lost', WON='won'
03:33:54Z  PLAN    WI-7 a frozen GameState in the domain (maze, player, ghost, ghost_heading, dots, score, outcome) and new_game(maze) that places player and ghost and lays the dots, with no randomness
03:33:54Z  DECIDE  WI-7 outcome values -> domain PLAYING=None, LOST='lost', WON='won', equal to WI-5's, because the composer can then hand state.outcome straight to status_text; a test pins the equality at the seam
03:33:54Z  DECIDE  WI-7 centre -> (width//2, height//2), which is (9, 14) on the 19 x 29 maze; distances compared as integer squared distances so ties are exact
03:33:54Z  DECIDE  WI-7 ties -> the first tied square in row-by-row order (corridor_squares order), for both player and ghost, because it is simple to state and deterministic
03:33:54Z  DECIDE  WI-7 ghost heading lives in GameState as ghost_heading, None at start, because WI-8's policy takes a heading and WI-11 must carry it between steps; stated as an A claim so the field is explained
03:33:54Z  DECIDE  WI-7 a maze with fewer than two corridor squares is refused with ValueError, because player and ghost could not start apart (C7)
03:35:51Z  DRAFT   WI-7 terminal_game/domain/game_state.py, game_setup.py; tests/test_game_setup.py (C1-C7, A1-A3), tests/test_game_state.py (A4)
03:35:51Z  TEST    208 passed, 0 failed, 1 skipped; layer_check PASS, domain 5
