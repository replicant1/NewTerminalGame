"""Domain layer — the rules of the game, with nothing around them.

This package names nothing above it.  It imports no windowing toolkit, reads
no clock and creates no randomness: anything that varies is *handed* to it.
That is what lets the maze, the ghost and every scoring and ending rule be
tested with no window anywhere near the test.

What is here so far:

* :mod:`terminal_game.domain.maze` — ``Square``, ``Direction``,
  ``SquareKind`` and the immutable ``Maze``, which owns the query surface the
  rest of the system asks its questions through.
* :mod:`terminal_game.domain.maze_invariants` — MAZE-2, MAZE-3, MAZE-5 and
  MAZE-6 as predicates over a finished grid.
* :mod:`terminal_game.domain.maze_generator` — ``generate_maze``: carve a
  spanning tree, braid away every dead end, verify, then hand the maze out.
"""
