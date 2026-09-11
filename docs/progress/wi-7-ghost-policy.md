02:28:51Z  START   WI-7 ghost movement policy — branch wi-7-ghost-policy cut from main 4d88d47
02:29:03Z  READ    plan §5 WI-7 brief — three clauses, five test obligations, GHOST-4 the keystone
02:31:01Z  READ    ARCHITECTURE 5.4 — move_ghost(state, rng); END-5 guard first, collision test last
02:31:04Z  READ    FR GHOST-1..4, SCORE-4, END-1, END-5 — source of truth; model.py and rules.py (WI-5) read; Maze already answers every corridor question I need
02:31:06Z  NOTE    boundary with Dev A: they own move_player, I own move_ghost. I add NO shared helper — Maze.is_open/open_directions and Direction.opposite already cover it. Expected conflict points are __all__ and the module docstring header, both one-line and mechanical.
02:31:09Z  PLAN    append ghost_heading() + move_ghost() to termgame/rules.py; five hand-built boards (straight, cross plus isolated player pocket, T-junction, stub cul-de-sac, dotted) in a new tests/test_rules_ghost.py
02:31:56Z  COMMIT  76d3265 WI-7: the ghost's movement policy — ghost_heading() and move_ghost()
02:32:18Z  NOTE    pushed wi-7-ghost-policy; draft PR #11 open — https://github.com/replicant1/NewTerminalGame/pull/11
02:39:14Z  TEST    49 tests, 2 failed, 0 skipped (own file only) — one my bug, one a real finding
02:39:18Z  NOTE    FINDING: on the regular CROSS lattice the ghost makes at most ONE genuine random choice and then locks into a decision-free cycle — measured: every (start, heading) on CROSS yields <=1 choice in 200 ticks. A GHOST-4 test on such a board is near-vacuous: a hunting ghost would have nothing to hunt at. Replacing it with a hand-built CIRCUIT board (20 choices in 200 ticks, measured) plus a real generated maze (13-15 in 300, measured).
02:39:23Z  NOTE    conductor relays WI-6 merged (main 515/2). My END-5 guard already returns the identical object, matching Dev A's CTRL-3 choice. Will merge origin/main once my own file is green.
02:41:17Z  TEST    52 passed, 0 failed, 0 skipped (tests/test_rules_ghost.py alone) — GHOST-4 now on the CIRCUIT board and on a real generated maze, both proven non-vacuous by seed-sensitivity
