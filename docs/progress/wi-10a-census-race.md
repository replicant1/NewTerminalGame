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
