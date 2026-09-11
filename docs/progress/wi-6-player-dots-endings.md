02:28:31Z  START   WI-6 player movement, dots, score, endings — branch wi-6-player-dots-endings cut from origin/main
02:28:56Z  READ    plan §1,2.1-2.8, §5 WI-6/WI-7, §6 round-4, §11 traceability; requirements CTRL/SCORE/END/GAME-2; rules.py as WI-5 left it
02:29:41Z  PLAN    move_player(state, direction) into termgame/rules.py — END-5 guard, CTRL-3 identity return, SCORE-1..3, then CAUGHT-before-CLEARED (END-3); tests in tests/test_rules_player.py on hand-written boards
02:29:59Z  TEST    baseline on branch point: 479 passed, 0 failed, 2 skipped
