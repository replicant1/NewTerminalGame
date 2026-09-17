"""Developer tooling that is not part of the game.

Nothing under ``terminal_game`` may import anything from here: this package
exists for the test suite and for audits, and it is deliberately outside the
tree that ``layer_rule`` scans.
"""

from __future__ import annotations
