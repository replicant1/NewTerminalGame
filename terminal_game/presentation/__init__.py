"""Presentation layer: frame composition, wall glyphs, the status line and input
translation.

Pure: it turns state into characters and colour roles, and key names into
intents.  No toolkit, no operating-system API.  It may import from the
application and the domain, never from the shell (IMPLEMENTATION_PLAN.md
section 1.4).
"""
