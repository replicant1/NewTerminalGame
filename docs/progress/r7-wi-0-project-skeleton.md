# WI-0 — project skeleton and the layer rule (developer B, run 7)

WI-0 START   01:34:22Z  developer B begins WI-0 on branch r7/wi-0-project-skeleton, cut from main at 4015c96; non-local mode.
WI-0 READ    01:34:38Z  .claude/agents/developer.md, .claude/shared/progress-tracking.md, .claude/shared/ask-a-human.md
WI-0 READ    01:34:48Z  docs/IMPLEMENTATION_PLAN.md sections 0-5 and 6-10; WI-0 is section 5 iteration M0, lane B
WI-0 VERIFY  01:35:32Z  /usr/bin/python3 is 3.9.6; _tkinter reports TK_VERSION 8.5 TCL_VERSION 8.5; tkinter.TkVersion read with no Tk root constructed, so no window reaches the screen
WI-0 PLAN    01:35:36Z  four layer packages under one top-level package, a .venv built from /usr/bin/python3 with pytest pinned in requirements.txt, pytest.ini so that .venv/bin/python -m pytest -q works from the repo root, and an AST import scanner in tools/ that the layer-rule test drives over the real tree
WI-0 VERIFY  01:35:54Z  .venv created from /usr/bin/python3 is 3.9.6 and keeps _tkinter 8.5; pip install pytest==8.4.2 succeeded over the network; .venv/bin/python -m pytest --version reports pytest 8.4.2
WI-0 DECIDE  01:37:00Z  where the layer-rule scanner lives -> tools/layer_rule.py, outside the package it scans, because a scanner inside terminal_game would have to judge itself and would have to be exempted, which is the first hole anyone would use
WI-0 DECIDE  01:37:03Z  the scanner reads source with ast rather than importing modules -> ast, because importing a presentation module to inspect it would run its module body and under candidate 2 that is exactly the code that could put a window on the user's screen
WI-0 TEST    01:38:11Z  56 passed, 0 failed, 0 skipped  (.venv/bin/python -m pytest -q from the repository root)
WI-0 COMMIT  01:38:37Z  77a6443 WI-0: project skeleton, the pinned runtime, and the layer rule
WI-0 COMMIT  01:39:25Z  70455cc WI-0: PR summary, and the clean-clone setup other developers need; pushed, draft PR #73 opened at https://github.com/replicant1/NewTerminalGame/pull/73
WI-0 VERIFY  01:39:52Z  clean-clone rehearsal in scratch: git clone of the branch, /usr/bin/python3 -m venv .venv, pip install -r requirements.txt, .venv/bin/python -m pytest -q -> 56 passed, 0 failed, 0 skipped; git status clean afterwards, so .venv and .pytest_cache are both ignored
WI-0 NOTE    01:39:56Z  I did not build a venv from the Homebrew python to watch test_the_windowing_binding_is_present go red. Nothing would have been mutated, but the value was marginal and the restraint is cheaper to explain than the exception; the guard's message text is therefore reasoned about, not observed
WI-0 MERGE   01:40:41Z  PR #73 merged to main as f220e62; git fetch origin && git merge origin/main brought S-1's documents down too; whole suite on the merged result: 56 passed, 0 failed, 0 skipped
WI-0 NOTE    01:40:45Z  section 8 steps 4 and 6 cannot both be satisfied from one branch: the MERGE line and its test count only exist after the merge, by which point the branch that carried the log is already merged. Landing the tail of this log and the completion record on a short follow-up branch, r7/wi-0-completion-record
WI-0 DONE    01:40:49Z  WI-0  r7/wi-0-project-skeleton  70455cc (merged to main as f220e62 via PR #73)
