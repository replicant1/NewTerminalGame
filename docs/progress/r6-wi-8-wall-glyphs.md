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
