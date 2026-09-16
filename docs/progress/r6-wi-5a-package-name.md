04:40:33Z  START   WI-5a One root package, not two. DEV-A follow-up after WI-5 and WI-1 landed different package names.
04:40:33Z  READ    the merged tree: terminal_game/ from WI-1 (DEV-B) and terminalgame/ from WI-5 (DEV-A) both present at main 34eba2c.
04:40:33Z  DECIDE  which spelling survives -> DEV-B s terminal_game/ with flat tests/, because WI-1 landed first, its package docstring already carries the layer rule and names domain, and conforming changes none of DEV-B s files so there is nothing to arbitrate.
04:40:33Z  VERIFY  WI-1 alone: /usr/bin/python3 -m unittest tests.test_frame -> Ran 45 tests, OK. 68 + 45 = 113, which is the whole suite.
04:40:33Z  TEST    113 passed, 0 failed, 0 skipped after the move  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py")
