02:48:09Z  START   WI-10 verification harness and human-check pack — base main c8defe7, branch wi-10-verification-pack
02:48:21Z  READ    plan §5 WI-10 brief, §6 parallelism, §8 the six human checks H1–H6
02:48:26Z  READ    plan §2 ground rules in full (2.1 non-local, 2.2 pinned command, 2.3 flat tests, 2.4 purity, 2.6 window safety, 2.8 branches)
02:48:32Z  READ    findings WI-2 (window id, coord spaces, census [367, 2486]) and WI-4 (pty harness, bottom-right cell, ESC-O arrows)
02:48:39Z  READ    findings WI-7 (ghost decision points) and both WI-8 notes (timeouts; title settling race + the silent display fallback)
02:50:13Z  READ    code: loop.py, standins.py, screen.py API, launch-smoke, tests/test_curses_pty.py, tests/test_purity.py — the purity guard scans termgame/ only, so a top-level executable is safe (same reason WI-8 made launch-smoke top-level)
02:50:13Z  PLAN    three deliverables: (1) top-level ./verify with named stages — suite, launch smoke, scripted play-through against the REAL rules+renderer, plus an opt-in --corner stage that measures the bottom-right cell in a real 40x30 Terminal window; (2) ./check-window-placement, the single step for H1, which prints the reference position, runs ./play and does the offset arithmetic for the user; (3) docs/findings/WI-10-human-checks.md, the pack for H1-H6, written for someone who has not read the plan
02:50:32Z  TEST    567 passed, 0 failed, 2 skipped — baseline on main before any change
02:53:14Z  NOTE    baseline confirmed and the shape settled; writing ./verify now — stages suite / smoke / play, with --corner for the real-window bottom-right measurement
