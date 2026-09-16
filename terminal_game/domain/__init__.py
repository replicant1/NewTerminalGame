"""Domain layer — the rules of the game, with nothing around them.

This package names nothing above it.  It imports no windowing toolkit, reads
no clock and creates no randomness: anything that varies is *handed* to it.
That is what lets the maze, the ghost and every scoring and ending rule be
tested with no window anywhere near the test.

What is here so far:

* :mod:`terminal_game.domain.maze` — ``Square``, ``Direction``,
  ``SquareKind`` and the immutable ``Maze``, which owns the query surface the
  rest of the system asks its questions through (WI-5).
* :mod:`terminal_game.domain.maze_invariants` — MAZE-2, MAZE-3, MAZE-5 and
  MAZE-6 as predicates over a finished grid (WI-5).
* :mod:`terminal_game.domain.maze_generator` — ``generate_maze``: carve a
  spanning tree, braid away every dead end, verify, then hand the maze out
  (WI-5).
* :mod:`terminal_game.domain.dot_field` — ``DotField``, the dots along the
  corridors and what happens when one is taken (WI-6).
* :mod:`terminal_game.domain.game_state` — ``Score``, ``Outcome`` and
  ``GameState``, the vocabulary a game is carried in.  It is a **value**: a
  rule that must change nothing is asserted by comparing two whole states
  (WI-6).
* :mod:`terminal_game.domain.opening_position` — where everything stands the
  moment the window opens, as a pure function of the maze (WI-6).

Still to come: the ghost's movement policy (WI-7) and the turn resolver, in
which the fixed order of the rules of a turn lives in one readable place
(WI-11).
"""
