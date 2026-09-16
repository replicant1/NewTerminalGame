04:40:33Z  START   WI-5a One root package, not two. DEV-A follow-up after WI-5 and WI-1 landed different package names.
04:40:33Z  READ    the merged tree: terminal_game/ from WI-1 (DEV-B) and terminalgame/ from WI-5 (DEV-A) both present at main 34eba2c.
04:40:33Z  DECIDE  which spelling survives -> DEV-B s terminal_game/ with flat tests/, because WI-1 landed first, its package docstring already carries the layer rule and names domain, and conforming changes none of DEV-B s files so there is nothing to arbitrate.
04:40:33Z  VERIFY  WI-1 alone: /usr/bin/python3 -m unittest tests.test_frame -> Ran 45 tests, OK. 68 + 45 = 113, which is the whole suite.
04:40:33Z  TEST    113 passed, 0 failed, 0 skipped after the move  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py")
04:42:03Z  NOTE    WI-3 (DEV-C) merged while this branch was open and used terminal_game/shell plus a nested tests/shell. That settles both questions: terminal_game is 2 of 3 lanes for the package, and nested-by-layer is 2 of 3 for the tests.
04:42:03Z  DECIDE  test layout -> put WI-5 s tests back in tests/domain/ rather than flat, because WI-3 landed tests/shell/ and nested mirrors terminal_game/ directory for directory.
04:42:03Z  VERIFY  origin/main (with WI-1, WI-3, WI-5) merged onto the branch; only terminal_game/ remains, terminalgame/ is gone.
04:42:03Z  TEST    167 passed, 0 failed, 0 skipped  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"): 68 WI-5, 54 WI-3, 45 WI-1.
04:42:52Z  MERGE   PR #27 merged into main as fc238ae; origin/main brought back onto the branch.
04:42:52Z  TEST    167 passed, 0 failed, 0 skipped on main at fc238ae  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py")
04:42:52Z  NOTE    told DEV-B on their open PR #26 that terminal_game won, that none of their files moved, and what the maze query surface offers WI-7.
04:42:52Z  DONE    WI-5a r6/wi-5a-package-name fc238ae
