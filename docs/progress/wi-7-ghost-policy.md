02:28:51Z  START   WI-7 ghost movement policy — branch wi-7-ghost-policy cut from main 4d88d47
02:29:03Z  READ    plan §5 WI-7 brief — three clauses, five test obligations, GHOST-4 the keystone
02:31:01Z  READ    ARCHITECTURE 5.4 — move_ghost(state, rng); END-5 guard first, collision test last
02:31:04Z  READ    FR GHOST-1..4, SCORE-4, END-1, END-5 — source of truth; model.py and rules.py (WI-5) read; Maze already answers every corridor question I need
02:31:06Z  NOTE    boundary with Dev A: they own move_player, I own move_ghost. I add NO shared helper — Maze.is_open/open_directions and Direction.opposite already cover it. Expected conflict points are __all__ and the module docstring header, both one-line and mechanical.
02:31:09Z  PLAN    append ghost_heading() + move_ghost() to termgame/rules.py; five hand-built boards (straight, cross plus isolated player pocket, T-junction, stub cul-de-sac, dotted) in a new tests/test_rules_ghost.py
