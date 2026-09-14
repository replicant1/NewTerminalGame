# WI-3 — the end-to-end join

Branch `wi-3-end-to-end-join`, cut from `main` at 5269b67. DEV-A, local mode.

```
05:12:41Z START   WI-3 the end-to-end join: the launcher opens the window running the
05:12:41Z         real game process, the game runs, the game exits on q, the launcher
05:12:41Z         confirms the window is idle and closes it by the captured identity.
05:12:41Z NOTE    WI-3 this worktree's HEAD was on an unrelated branch
05:12:41Z         (worktree-agent-a3edb1c9bd34f0bdc, an agent-config history with no
05:12:41Z         launcher/ or terminalgame/ in it). Cut wi-3-end-to-end-join from
05:12:41Z         main explicitly rather than from HEAD.
05:09:27Z NOTE    WI-3 read both halves before writing. WindowLauncher.run(command)
05:09:27Z         already does open/wait/reap; game_main already exits on q or on a
05:09:27Z         bounded --hold. So WI-3 is the command in between, plus the proof.
05:09:27Z NOTE    WI-3 found a race the join has to face. game_main checks the screen
05:09:27Z         size once, at curses startup, and fails loudly below 40x30. But the
05:09:27Z         launcher's configure(40x30) runs AFTER open_window_running has
05:09:27Z         already started the command, and no rows/columns are set in
05:09:27Z         com.apple.Terminal, so a new window opens at the built-in 80x24.
05:09:27Z MEASURE WI-3 one window (7681), instrumented both sides: created +0.124s,
05:09:27Z         configured +0.316s, child's first look +0.823s, and it saw "30 40".
05:09:27Z         Margin 0.496s. The race is won, but only by login-shell start-up
05:09:27Z         latency, which is accidental, not designed.
05:09:27Z DECIDE  WI-3 add a bounded size gate to the launched command rather than
05:09:27Z         rely on that 0.5s. Bounded 60 x 0.1s, and it always falls through,
05:09:27Z         so WI-2's loud failure on a genuinely small screen is preserved.
05:09:27Z NOTE    WI-3 census metric corrected. "id of every window" counts closed
05:09:27Z         but still addressable window objects -- it reported 7681 after the
05:09:27Z         launcher had closed it. The metric that holds still is "every
05:09:27Z         window whose visible is true". True baseline: 1 visible (id 7104).
05:09:27Z PLAN    WI-3 launcher/game.py: the game command as pure text (gate, cd to
05:09:27Z         the repository root, exec python -m terminalgame.game_main with an
05:09:27Z         explicit --hold), plus python3 -m launcher.game. Tests in
05:09:27Z         tests/test_game_command.py and tests/test_end_to_end_join.py --
05:09:27Z         names colliding with neither DEV-B's set nor my WI-1 set.
05:11:39Z TEST    231 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
05:11:39Z COMMIT  c8450e6 WI-3: join the launcher to the real game process

05:21:58Z NOTE    WI-3 the first real run against the real desktop was a FALSE GREEN
05:21:58Z         and this is the whole story of the work item. python3 -m
05:21:58Z         launcher.game reported "window 7684 closed" and exit 0, and took
05:21:58Z         1.00s -- with --hold 5 AND with --hold 12. The launcher's success
05:21:58Z         signal says nothing about whether the game ran. It had not.
05:21:58Z MEASURE WI-3 tab contents read back from a live window (7693) show the
05:21:58Z         whole frame -- walls, title, dots, player glyph, ghost glyph and
05:21:58Z         the status line, in 40x30. So the game DOES draw. The launcher was
05:21:58Z         closing the window out from under it.
05:21:58Z MEASURE WI-3 ground truth via pgrep, which knows nothing about Terminal:
05:21:58Z         with the grid set (7698) the game is alive +0.9s..+8.4s while busy
05:21:58Z         says false from +0.9s onwards. Without the grid (7699) busy tracks
05:21:58Z         the process exactly. Bisected configure by group: font, colours
05:21:58Z         and title are all harmless; it is "set number of columns/rows"
05:21:58Z         alone (7700-7704) that spoils the flag. WIN-2 requires the grid.
05:21:58Z NOTE    WI-3 so caution C2's guard is inert on every window this system
05:21:58Z         opens. No modal sheet was ever raised, and none was expected --
05:21:58Z         Terminal does not prompt for a window it believes is idle. The
05:21:58Z         damage is the opposite of what C2 anticipated: not a blocked
05:21:58Z         automation call, but a game killed under the player.
05:21:58Z MEASURE WI-3 sizing the window BEFORE running the game in it (do script
05:21:58Z         ... in selected tab) does not fix busy either -- still false. The
05:21:58Z         tab is spoiled by having been resized at all.
05:21:58Z MEASURE WI-3 "processes of selected tab" stays accurate (7709): during
05:21:58Z         start-up "login|-zsh|ssh-add", while playing "login|Python", after
05:21:58Z         the game "" -- empty. Empty is unambiguous and needs no name
05:21:58Z         matching, because the launcher execs the command so no shell is
05:21:58Z         left underneath it. Non-empty during start-up also closes the
05:21:58Z         start-up gap for free.
05:21:58Z DECIDE  WI-3 the join asks the process list, not the busy flag.
05:21:58Z         wait_until_idle and reap take a still_running argument defaulting
05:21:58Z         to the old behaviour, so WI-1's contract and its 107 tests are
05:21:58Z         untouched; launcher/game.py passes has_live_processes. The general
05:21:58Z         fix to WindowLauncher.run needs a ruling and is in the PR summary.
05:21:58Z NOTE    WI-3 WI-1's test_every_public_builder_in_the_module_is_covered_by
05:21:58Z         _these_rules caught the new window_processes builder and made me
05:21:58Z         register it in CALLS_ON_THE_CAPTURED_WINDOW, where it passes the
05:21:58Z         by-id and boundedness rules. That guard did exactly its job.
05:21:58Z MEASURE WI-3 the join now works: --hold 5 takes 6.13s, --hold 12 takes
05:21:58Z         12.92s. A 7s difference in the hold shows as 6.79s in the session.
05:21:58Z         Nothing leaked either time; visible census 1 before and after.
05:21:58Z TEST    238 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
05:21:58Z COMMIT  60ba089 WI-3: ask what is running, not whether the tab says busy

05:23:08Z MEASURE WI-3 the q path, which a --hold expiry does not demonstrate.
05:23:08Z         Window 7719 given a 30s hold; q delivered to that tab alone via
05:23:08Z         do script "q" in selected tab of window id N (no focus stealing,
05:23:08Z         no keystroke injection). Game running +0.76s, q sent +2.76s, game
05:23:08Z         gone +2.90s -- 0.14s later and 27s before the hold. Window closed
05:23:08Z         by the captured id, nothing leaked. So every clause of WI-3 is
05:23:08Z         now observed: opens running the real game, the game runs, it
05:23:08Z         exits on q, the window is closed, nothing is left behind.
05:23:08Z NOTE    WI-3 windows: 29 opened across all measurement, 29 closed. Final
05:23:08Z         visible census 7104 only, which is where it started.
05:23:08Z DONE    WI-3 wi-3-end-to-end-join 72402a9 (this log commit follows it)
```
