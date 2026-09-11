01:14:26Z  START   WI-4 curses adapter and the loop with its one deadline
01:14:44Z  READ    FUNCTIONAL_REQUIREMENTS.md in full (CTRL-1..5, GHOST-1, SCRN-7, END-6)
01:14:59Z  READ    IMPLEMENTATION_PLAN §2 ground rules, §5 WI-4 brief, §10.1 ruling
01:15:13Z  READ    ARCHITECTURE §5.5, §6.1, §6.2, §7, §8
01:17:43Z  PLAN    pure controls.py (key->command) + ticker.py (deadline), impure screen.py (sole curses importer), loop.py rewritten as a fake-drivable loop, standins.py that WI-9 deletes
01:17:53Z  TEST    186 passed, 0 failed, 2 skipped (baseline on main before any WI-4 change)
01:19:01Z  NOTE    purity guard names the impure trio {screen, loop, window}; the curses adapter must therefore be termgame/screen.py
01:19:01Z  ASK     what style identifiers does WI-3 use for wall/dot/player/ghost/status? Dev A owns the names and WI-3 has not merged
01:19:01Z  ASSUME  the adapter palette is keyed on those five plain names and an unknown identifier falls back to the default attribute, so a mismatch loses colour and never the picture. Affects termgame/screen.py PALETTE only; a self-arming test asserts every identifier WI-3 emits is known the moment view.py lands
01:19:47Z  NOTE    lead endorses the lenient-palette design and the self-arming test; will relay WI-3 style names when Dev A commits termgame/theme.py. Proceeding on the ASSUME, not holding up
01:22:23Z  NOTE    lead relayed WI-3 style names: wall/dot/player/ghost/status + default — my guess matched. Adapter now READS termgame.theme.STYLES when present rather than hardcoding colours; the fallback table stays for this branch alone
01:22:39Z  COMMIT  5f4a24c WI-4: the two pure decisions, the curses adapter and the real loop
01:24:34Z  TEST    40 passed, 0 failed, 0 skipped (test_controls.py + test_ticker.py alone)
01:24:34Z  NOTE    measured: int((10.1-10.0)*1000) is 99, not 100 — truncating a dirty float loses up to 1ms, costing one extra turn of the loop (0.25ms paint) and no tick. Tests assert exact ms only on binary-exact values
01:24:50Z  COMMIT  a72ab69 WI-4: the key mapping and the deadline, tested exhaustively
01:31:59Z  NOTE    wrote tests/test_loop.py (40 tests, fake screen + fake clock) and tests/test_screen_adapter.py (24, fake curses window) — both green; three of my own test-arithmetic errors found and fixed, no loop defects
01:31:59Z  NOTE    building tests/test_curses_pty.py: the adapter against REAL ncurses on a 40x30 pty, to measure C1 rather than assume it. First attempt hung for the full 60s timeout
01:31:59Z  NOTE    cause found: nobody was draining the pty master, so the child blocked in write once the buffer filled. Added a reader thread; retrying now. Nothing blocked, no windows opened, no gh refusals
01:31:59Z  NOTE    lead reports WI-3 merged to main at 258/0/2; will merge origin/main after the pty probe is settled
01:32:25Z  NOTE    pty probe green against real ncurses: addstr at (29,39) gives "addwstr() returned ERR", insstr does not, full 30x40 paint clean, and the screen reads back identical including the corner cell. C1 measured, not assumed
01:32:48Z  TEST    290 passed, 0 failed, 3 skipped (whole suite, branch before merging main)
01:33:06Z  COMMIT  344cf5f WI-4: the loop driven by a fake screen, and the adapter measured on a real pty
01:34:30Z  COMMIT  9241c3f WI-4: PR summary
01:34:34Z  NOTE    draft PR 7 open against main; merging main in now that WI-3 has landed
01:36:05Z  TEST    368 passed, 0 failed, 2 skipped (whole suite, after merging main with WI-3, /usr/bin/python3 3.9.6)
01:36:09Z  TEST    368 passed, 0 failed, 2 skipped on /opt/homebrew/bin/python3 3.14.7 too — the cross-check agrees
01:37:05Z  COMMIT  1ef1add WI-4: merge main WI-3, and the tests that only WI-3 being here makes possible
01:39:56Z  NOTE    found: keypad(True) sends smkx, so a terminal in application-cursor mode sends ESC O C for right, not ESC [ C. Feeding ESC [ C to a pty gives back 27, 91, 67 as three separate codes and the arrows look broken. The scripted pty game now reads the four sequences out of terminfo
01:40:00Z  TEST    373 passed, 0 failed, 2 skipped (whole suite with the scripted real-ncurses game added)
01:40:41Z  COMMIT  f80cf0b WI-4: play a whole scripted game through real ncurses, and write up the how
01:41:38Z  TEST    373 passed, 0 failed, 2 skipped on /opt/homebrew/bin/python3 3.14.7 — cross-check agrees exactly
01:41:44Z  NOTE    no Terminal window opened by this work item at any point — the live run needs a person to press q, and typing into another app needs Accessibility which this design does not require. Real-ncurses coverage came from the pty instead
