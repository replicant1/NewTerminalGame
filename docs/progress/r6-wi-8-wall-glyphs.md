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
05:02:48Z  WI-8 COMMIT  ecc73a2 WI-8: merge main, and answer amendment 2's real-medium question -- pushed, PR #43 body updated and marked ready
05:03:31Z  WI-8 MERGE   PR #43 merged to main as 7374aeb; then fetched and merged origin/main back (WI-13 had landed beside it) and re-ran the whole suite
05:03:39Z  WI-8 TEST    445 passed, 0 failed, 0 skipped on main at 7374aeb -- /usr/bin/python3 -m unittest discover -t . -s . -p test_*.py ; what landed is green beside WI-13
05:03:49Z  WI-8 NOTE    announced for WI-12 per first-lander rule 4: wall_layer(maze) and wall_layer_text(maze) in terminal_game/presentation/wall_glyphs.py give the whole wall skeleton as frame cells, square c at index 2c and the connector at 2c+1, blanks elsewhere -- the frame composer need not name a single wall character
05:03:53Z  WI-8 NOTE    no query was added to the maze and DEV-A was not asked for one: Maze.wall_neighbours already returned exactly the frozenset this item needs, and its docstring says it was written for the border ring. No gh pr comment to DEV-A was needed.
05:03:56Z  WI-8 ASK     whether the strokes of adjacent double-line glyphs actually MEET on screen -- not measurable here, only an eye can settle it. Recorded as open in the module, the tests, the PR body and docs/findings/WI-8-glyph-census.md section 4; nowhere recorded as verified.
05:04:01Z  WI-8 ASSUME  proceeding on the measured geometry alone -- the 12 characters and the connector rule are chosen from what the specimen picture shows and what the generator produces, and nothing in the choice depends on whether the ink joins. If it does not join, the answer is a font or a size, not a different table: nothing in this branch changes. Affects WI-16 only.
05:04:08Z  WI-8 NOTE    no window was opened at any point in this work item -- zero windows, so nothing to reap; the item is pure Presentation and imports no toolkit
05:04:11Z  WI-8 DONE    WI-8 r6/wi-8-wall-glyphs 7374aeb -- merged as PR #43, main green at 445 passed 0 failed 0 skipped
