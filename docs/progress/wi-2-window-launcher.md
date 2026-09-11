00:37:53Z  START   WI-2 — window, launcher, two executables; branch wi-2-window-launcher cut from main
00:38:04Z  READ    plan §2 ground rules and §5 WI-2 brief; next: ARCHITECTURE §6.3, §4, §7, §12
00:38:14Z  READ    ARCHITECTURE §4, §6.3, §7, §12 — WIN-3 recipe is measured; adopting it verbatim
00:39:31Z  WI-2 PLAN    window.py = AppleScript island + supervisor; pure decisions (offset, fallback chain, script text) extracted and unit-tested; play + 'Terminal Game' executables; placeholder entry point in loop.py
00:39:31Z  WI-2 ASK     A1 — does WIN-5 mean the window vanishes on the final frame, or when the player presses q? (with the user, unanswered)
00:39:31Z  WI-2 ASSUME  proceeding on the architect's assumption: q exits the child, the supervisor then closes the window. Affects one wait in the supervisor's close path, WI-8, WI-9, human check H2. Cheap to flip.
00:39:45Z  WI-2 NOTE    Terminal window census BEFORE: ids 367, 2486, 2420, 2440 (4 windows). tty reports 'not a tty', os.isatty(0) False — the live smoke will skip for me.
00:44:36Z  WI-2 NOTE    child with stdin not a tty: first bytes ESC]7;BEL then the static screen, exit 0 — cannot block forever without a terminal
00:45:52Z  WI-2 NOTE    draft PR #4 open against main (repo replicant1/NewTerminalGame). Now writing the tests.
00:46:59Z  WI-2 TEST    41 passed, 0 failed, 0 skipped (geometry + script text)
00:49:13Z  WI-2 TEST    69 passed, 0 failed, 0 skipped (adds executables, supervisor sequence, placeholder screen)
