"""Terminal Game — a simplified Pac-Man played in a window of its own.

The package is split into a **pure core** and an **impure shell**.

Pure core (no ``curses``, ``time``, ``subprocess``, ``os``, ``sys``,
``pathlib``, no file, clock, terminal, environment or window access):

* :mod:`termgame.model` — the frozen value types every work item speaks.
* :mod:`termgame.maze`  — maze generation and the text-grid loader.

Randomness enters the core only as a ``random.Random`` passed in as a
parameter; there is no module-level ``random.*`` call anywhere in the core.
That is the only reason maze and ghost tests are reproducible.
"""
