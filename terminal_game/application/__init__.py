"""Application — the session controller and the turn resolver.

Of the four layers it may import Domain and itself, and no other.  No
toolkit.  No clock: a tick *arrives as a call*, it is never read from a clock.

Enforced by ``tools/layer_rule.py``; see IMPLEMENTATION_PLAN.md section 1.3.
"""

from __future__ import annotations
