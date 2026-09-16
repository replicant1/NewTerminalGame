WI-3a  START   04:42:00Z  DEV-C. Follow-up to WI-3 (merged as 1fa9490). WI-3 put its tests in tests/shell/; DEV-A's PR #27 states one convention for the tree with tests flat in tests/. Conforming.
WI-3a  READ    04:41:30Z  DEV-A's PR #27 body in full. It consolidates the root package onto terminal_game, which WI-3 already uses, so nothing of mine moves on that count. Its closing tree diagram says tests are flat.
WI-3a  DECIDE  04:42:10Z  tests/shell/ -> tests/, because flat is the incumbent, two of three developers already use it, and WI-10 (mine, M1) is the architecture guard that walks the whole tree and is better off with one convention.
WI-3a  NOTE    04:42:15Z  Settled with DEV-A directly on their PR, comment 5692146610, not through the conductor or the technical lead. Offered to go the other way instead if they would rather the tree were nested.
WI-3a  VERIFY  04:43:00Z  Move done with git mv, five files, plus tests/shell/__init__.py removed. The relative import of the recording double needed no change - both files moved up one package together.
WI-3a  TEST    04:43:54Z  228 passed, 0 failed, 0 skipped  [/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"]  -- the whole tree after merging origin/main, which by then carried WI-2 and WI-5a as well. Clean merge, no conflicts.
WI-3a  DONE    04:43:54Z  WI-3a  r6/wi-3a-tests-flat  merged as 4693693 (PR #30).
