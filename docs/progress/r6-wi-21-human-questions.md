# WI-21 — the questions for a human

Branch `r6/wi-21-human-questions`, based on `main` at `238f4dd`. Non-local mode. Append-only.

05:34:16Z  WI-21 START   the five questions for a human; make them cheap and unambiguous to answer, and answer none of them
05:34:43Z  WI-21 READ    IMPLEMENTATION_PLAN sections 0a-0g, 4, 8 (WI-21/WI-22), 13; amendment 10 rewrote WI-21
05:34:43Z  WI-21 READ    terminal_game/shell/game.py, terminal_game/__main__.py - main() already takes --seconds and --seed
05:34:43Z  WI-21 READ    tools/play_the_game.py (4 machine exercises, ~1.2s each), tools/the_look.py (3 views, joinery is the A10 instrument)
05:34:43Z  WI-21 READ    docs/findings/WI-16-the-look.md, WI-18-the-game-on-screen.md; tests/house_rules.py, tests/recording_toolkit.py, tests/test_the_look.py
05:35:28Z  WI-21 PLAN    tools/the_questions.py: the five questions as data, one bounded sitting over the REAL assembled game at the REAL anchor, and a checklist that hands the user the unbounded command separately
05:35:28Z  WI-21 WEIGH   where the sitting comes from : (a) extend tools/play_the_game.py, (b) a new tool, (c) reuse tools/the_look.py
05:35:28Z  WI-21 DECIDE  a new tool -> tools/the_questions.py, because play_the_game's four exercises are ~1.2s JSON measurements nobody can look at, and the_look opens at the DEFAULT position, never the real anchor - so WIN-4 has never been shown to a person
05:35:28Z  WI-21 DECIDE  A10 -> point at tools/the_look.py --view joinery rather than redraw a lattice, because section 13 names that view and a second lattice would be a duplicate nobody asked for
05:35:28Z  WI-21 DECIDE  the frame -> build_game() with compose left at its default (shell/game.py compose_picture), because WI-22 is consolidating that binding and this item must not add a fifth copy
05:35:28Z  WI-21 WEIGH   findings filename : the plan names docs/findings/WI-21-human-answers.md, but it will contain no answers
05:35:28Z  WI-21 DECIDE  docs/findings/WI-21-the-five-questions.md -> because a file called "human-answers" holding five unanswered questions is the one name most likely to be misread; reported as a deviation, one line to flip
05:37:32Z  WI-21 DRAFT   tools/the_questions.py - QUESTIONS (5, every answer None), RULINGS (5, each with its one place), the C-7 warning, parse_options with two caps, a_sitting over build_game
05:37:32Z  WI-21 VERIFY  --checklist opens NO window and prints the whole thing -> exit 0; --seconds 0 / 600 / (4 x 60s run) all refused at parse time -> exit 2, no window
05:37:32Z  WI-21 DECIDE  two caps not one -> MAXIMUM_SECONDS=60 per window AND MAXIMUM_RUN_SECONDS=180 per run, because capping one window still allows four minutes of somebody's screen
05:38:50Z  WI-21 DRAFT   tests/test_the_questions.py - 47 tests: cannot run unbounded, reaps on the failure path, no answer can be recorded, the route to the unbounded game is structurally absent, no fifth copy of the frame binding
05:38:50Z  WI-21 TEST    787 passed, 0 failed, 0 skipped  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py")  [740 on main + 47 new]
05:38:50Z  WI-21 NOTE    two test failures on first run were mine, not the tool's: the checklist is word-wrapped for a person, so a phrase spans a line break; fixed by collapsing whitespace in the assertion, no production change
05:39:27Z  WI-21 COMMIT  5f13fae WI-21: the five questions, and a bounded harness to ask them with
05:39:27Z  WI-21 COMMIT  6c8b7c7 WI-21: the PR summary
05:39:27Z  WI-21 VERIFY  draft PR #66 opened against main -> https://github.com/replicant1/NewTerminalGame/pull/66
05:39:27Z  WI-21 BLOCKED need the screen gate from the conductor: all the non-window work is done, and the harness now has to be run short-first on the real desktop
05:39:57Z  WI-21 NOTE    WI-22 landed while I worked; merged origin/main into the branch, no conflict. frame_for(state) now owns the join; the harness needs no frame of its own, so nothing changed here
05:39:57Z  WI-21 TEST    794 passed, 0 failed, 0 skipped  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py")  [747 on main + 47 mine]
05:39:57Z  WI-21 NOTE    screen gate GRANTED by the conductor; going short-first - one 2s window to prove the mechanics and the reap before anything longer
05:41:41Z  WI-21 DECIDE  the sitting's deadline -> game.session.quit at N s PLUS game.owner.end_session at N s + 1500 ms, because the first is the production --seconds shape and leaves the phase Ended, and the second asks nobody's permission
05:41:41Z  WI-21 VERIFY  window 1/9  the_questions --seconds 2 -> reaped, exit 0, landed (120,120), 400x570, 706 items all "text", 13 frames, phase playing (before the deadline change)
05:41:41Z  WI-21 VERIFY  window 2/9  the_questions --seconds 3 -> reaped, exit 0, held 3.084s, phase ENDED with nothing pressed, 21 frames
05:41:41Z  WI-21 VERIFY  windows 3-6/9  the_questions --sizes 14,16,18,20 --seconds 3 -> 4 opened, 4 reaped, ladder 320x480 / 400x570 / 440x630 / 480x720 EXACTLY as WI-16 measured, all at (120,120), 706 items each
05:41:41Z  WI-21 VERIFY  window 7/9  the_look --view joinery --seconds 3 -> reaped, 714 items all "text" - matches WI-16 exactly
05:41:41Z  WI-21 VERIFY  window 8/9  the_look --view game --seconds 3 -> reaped, 698 items all "text" - matches WI-16 exactly, so WI-22's frame_for is confirmed identical ON SCREEN
05:41:41Z  WI-21 VERIFY  window 9/9  window_manners --exercise keys -> reaped, player moved, z ignored, q ended the session, stdout and stderr empty; WI-22's other on-screen call site confirmed
05:41:41Z  WI-21 VERIFY  after the turn: pgrep found no tool process, System Events counted 0 processes named Python. 9 opened, 9 reaped, no modal sheet
05:41:41Z  WI-21 NOTE    releasing the screen gate to the conductor
05:42:45Z  WI-21 DRAFT   docs/findings/WI-21-the-five-questions.md - all five OPEN, each with its command, what to look for and the one file a reversal lands in
05:42:45Z  WI-21 TEST    795 passed, 0 failed, 0 skipped  (/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py")
05:42:45Z  WI-21 NOTE    answered WI-20b on PR #66: the findings file is docs/findings/WI-21-the-five-questions.md, one document, and I will post there first if the name ever changes
