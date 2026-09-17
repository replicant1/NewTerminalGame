"""Terminal Game — a single-process windowed character grid.

**GAME-1** — *the player guides a single character around a walled maze,
eating the dots laid along its corridors while one ghost roams the same
maze.* That is the whole game, and this is the only place it is written
down: WI-18's audit found GAME-1 claimed by no test, no source and no
docstring, realised by everything and owned by nothing. A summary
requirement still needs somewhere to be stated, or it is an assumption
rather than a claim.

The package is divided into exactly four layers, and the arrow reads
"may import" (IMPLEMENTATION_PLAN.md section 1.3):

    shell -> presentation -> application -> domain

``tools/layer_rule.py`` enforces that by reading the imports of every module
under this package, and ``tests/test_layer_rule.py`` runs it over the real
tree on every suite run.  Nothing may live directly under ``terminal_game``
except this file: code goes in one of the four layer packages, because a
module with no layer is a module the rule cannot judge.
"""

from __future__ import annotations
