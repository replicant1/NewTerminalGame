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
