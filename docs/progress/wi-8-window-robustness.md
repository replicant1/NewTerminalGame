# WI-8 — window robustness, the failure-path close, and the launch smoke

01:45:48Z  START   WI-8 branch wi-8-window-robustness cut from origin/main 496d572
01:46:00Z  WI-8 READ    docs/IMPLEMENTATION_PLAN.md §2 ground rules, incl §2.6 window safety and §2.8 branches
01:46:07Z  WI-8 READ    docs/findings/WI-2-terminal-window-id.md — busy-false-while-running, visible-not-exists, the coordinate offset, exact error text
01:46:13Z  WI-8 READ    termgame/window.py — 772 lines; supervise() already has a finally-close, close_when_idle, CLOSE_GRACE_SECONDS=10.0
01:46:19Z  WI-8 READ    tests/test_window_supervisor.py, tests/test_launch_smoke.py, play, Terminal Game
01:49:39Z  WI-8 TEST    373 passed, 0 failed, 2 skipped (baseline on origin/main, before any change)
01:49:39Z  WI-8 PLAN    harden window.py's failure paths (tolerant reference query, gone-window tolerance, signal-driven interrupt close, visible-confirmed close, an unmaskable finally), add a ./launch-smoke one-command executable, and a failure-path test module whose recording fake forbids `front window` / a title / an index on EVERY path
01:52:03Z  WI-8 TEST    373 passed, 0 failed, 2 skipped (window.py hardened, no new tests yet)
01:52:03Z  WI-8 COMMIT  87e048c WI-8: the failure paths harden — tolerant reference query, a gone window, signals, and a close confirmed by visible
01:52:31Z  WI-8 NOTE    draft PR #9 opened against main — https://github.com/replicant1/NewTerminalGame/pull/9
01:52:31Z  WI-8 ASSUME  A1 unanswered: proceeding on the architect's reading — the last picture stays, q exits, the window closes then. Depends on it: the main wait in supervise(), every failure-path test that asserts a close happens only after the tab is empty, and human check H2. Flipping it is one wait removed; it is NOT a ruling.
01:53Z-01:58Z  WI-8 NOTE    (logged late, at 01:58:37Z — the six minutes below were one stretch of writing tests/test_window_failure_paths.py and iterating on it; nothing was stuck, no osascript ran, no window was opened)
01:58:37Z  WI-8 NOTE    wrote tests/test_window_failure_paths.py — a RecordingTerminal fake + 14 named paths swept by the §2.6-rule-1 regression test
01:58:37Z  WI-8 NOTE    the rule-1 check is an ALLOWLIST, not a denylist: every occurrence of the word `window` in every script on every path must be one of `first window whose id is N`, `first window whose tabs contains newTab`, `repeat with w in windows`, or the WIN-3 title component `title displays window size`
01:58:37Z  WI-8 NOTE    added window._sleep / window._now indirections so a test can watch the 10s grace elapse without spending 10s, and without mutating the stdlib time module for the whole process
01:58:37Z  WI-8 TEST    34 passed, 1 failed, 0 skipped (failure-path module alone; the signal scenario's fake was modelling the wrong tab state — fixing)
01:59:31Z  WI-8 TEST    409 passed, 0 failed, 2 skipped (whole suite, pinned command — 373 at the branch point + 36 new)
01:59:31Z  WI-8 COMMIT  66e681e WI-8: every failure path, and the never-touch-a-window-you-did-not-open regression test
01:59:31Z  WI-8 PLAN    next: ./launch-smoke, the one-command smoke — supervise() on a worker thread against a self-exiting child named `Terminal Game` in a temp dir, with the captured id arriving via on_window_opened, never by enumerating windows
