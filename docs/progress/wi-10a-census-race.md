# WI-10a — window census race fix

04:15:18Z  START   WI-10a census race fix, branch wi-10a-census-race cut from origin/main 37def54
04:15:39Z  READ    WI-10a termgame/window.py: script_visible_window_ids (repeat loop), parse_window_ids (splits on , and newline), visible_window_ids caller
04:15:39Z  READ    WI-10a tests/test_window_failure_paths.py: ADDRESSING_ALLOWLIST + addressing_faults residue check; tests/test_launch_smoke.py uses visible_window_ids() live
04:16:06Z  NOTE    WI-10a live baseline census: all window ids = 367, 2486, 2420, 2440; visible = 367, 2486
04:16:06Z  NOTE    WI-10a output shapes measured: 2 windows -> "367, 2486\n"; 1 window -> "367\n"; empty -> "\n" (rc 0). parse_window_ids splits on "," and newline, so all three parse; empty -> []
04:17:06Z  TEST    746 passed-run: 744 passed, 2 failed, 2 skipped (test_launch_smoke_script) after applying the patch as given
04:17:06Z  NOTE    WI-10a DEFECT IN THE PATCH: tests/test_window_failure_paths.py::classify still keys the census off the old text "if visible of w then", so the fake Terminal stopped answering the census at all -> smoke before-census came back empty and the reconcile test passed vacuously. Patch is incomplete; fixing.
04:19:33Z  NOTE    WI-10a second stale literal found: tests/test_launch_smoke_script.py keyed its census-lie on "set out to"; now keys on classify(script)=="census". Fake census answer is now ", "-joined, the shape osascript really prints.
04:19:33Z  TEST    746 passed, 0 failed, 2 skipped (/usr/bin/python3 -m unittest discover -s tests)
04:20:24Z  COMMIT  e28e4fb WI-10a: census asks Terminal once instead of walking an index
04:21:16Z  NOTE    WI-10a pushed wi-10a-census-race, opened draft PR #14 against main
04:21:16Z  PLAN    WI-10a add the test that carries the weight (census survives a window vanishing mid-census, driven through visible_window_ids with a fake run_osascript that raises the measured -1719 for a loop-shaped script) plus a parse test over the three measured output shapes
04:22:41Z  TEST    749 passed, 0 failed, 2 skipped (3 new tests in tests/test_window_supervisor.py)
04:22:41Z  NOTE    WI-10a discrimination check: with script_visible_window_ids swapped back to the old repeat-loop text, visible_window_ids() raises the measured -1719 WindowError against the same fake the new test passes against. The behavioural test tells the two apart.
04:23:14Z  COMMIT  d5acdf7 WI-10a: test the census against a Terminal that is losing a window (pushed)
04:23:14Z  PLAN    WI-10a live verification next: open one window, capture its id at creation, let its child exit and confirm, census across the close with BOTH script forms, then close by the captured id and reap. Full census before and after.
04:24:16Z  NOTE    WI-10a starting live check: opens up to 4 windows one at a time, each with a 2s sh child, each closed by its captured id after the child is confirmed exited
04:24:43Z  NOTE    WI-10a live check PASSED, exit 0. 4 windows opened and reaped, each closed by its captured id after wait_until_idle confirmed the child exited. Visible census before [367, 2486] == after [367, 2486]; no user window went missing. All-ids grew to include 4632, the lingering-invisible closed id WI-2 measured.
04:24:43Z  NOTE    WI-10a HONEST LIMIT: the old repeat-loop census did NOT fail in these 4 rounds. It is a race; WI-10 hit it, I did not reproduce it live. What I could prove live is that the new census agrees with the old one every round and reconciles across every close.
04:26:02Z  TEST    749 passed, 0 failed, 2 skipped (final) -- /usr/bin/python3 -m unittest discover -s tests
04:26:51Z  NOTE    WI-10a PR #14 body updated from docs/prs/PR-WI-10a-census-race.md and marked ready for review; base main, MERGEABLE, not merged (the technical lead merges).
04:26:51Z  NOTE    WI-10a final visible census 367, 2486 -- identical to the baseline taken at 04:16:06Z. No window opened by this work item is left on the screen.
04:26:51Z  DONE    WI-10a wi-10a-census-race 1153a98
