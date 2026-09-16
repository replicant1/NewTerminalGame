04:43:58Z  START   WI-6 The opening position. DEV-A, branch r6/wi-6-opening-position off main at d07a5f7.
04:44:36Z  READ    plan section 8 WI-6 and requirements START-1..5, SCORE-5, GAME-1, GAME-2.
04:44:36Z  VERIFY  start-square ties measured over 200 generated mazes: the player lands on (9,14) in 115 of 200 and on (9,13) in the other 85 (a 2-way tie broken row-major). The ghost is ALWAYS a corner: a 4-way tie among all four corners when the player is at (9,14), a 2-way tie between the bottom two when the player is at (9,13).
04:44:36Z  WEIGH   how to break a tie for the start squares : deterministic row-major vs drawing from a handed random source.
04:44:36Z  DECIDE  tie-break -> deterministic, first in row-major order, because WI-6 s outcome text pointedly does not hand this item a random source where WI-5 and WI-7 both do. Consequence measured above: the ghost always starts in the left-hand column, at (1,1) or (1,27). Flagging it rather than inventing a requirement.
04:44:36Z  PLAN    three modules: dot_field.py (START-3, SCORE-1, SCORE-3), game_state.py (Score, Outcome, GameState), opening_position.py (START-1, START-2, START-4).
04:46:25Z  TEST    221 passed, 0 failed, 0 skipped  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py", 3.46s). 54 of them are WI-6 s.
04:46:25Z  NOTE    WI-6 s first run took the suite from 3.3s to 8.5s because six sweeps each regenerated 200 mazes. Added tests/domain/generated_mazes.py, a shared cache deliberately not named test_*, and the suite is back to 3.46s with 54 more tests in it.
04:46:25Z  VERIFY  the finished opening_position reproduces the measurement taken before it was written: player (9,14) x115 and (9,13) x85; ghost (1,1) x115 and (1,27) x85; dots 259 to 271, mean 264.5, always one fewer than the corridor count.
04:47:50Z  MERGE   origin/main brought onto the branch: WI-2 and WI-2a from DEV-B landed since. Clean, no conflict.
04:47:50Z  NOTE    WI-2 flattened DEV-C s tests/shell into tests/, leaving tests/domain as the only nested directory. Flattened WI-5 and WI-6 s tests to match, so the convention now has no exceptions. Second move for these files; the churn itself is worth reporting.
04:47:50Z  TEST    282 passed, 0 failed, 0 skipped  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py", 3.7s)
04:48:47Z  MERGE   PR #32 merged into main as edcb5a3; origin/main brought back onto the branch.
04:48:47Z  TEST    282 passed, 0 failed, 0 skipped on main at edcb5a3  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py")
04:48:47Z  ASK     should the ghost s start square be drawn at random from the tied furthest corners? As built it is deterministic and the ghost always starts in the left-hand column. Measured in docs/findings/WI-6-start-squares.md.
04:48:47Z  ASSUME  proceeding with the deterministic row-major tie-break, on which nothing downstream depends except what a player sees; the change is confined to ghost_start_square.
04:48:47Z  DONE    WI-6 r6/wi-6-opening-position edcb5a3
