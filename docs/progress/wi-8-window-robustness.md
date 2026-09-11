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
02:04:40Z  WI-8 TEST    433 passed, 0 failed, 2 skipped (whole suite; +24 for the smoke script)
02:04:40Z  WI-8 COMMIT  48868b7 WI-8: ./launch-smoke — the one-command launch smoke, and its tests
02:04:40Z  WI-8 NOTE    the smoke's fake found a real defect in itself: visible_after_close was a fixed string, so the clean-up could believe the window had gone while the census still listed it. The fake now derives `visible` from its own census, and the never-force-a-busy-tab test only passes because of it.
02:04:40Z  WI-8 PLAN    next: the REAL run. ./launch-smoke --repeat 2 against Terminal.app, with the census before and after. This is the first osascript this branch has run.
02:19:13Z  WI-8 NOTE    (logged late again — my fault, not a hang. Nothing was ever stuck; no osascript hung, none timed out, no modal sheet. Every window this branch opened is closed. The lines below are what happened between 02:05Z and 02:19Z.)
02:19:13Z  WI-8 SMOKE   ./launch-smoke --repeat 2 — FIRST live attempt, ~02:06Z: both runs FAILED, on one check only, and the failure was real and worth having
02:19:13Z  WI-8 NOTE    census that attempt: visible [367, 2486] before AND after BOTH runs. Windows 4081 and 4085 opened, closed by captured id, confirmed not visible. Nothing of the user's moved.
02:19:13Z  WI-8 NOTE    the failing check: the title read 'rodneybailey — ssh-add --apple-use-keychain ~/.ssh/id_ed25519'. NOT a WIN-3 failure — `do script` runs the user's LOGIN SHELL, which sources their startup files before our `exec` line, and Terminal's title follows whatever that shell is doing. WI-2 never saw it because it sampled the title a full second after creating the window; my on_window_ready hook fires ~0.4s earlier. Fix: poll the title until it settles rather than sampling it once, and report how long it took. Settles in 0.4s, measured.
02:19:13Z  WI-8 NOTE    second real defect from the same run: Check.__str__ printed the failure detail beside passing checks too, so the report read "ok  the window we opened is no longer visible -- window 4081 is still on the screen". Cosmetic, but it is the line a human reads to decide whether their screen is safe. Fixed and pinned by a test.
02:19:13Z  WI-8 SMOKE   ./launch-smoke --repeat 2 — SECOND live attempt, ~02:12Z: PASS, PASS. 10/10 checks green both runs. Windows 4102 and 4103 opened and closed by captured id. Census [367, 2486] before and after BOTH runs — identical to WI-2's and WI-4's measurement.
02:19:13Z  WI-8 NOTE    THIRD real finding, from comparing the two attempts: window.displays() returned the 1440x900 FALLBACK on one call, on a machine whose three displays CGGetActiveDisplayList reported correctly seconds later — and it fell back SILENTLY. Consequence is not cosmetic: the reference at (-898, 76) is then "on no display", the clamp moves the game to the main screen, and WIN-4 quietly stops holding. The game window did land at (0, 106) instead of (-868, 106) because of it. Falling back is right; falling back in silence is not.
02:19:13Z  WI-8 NOTE    no osascript call errored, timed out, or hung at any point on this branch. No modal sheet was raised. No window this branch opened is still open.
02:21:22Z  WI-8 TEST    443 passed, 0 failed, 2 skipped (whole suite, pinned command)
02:21:22Z  WI-8 SMOKE   ./launch-smoke --repeat 2 — THIRD live attempt, after the displays() reporting change: PASS, PASS. Windows 4248 and 4251. Census [367, 2486] before and after BOTH runs. Title settled in 0.8s then 0.4s. Window landed at (-868, 106) = reference + 30 on the reference's own display, so the real layout was read and no fallback line was printed — the earlier silent fallback was transient, which is exactly why it needed to become audible.
02:23:53Z  WI-8 NOTE    merged origin/main (0c4b93f, WI-5) — CLEAN, no conflict. WI-5 added termgame/rules.py and tests/test_rules_start.py, neither of which I touch.
02:23:53Z  WI-8 TEST    479 passed, 0 failed, 2 skipped (whole suite after the merge — 409 on main + 70 mine)
02:23:53Z  WI-8 NOTE    my PR diff against origin/main contains NO orchestration/ changes. index.html arrived via the merge FROM main, not from me; I have not touched it.
02:23:53Z  WI-8 COMMIT  bf97cc9 WI-8: the title has to settle, the report must not contradict itself, and a silent display fallback becomes audible
02:23:53Z  WI-8 NOTE    wrote docs/findings/WI-8-close-grace-timeout.md and docs/findings/WI-8-title-settling-race.md
02:25:19Z  WI-8 TEST    479 passed, 0 failed, 2 skipped (whole suite, final)
02:25:19Z  WI-8 NOTE    PR body written to docs/prs/PR-WI-8-window-robustness.md
02:25:51Z  WI-8 NOTE    final census: visible Terminal windows [367, 2486] — unchanged from the start of this work item. No osascript, launch-smoke or `Terminal Game` process is running. Nothing of mine is left on the user's screen.
02:25:51Z  WI-8 NOTE    PR #9 marked ready for review, base main, MERGEABLE. NOT merged, not approved, not closed — that is the conductor's.
02:25:51Z  WI-8 DONE    WI-8 wi-8-window-robustness c81b35f
