"""Terminal Game — a single-process windowed character grid.

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
