02:48:09Z  START   WI-10 verification harness and human-check pack — base main c8defe7, branch wi-10-verification-pack
02:48:21Z  READ    plan §5 WI-10 brief, §6 parallelism, §8 the six human checks H1–H6
02:48:26Z  READ    plan §2 ground rules in full (2.1 non-local, 2.2 pinned command, 2.3 flat tests, 2.4 purity, 2.6 window safety, 2.8 branches)
02:48:32Z  READ    findings WI-2 (window id, coord spaces, census [367, 2486]) and WI-4 (pty harness, bottom-right cell, ESC-O arrows)
02:48:39Z  READ    findings WI-7 (ghost decision points) and both WI-8 notes (timeouts; title settling race + the silent display fallback)
02:50:13Z  READ    code: loop.py, standins.py, screen.py API, launch-smoke, tests/test_curses_pty.py, tests/test_purity.py — the purity guard scans termgame/ only, so a top-level executable is safe (same reason WI-8 made launch-smoke top-level)
02:50:13Z  PLAN    three deliverables: (1) top-level ./verify with named stages — suite, launch smoke, scripted play-through against the REAL rules+renderer, plus an opt-in --corner stage that measures the bottom-right cell in a real 40x30 Terminal window; (2) ./check-window-placement, the single step for H1, which prints the reference position, runs ./play and does the offset arithmetic for the user; (3) docs/findings/WI-10-human-checks.md, the pack for H1-H6, written for someone who has not read the plan
02:50:32Z  TEST    567 passed, 0 failed, 2 skipped — baseline on main before any change
02:53:14Z  NOTE    baseline confirmed and the shape settled; writing ./verify now — stages suite / smoke / play, with --corner for the real-window bottom-right measurement
02:58:11Z  NOTE    branch pushed; draft PR #13 open against main (replicant1/NewTerminalGame pull 13)
03:01:20Z  TEST    644 passed, 0 failed, 2 skipped — 77 new tests for ./verify (567 on main + 77)
03:01:53Z  COMMIT  71a6166 WI-10: 77 tests for the harness, most of them breaking a stage on purpose
03:04:36Z  NOTE    broke the harness twice on purpose, live: a deliberately failing test file made stage 1 of 2 report "FAILED at stage 1 of 2: the test suite ... exited 1 -- Ran 645 tests; FAILED (failures=1, skipped=2)" with the traceback under it; a doctored recording made the play stage report "row 3 differs from the recorded picture, first at column 1" with both rows quoted. Both artefacts removed afterwards
03:04:36Z  TEST    664 passed, 0 failed, 2 skipped — ./check-window-placement and its 20 tests added
03:05:05Z  COMMIT  608b547 WI-10: ./check-window-placement — human check H1 as one step
03:05:11Z  NOTE    census before the live window run: visible [367, 2486], full [367, 2420, 2440, 2486] — the same set WI-2, WI-4 and WI-8 measured
03:06:25Z  NOTE    corner stage run live twice — windows 4318 and 4321, both landed at (-868, 106) from reference (-898, 76), i.e. exactly +30/+30, and no display-layout fallback either time. In a REAL 40x30 window: addstr(29,39) raises "addwstr() returned ERR", insstr does not, the adapter paints the whole picture without raising, and the screen reads back identical to the picture. **No fix needed** — architecture C1 holds against a real window exactly as WI-4 measured it on a pty
03:06:25Z  NOTE    census unchanged across all three live windows: visible [367, 2486] before and after every one. The closed ids linger in "id of every window" and go invisible, which is WI-2 finding §6 reproduced
03:06:58Z  TEST    666 passed, 0 failed, 2 skipped — and the whole ./verify run green in 23.1s: suite 12.5s, launch smoke 9.8s (window 4324, title settled in 0.8s, tab 40 x 30 Menlo-Regular 18, census unchanged), play-through 0.1s
03:07:19Z  COMMIT  667f6c5 WI-10: --verbose, so a measurement taken by a passing stage can be read
03:11:27Z  TEST    701 passed, 0 failed, 2 skipped — the human-check pack and its 35 staleness tests, plus the bottom-right findings note
03:14:32Z  TEST    745 passed, 0 failed, 2 skipped — after merging origin/main (WI-9, 606 there) and folding WI-9's three measurements into the pack. Merge was clean: no conflicts, nothing of mine referenced standins.py
03:14:32Z  NOTE    the real-maze recorded picture survived WI-9 unchanged — rules.new_game(Random(10)) is what it always was, so the golden still matches character for character
