# WI-1 — the maze as data (developer B, run 7)

WI-1 START   01:42:56Z  developer B begins WI-1 on branch r7/wi-1-maze-grid; non-local mode, lane B, iteration M0.
WI-1 NOTE    01:43:05Z  branched from origin/main at c76bc37, not the c3c6c55 my brief named: S-1's PR #75 landed between the brief being written and my fetch. Branching from the tip is what 'from main' means and avoids missing what landed
WI-1 VERIFY  01:43:13Z  baseline on the branch before writing anything: .venv/bin/python -m pytest -q -> 56 passed, 0 failed, 0 skipped, matching what the conductor named
WI-1 READ    01:43:21Z  docs/FUNCTIONAL_REQUIREMENTS.md section 4: MAZE-1 19 across x 29 deep, MAZE-2 each square corridor or wall with one-square-wide axis-aligned corridors, MAZE-3 solid border ring, MAZE-5 at least two ways on from any corridor square, MAZE-6 all corridor squares mutually reachable
WI-1 DECIDE  01:44:02Z  how a maze is stored -> the frozenset of its corridor squares, everything else wall, because it makes MAZE-2 structural rather than remembered and makes carving a cheap set union
WI-1 DECIDE  01:44:06Z  whether 19x29 is a constructor argument -> no, module constants only, because MAZE-1's 'no other shape is representable' is a property of the type and a size parameter would make it a property of every call site
WI-1 DECIDE  01:44:21Z  what the checker returns -> which squares fail each of the three questions, not three booleans, because WI-2's repair loop opens a wall to remove a dead end and thereby changes connectivity, and a generator told only 'not sound' cannot tell whether its last repair helped
WI-1 TEST    01:45:58Z  149 passed, 0 failed, 0 skipped  (.venv/bin/python -m pytest -q from the repository root; 56 inherited from main, 93 new)
WI-1 NOTE    01:46:02Z  my first RING_WITH_A_STUB picture hung the stub off a corner, so it touched the ring at two points and had two ways on: no dead end at all, and four tests failed on it. The picture was wrong, not the checker. Kept the mistaken shape as its own test so nobody later 'fixes' the checker towards it
WI-1 VERIFY  01:46:16Z  WI-0's layer-rule test is no longer vacuous: the scanner now reads real imports off the tree, including terminal_game.domain.structure importing terminal_game.domain.maze, an intra-layer import the rule permits. check_package('terminal_game') returns no violations and the domain names only __future__, enum and typing
WI-1 COMMIT  01:46:42Z  10074c8 WI-1: the maze as data, and the structural checker WI-2 will ask; pushed to origin
