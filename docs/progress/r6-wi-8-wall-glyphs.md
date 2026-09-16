04:54:41Z  WI-8 START   DEV-C taking over lane; work item WI-8 wall glyphs, branch r6/wi-8-wall-glyphs, non-local mode
04:54:55Z  WI-8 READ    docs/FUNCTIONAL_REQUIREMENTS.md; SCRN-3 is my requirement, specimen picture is the reference
04:55:07Z  WI-8 READ    terminal_game/domain/maze.py -- Maze.wall_neighbours() already exists, DEV-A wrote it for exactly this; Maze.from_text is the ASCII helper, no new one needed
04:56:14Z  WI-8 NOTE    branch r6/wi-8-wall-glyphs cut from origin/main 6eb731e (WI-11 landed); git ls-remote r6/wi-8-* empty, clear to push
04:56:17Z  WI-8 TEST    349 passed, 0 failed, 0 skipped -- baseline, /usr/bin/python3 -m unittest discover -t . -s . -p test_*.py
04:56:20Z  WI-8 VERIFY  inverted the specimen picture to a 19x29 wall grid and read every glyph back -> 15 of the 16 neighbour combinations appear, all agreeing with the standard double-line set; NESW crossing absent, as the plan said
04:56:23Z  WI-8 VERIFY  connector column 2c+1 across all 29x18 positions -> U+2550 exactly when squares c and c+1 are both wall, and blank or an actor overlay otherwise; no counterexample
04:56:59Z  WI-8 DRAFT   terminal_game/presentation/wall_glyphs.py -- 16-entry table, wall_glyph_at, connector_glyph_east_of, wall_layer(_text); no dot and no actor motif declared anywhere in it
04:58:06Z  WI-8 VERIFY  census over 200 generated mazes -> all 12 distinct glyphs occur; the crossing U+256C appears 61 times in 55 of the 200, so the one entry the specimen lacks is reachable in play, not theoretical; lone block U+25A0 558 times in 189 of 200; first crossing at seed 1
04:58:24Z  WI-8 TEST    394 passed, 0 failed, 0 skipped -- /usr/bin/python3 -m unittest discover -t . -s . -p test_*.py ; 45 new (349 baseline)
04:59:12Z  WI-8 COMMIT  db615a0 WI-8: the wall glyphs and the connector rule -- pushed to origin, r6/wi-8-wall-glyphs
04:59:15Z  WI-8 DRAFT   docs/prs/PR-WI-8-wall-glyphs.md and docs/findings/WI-8-glyph-census.md; both state the stroke-joining question is open and WI-16's, and neither claims it verified
04:59:23Z  WI-8 NOTE    draft PR #43 opened -- https://github.com/replicant1/NewTerminalGame/pull/43 , base main
05:00:03Z  WI-8 DECIDE  dropped two tests that re-asserted behaviour test_maze.py already owns (off-grid neighbours at the four corners, and a weaker only-two-colours check) -> 43 new instead of 45, because the border ring and the colour rule are each now asserted once, at the level that owns them
05:00:06Z  WI-8 TEST    392 passed, 0 failed, 0 skipped -- /usr/bin/python3 -m unittest discover -t . -s . -p test_*.py ; 43 new over the 349 baseline
05:00:09Z  WI-8 VERIFY  tkinter._default_root is None after the whole 392-test suite -> True; no Tk interpreter created, property preserved
05:00:59Z  WI-8 COMMIT  50add73 WI-8: the PR summary, the glyph census, and two tests removed as duplicates -- pushed
05:01:44Z  WI-8 READ    amendments 2 and 3 (landed on main while I worked). WI-8's own entry is unchanged. Three things bear on me: WI-8 is now on the critical path to WI-18 via WI-12; nothing that is not a test may depend on test code; tests/specimen.py is to move out of tests/ at DEV-B's call
05:01:47Z  WI-8 TEST    417 passed, 0 failed, 0 skipped after merging origin/main 6cee5c9 (WI-9, WI-9a, amendments) -- clean merge, no conflict; 43 of those are WI-8's
