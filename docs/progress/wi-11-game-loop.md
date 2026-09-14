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
```
