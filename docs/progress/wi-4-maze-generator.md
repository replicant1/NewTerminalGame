# WI-4 — the maze model and its generator (DEV-B, iteration M0)

Local mode. No push, no `gh`, no merge. Branch `wi-4-maze-generator`, cut from `main` at `5269b67`.

05:07:24Z  START   WI-4, the maze model and its generator. Head of the critical path (WI-7, WI-5a, WI-9 depend on it).
05:07:40Z  READ    docs/IMPLEMENTATION_PLAN.md §2 runtime (Python 3.9.6, stdlib only, unittest), §3 the layer rule, §4 ground rules, §7 M0 and the WI-4 row, §11 amendments after M0.
05:07:55Z  READ    docs/FUNCTIONAL_REQUIREMENTS.md MAZE-1..MAZE-6 — 19 across by 29 deep, one-square corridors, solid border, random per game, no dead ends, fully connected.
05:08:00Z  READ    docs/ARCHITECTURE.md C5 (no screen geometry in the domain) and C8 (braid on the odd lattice only; 0 2x2 blocks, 0 dead ends, full connectivity over 300 mazes measured with the restriction, no guarantee without).
05:08:05Z  READ    main:tests/test_layering.py — its `imports(source, module_name)` helper already takes the module name as a parameter, so the domain-purity cases are a new list and a new test method, not new machinery.
05:08:08Z  READ    docs/prs/PR-WI-2-screen-port.md — the same lane's previous item; naming and docstring conventions taken from it.
05:08:10Z  NOTE    Three corrections the conductor flagged on main, carried and not acted on: the "Agreed with DEV-B" section in PR-WI-1 never happened; the claim that tests/__init__.py must be empty is false (it must exist — leaving it exactly as it is, 81 bytes); the launcher half of the layer rule is WI-12's gap, not mine.
05:08:15Z  PLAN    A pure `terminalgame/domain/` package: `maze.py` (the immutable model, four-sided neighbour queries) and `maze_generator.py` (border-preserving spanning-tree carve on the odd lattice, then a braid restricted to that same lattice). Tests: tests/test_maze.py, tests/test_maze_generator.py, plus domain-purity cases appended to tests/test_layering.py.
05:08:15Z  WEIGH   where the domain lives : a new top-level package vs a sub-package of terminalgame — chose terminalgame/domain/ so the layering test has one obvious root to walk and the purity rule is visible in the tree.
05:08:15Z  DECIDE  the 2x2 problem -> never open a square whose x and y are both even, because every 2x2 block of squares contains exactly one such square, so MAZE-2 holds by construction rather than by measurement (this is C8 restated as an invariant).
05:08:50Z  DRAFT   terminalgame/domain/__init__.py, maze.py (Maze, Direction, WIDTH 19, HEIGHT 29, neighbours/open_neighbours/ways_on/reachable_from/as_text/from_text) and maze_generator.py (generate_maze, generate_maze_with, MazeTooSmall).
05:09:00Z  VERIFY  Ad-hoc sweep of seeds 0..299 before writing any test: 0 size failures, 0 border breaches, 0 2x2 open blocks, 0 dead ends, 0 disconnected mazes; 300 distinct layouts; 259..271 corridor squares; 0.768 s for all 300 including every check, i.e. 2.6 ms per maze.
05:09:04Z  DECIDE  default sweep size -> 400 seeds in the ordinary run, because 300 with full checking cost 0.77 s, so 400 costs about 1 s and still leaves `python3 -m unittest discover` quick; a longer sweep goes behind the MAZE_SWEEP_SEEDS environment variable rather than into the default run.
