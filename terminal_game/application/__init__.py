"""Application layer: the session controller and the turn resolver.

No toolkit, no clock, no presentation imports.  Ticks and intents arrive as
calls; it reads no time.  It may import from the domain only
(IMPLEMENTATION_PLAN.md section 1.4).
"""
