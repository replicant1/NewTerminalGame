02:47:50Z  START   WI-9 wire the real game together — branch wi-9-wire-the-game, base c8defe7 (origin/main)
02:48:02Z  READ    WI-9 docs/IMPLEMENTATION_PLAN.md §5 WI-9 — brief, tests-must-establish, done-when
02:48:12Z  READ    WI-9 plan §2 ground rules and §3/§4 — pinned interpreter, flat tests, dependency rule, window-safety
02:48:20Z  READ    WI-9 termgame/loop.py, standins.py, ticker.py — the three seams to rewire and resolve_render to delete
02:48:36Z  READ    WI-9 termgame/rules.py, view.py, `Terminal Game` — rules signatures are drop-in for the stand-ins; the child calls loop.run_game and needs no change
02:48:46Z  READ    WI-9 standins is referenced from tests/test_loop.py, test_curses_pty.py, test_screen_adapter.py — no test_standins.py exists; the deletions are surgical, not a whole file of tests
02:49:31Z  TEST    567 passed, 0 failed, 2 skipped  (baseline on c8defe7, before any WI-9 change)
02:49:53Z  READ    WI-9 docs/FUNCTIONAL_REQUIREMENTS.md in full — 49 codes; WI-9 is the item that makes GAME-1/2, START-5, CTRL-1..5, GHOST-1, END-4/5/6, WIN-5 true of the running program
02:51:12Z  ASK     WI-9 A1 — does WIN-5 mean the window vanishes on the final frame, or when the player presses q? Still with the user.
02:51:12Z  ASSUME  WI-9 the architect's reading: the last picture stays (END-5), q exits the process (END-6), the supervisor closes the window then (WIN-5). Not a ruling. Depends on it: run_loop returning only on quit, run_game returning 0 only after that, and the END-5/END-6 tests I am about to write. Cheap to flip — WI-11 owns the change and it lives in window.py, not here.
02:51:12Z  PLAN    WI-9 delete termgame/standins.py and loop.resolve_render; run_game builds rules.new_game(random.Random()) and drives run_loop with view.render, rules.move_player, rules.move_ghost; add tests/test_scripted_game.py — a scripted win, two scripted losses (player walks in, ghost walks in), END-5/END-6/STAT-3 after the ending, and MAZE-4 end to end through run_game.
02:54:17Z  TEST    566 passed, 0 failed, 2 skipped  (the wiring in; the scripted-game file is not written yet)
02:54:17Z  NOTE    WI-9 arithmetic so far: 567 -> 566. -5 for loop.resolve_render's fake-lookup tests (the lookup is gone), -1 for a screen-adapter test that had become a duplicate of an existing theme test, +3 new (resolve_render absent, standins unimportable, and two new real-game assertions on the pty run: outcome and the real status line). 567 - 5 - 1 + 3 = 564... the pty class also gained one; see the PR body for the exact ledger.
