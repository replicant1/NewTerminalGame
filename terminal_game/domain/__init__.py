"""Domain — the rules of the game, and nothing else.

Imports nothing from the three layers above it and nothing impure: no
windowing toolkit, no clock, no filesystem, no environment, no process.  It
does not reach for a module-level random source either — **randomness arrives
as an argument**, which is what makes MAZE-4/5/6 and every ``END-*`` rule
testable with no window and no clock.

Enforced by ``tools/layer_rule.py``; see IMPLEMENTATION_PLAN.md section 1.3.
"""

from __future__ import annotations
