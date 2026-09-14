# WI-11 — the game loop

Branch `wi-11-game-loop`. DEV-A, lane A, M2, local mode.

```
05:45:55Z START   WI-11 the game loop. GHOST-1, CTRL-1, CTRL-2, CTRL-4, CTRL-5,
05:45:55Z         START-5, END-5, END-6, SCRN-7.
05:45:55Z NOTE    WI-11 integration, recorded exactly as required. Cut
05:45:55Z         wi-11-game-loop from wi-6-status-line at a88d511. Merged
05:45:55Z         wi-9-ghost-policy at dee3312 into it -- clean, no conflicts,
05:45:55Z         5 files added, suite 435. Then merged main.
05:45:55Z MEASURE WI-11 main is NOT where I was told. I was told c4171fb, then
05:45:55Z         corrected to 8c4e2ce with "no queued branch has landed; the
05:45:55Z         lockout is unchanged". Checked myself: main is at ee0b954 and
05:45:55Z         FIVE branches have landed -- 679a629 wi-3-end-to-end-join,
05:45:55Z         c708a39 wi-7-game-state, 89e5d0a wi-5a-wall-glyphs, 6694d56
05:45:55Z         wi-8-player-move, ee0b954 wi-9-ghost-policy. 8c4e2ce is real
05:45:55Z         but is now six commits back. The lockout has ended.
05:45:55Z NOTE    WI-11 this is DEV-B's M0-failure shape again, one level up: the
05:45:55Z         conductor and I held different beliefs about where main was.
05:45:55Z         The remedy is the one DEV-B applied -- check, do not carry. I
05:45:55Z         verified with git log rather than accepting either sha.
05:45:55Z TEST    525 passed, 0 failed, 0 skipped -- merged tree, clean merge.
05:45:55Z DECIDE  WI-11 the tick uses ghost_policy.ghost_move (the pure policy,
05:45:55Z         which cannot see the player -- GHOST-4) and then WI-10's
05:45:55Z         advance_ghost, NOT ghost_policy.move_ghost. move_ghost does not
05:45:55Z         guard on outcome, so routing through it would take the ghost
05:45:55Z         half of END-5 out of the domain and put it back in the loop --
05:45:55Z         precisely what the ruling forbids.
05:45:55Z DECIDE  WI-11 the frame builder is injected rather than imported. WI-5b
05:45:55Z         is not in this tree (WI-12 is the wiring item, and it depends on
05:45:55Z         WI-5b), and the loop has no business knowing how a frame is
05:45:55Z         composed. Read their compose(state, status_line=None) signature
05:45:55Z         off wi-5b-frame-composition so the injection point matches what
05:45:55Z         WI-12 will pass.
05:45:55Z DECIDE  WI-11 redraw when the state CHANGED, tested by identity. The
05:45:55Z         domain returns the same object when nothing happened -- WI-8's
05:45:55Z         CTRL-3 convention, kept by WI-10 -- so "the frame is not rebuilt
05:45:55Z         once the game is over" falls out of the domain guard instead of
05:45:55Z         being a second rule in the loop. END-5's rebuild clause needs no
05:45:55Z         loop-side check at all.
05:45:55Z PLAN    WI-11 terminalgame/application/loop.py, tests in
05:45:55Z         tests/test_game_loop.py with fakes in tests/loop_fakes.py -- a
05:45:55Z         scripted screen that advances the clock to a key's arrival time
05:45:55Z         or to the deadline, which is what makes "a key arriving early
05:45:55Z         does not postpone the tick" testable at all.
05:49:02Z NOTE    WI-11 two of my own tests failed first and both were right to.
05:49:02Z         "nothing is redrawn while nothing moves" came back 8 frames
05:49:02Z         instead of 1: with_changes builds a new GameState whatever it
05:49:02Z         is handed, so a ghost told to stay put looked like a change and
05:49:02Z         the loop redrew an identical picture. That is a real gap in my
05:49:02Z         own WI-10 advance_ghost, found by the loop rather than by
05:49:02Z         inspection. Fixed there, not worked around here: the Domain now
05:49:02Z         returns the same state when the ghost stays, so the convention
05:49:02Z         every other step already followed holds without exception.
05:49:02Z NOTE    WI-11 the second failure was my test, not the code. I compared
05:49:02Z         whole ghost walks across three player positions for GHOST-4;
05:49:02Z         they differed in LENGTH because the ghost caught different
05:49:02Z         players at different moments and a finished game issues no more
05:49:02Z         ticks. That is END-5 working, not GHOST-4 failing. Compared as
05:49:02Z         a prefix instead, with the reason written down, and noted that
05:49:02Z         DEV-B's test_ghost_policy.py holds the definitive form.
05:49:02Z MEASURE WI-11 GHOST-1 against a REAL clock, because an injected one
05:49:02Z         proves only the arithmetic. 2.007s -> 14 ticks (6.975/s);
05:49:02Z         4.011s -> 28 ticks (6.981/s); target 7.000. The anti-drift
05:49:02Z         property is in the COUNTS not the rate: exactly double the
05:49:02Z         ticks for exactly double the time. A loop rebasing its deadline
05:49:02Z         on the present would show fewer than twice. Frames = ticks + 1,
05:49:02Z         the extra being START-5's opening picture.
05:49:02Z TEST    570 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
05:49:02Z COMMIT  b90d6ea WI-11: the game loop
05:49:02Z NOTE    WI-11 tests/test_layering.py deliberately untouched: no
05:49:02Z         Application purity class added, because WI-12 is the natural
05:49:02Z         place to settle what Application may import and DEV-B is
05:49:02Z         actively editing that file for WI-5b. Recorded in the commit
05:49:02Z         message and the PR summary per EDIT 11. LayerRuleTest already
05:49:02Z         sweeps loop.py for curses and subprocess.
05:49:02Z NOTE    WI-11 windows opened: 0. The real-clock measurement used a stub
05:49:02Z         screen -- GHOST-1 is about time, not about drawing.
05:49:02Z DONE    WI-11 wi-11-game-loop b90d6ea (docs commit follows)
```
