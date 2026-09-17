"""Presentation — everything the player sees, expressed as data.

May import Application and Domain.  Everything it produces is **data** — a
field of glyphs and colours — except for the single responsibility that
actually paints, which is the only part of Presentation permitted to name the
toolkit.  That one module is named once, in ``tools/layer_rule.PAINTING_MODULE``;
WI-5 owns it and may rename it there, in that one place.

Enforced by ``tools/layer_rule.py``; see IMPLEMENTATION_PLAN.md section 1.3.
"""

from __future__ import annotations
