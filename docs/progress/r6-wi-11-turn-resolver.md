04:50:18Z  START   WI-11 The turn resolver. DEV-A. Deciding the base: WI-7 is PR #33, open and out of draft but not merged.
04:51:17Z  DECIDE  base -> stacked on r6/wi-7-ghost-policy, because PR #33 is out of draft but not merged and DEV-A holds the critical path. WI-7 s merge base is edcb5a3, my own WI-6 merge, so the stack already contains everything WI-11 needs.
04:51:17Z  READ    DEV-B s WI-7: next_step(maze, square, heading, random_source) -> GhostStep(direction, square), heading Optional. Their comment on PR #32 asks me to decide where the heading is carried and recommends putting it in GameState.
04:51:17Z  DECIDE  ghost heading -> GameState gains ghost_heading: Optional[Direction], as DEV-B recommended, because a GameState that cannot say which way the ghost was going is not the whole state and WI-19 has to rebuild a game from one.
04:51:17Z  DECIDE  END-3 -> make it structural twice over: the step order lives in one visible list, AND an outcome once decided cannot be replaced, so the win test cannot overwrite a collision however the code is later rearranged. No mutation test, which is prohibited.
04:52:54Z  PLAN    terminal_game/domain/turn_resolver.py with resolve_move and resolve_tick, each opening with its step order written out; GameState gains ghost_heading.
04:52:54Z  VERIFY  END-3 case run by hand: one dot left, on the ghost s square, player adjacent, score 6. resolve_move EAST gives outcome CAUGHT, score 7, dots 0 -- so the winning condition really did hold in the same turn and the collision took precedence.
04:52:54Z  DECIDE  what happens to the dot on the losing turn -> it is still eaten and still scores, because the plan s step order puts eat after collision rather than instead of it. Pinned in a test and flagged in the PR as a judgement call.
04:52:54Z  TEST    330 passed, 0 failed, 0 skipped  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py", 3.74s). 25 of them are WI-11 s.
04:53:32Z  COMMIT  e70d57e WI-11: the turn resolver, with the step order in one readable place
04:53:32Z  COMMIT  87e58d1 WI-11: PR summary
04:53:32Z  VERIFY  draft PR #39 opened with --base r6/wi-7-ghost-policy, stacked on DEV-B s branch. Told DEV-B on PR #33 that I will retarget to main as soon as they merge.
04:54:18Z  NOTE    WI-7 merged while PR #39 was in draft. Retargeted #39 to main and merged origin/main onto the branch: clean, no conflict. No merge-order constraint remains.
04:54:18Z  TEST    349 passed, 0 failed, 0 skipped with origin/main merged in  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py", 3.72s)
04:55:10Z  MERGE   PR #39 merged into main as 7eb6ff0; origin/main brought back onto the branch.
04:55:10Z  TEST    349 passed, 0 failed, 0 skipped on main at 7eb6ff0  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py")
04:55:10Z  ASK     on the losing turn, should the dot the player walked onto still be eaten and still score? As built it is: outcome CAUGHT, score 7 rather than 6.
04:55:10Z  ASSUME  proceeding with the dot eaten, because the plan s step order puts eat after collision rather than instead of it. One line in resolve_move if the other reading is wanted; nothing downstream depends on it but the number on the CAUGHT status line.
04:55:10Z  DONE    WI-11 r6/wi-11-turn-resolver 7eb6ff0
