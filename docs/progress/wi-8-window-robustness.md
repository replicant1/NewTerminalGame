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
