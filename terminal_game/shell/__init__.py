"""Shell — the window, the event loop, the tick timer and the entry point.

May import anything.  It is the only layer with no restriction, which is
exactly why it should stay thin: whatever can be moved down out of here
becomes testable without a window.

See IMPLEMENTATION_PLAN.md section 1.3.
"""

from __future__ import annotations
