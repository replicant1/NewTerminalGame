# WI-12 — wire the whole game

Branch `wi-12-wire-the-game`. DEV-A, lane A, M3, local mode.

```
05:50:15Z START   WI-12 wire the whole game and play it. The loop drives the real
05:50:15Z         domain, asks the real frame builder for a frame, presents it
05:50:15Z         through the real screen port, in the window the real launcher
05:50:15Z         created, and the launcher closes that window when the game exits.
05:50:15Z NOTE    WI-12 integration, recorded as required. Re-read main at the
05:50:15Z         moment of branching rather than carrying a sha: main is at
05:50:15Z         16b4dac, NOT ee0b954 as I last reported nor 8c4e2ce as I was
05:50:15Z         told. Nine branches have landed and my wi-10-rules-outcome and
05:50:15Z         wi-6-status-line are among them. Cut wi-12-wire-the-game from
05:50:15Z         wi-11-game-loop at 41108ed, merged main 16b4dac -- clean, no
05:50:15Z         conflicts. Suite 620 (575 on main + 45 from WI-11).
05:50:15Z MEASURE WI-12 checked the four files I need to change against DEV-B's
05:50:15Z         live wi-13-launcher-robustness branch before touching any of
05:50:15Z         them, by blob id rather than by asking. launcher/game.py
05:50:15Z         88870dd, tests/test_game_command.py fbd8747,
05:50:15Z         terminalgame/game_main.py e64b3f9 -- all byte-identical on both
05:50:15Z         branches. DEV-B has touched none of them, so changing the
05:50:15Z         launcher seam here cannot collide with WI-13.
05:50:15Z DECIDE  WI-12 --hold goes. It was M0 scaffolding and the technical lead
05:50:15Z         said so at the time; the real game runs until q, which is A1 and
05:50:15Z         END-6. That means changing BOTH game_main (stop accepting it)
05:50:15Z         and launcher/game.py (stop passing it) in one commit, because
05:50:15Z         either alone leaves the launcher starting a game with an
05:50:15Z         argument it will reject.
05:50:15Z DECIDE  WI-12 one seed names the whole game: a single random.Random is
05:50:15Z         made from --seed, handed to new_game_with for the maze and the
05:50:15Z         placements AND to the loop for the ghost. Without that the ghost
05:50:15Z         would draw on a different source and a seed would only half
05:50:15Z         reproduce a game, which is exactly what WI-14a needs it for.
05:50:15Z NOTE    WI-12 the camouflage case I was told to guard: compose(state,
05:50:15Z         status_line=None) leaves row 29 blank and composes perfectly, so
05:50:15Z         a wiring omission is a silent STAT-1 violation that passes every
05:50:15Z         WI-5b test. The wired game must be asserted to produce a NON-
05:50:15Z         BLANK row 29 carrying the real score.
05:50:15Z PLAN    WI-12 rewrite terminalgame/game_main.py to the real game; change
05:50:15Z         the launcher seam; rewrite tests/test_game_main.py off the
05:50:15Z         skeleton; add tests/test_wired_game.py for the end-to-end plays;
05:50:15Z         pay the two layering debts (the launcher half over ast, and the
05:50:15Z         Application purity class I deferred from WI-11); then one real
05:50:15Z         run in a real window, with a census either side.
06:03:25Z NOTE    WI-12 the ast scanner I wrote for the launcher debt had a bug
06:03:25Z         and its own test found it: relative imports were hardcoded to
06:03:25Z         "launcher", so the GAME's own `from .screen import port` was
06:03:25Z         reported as importing the launcher and game_main.py and
06:03:25Z         curses_adapter.py came back as offenders. It now takes the
06:03:25Z         package to resolve relative imports within and refuses to guess
06:03:25Z         one -- left out it reports ".", which belongs to nothing. Worth
06:03:25Z         recording because the fault was in the GUARD, not the code it
06:03:25Z         guards, and that is the kind that gets "fixed" by loosening it.
06:03:25Z TEST    648 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
06:03:25Z COMMIT  de576a2 WI-12: wire the whole game
06:04:35Z MEASURE WI-12 the real run. ONE window opened (id 7891), ONE closed;
06:04:35Z         visible census ['7104'] before and after. Opened +0.93s, game
06:04:35Z         running +0.95s, q sent +4.05s, game gone +4.17s (0.12s later),
06:04:35Z         reap closed=True, nothing leaked, 4.50s total. Read the live
06:04:35Z         tab: the whole maze with joined-up walls, a dot on every
06:04:35Z         corridor square, the player near the middle, the ghost most of
06:04:35Z         the way across after ~20 ticks WITH NOTHING PRESSED -- GHOST-1
06:04:35Z         and START-5 in one picture -- and the status row NOT BLANK,
06:04:35Z         reading " score 0    arrows, q quits" with the leading space.
06:04:35Z NOTE    WI-12 reproduced WI-1's measurement without looking for it:
06:04:35Z         asked for y=-1352, landed at y=30. set position is a request,
06:04:35Z         not an instruction, and it is only visible because the launcher
06:04:35Z         reads the position back instead of believing the move.
06:04:35Z NOTE    WI-12 windows: 1 opened, 1 closed. The failure path was armed
06:04:35Z         and not needed: had q not ended it, the harness would have
06:04:35Z         killed the CHILD by pid, never the window -- a dead child lets
06:04:35Z         the window fall idle and close cleanly, where closing a busy
06:04:35Z         one raises the sheet that blocks the cleanup itself.
06:04:35Z DONE    WI-12 wi-12-wire-the-game de576a2 (docs commit follows)
```
