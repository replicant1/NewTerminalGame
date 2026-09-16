"""Terminal Game — a simplified Pac-Man in a window of its own.

The layer dependency rule, fixed by ``docs/IMPLEMENTATION_PLAN.md`` section 1:

    Shell  ->  Presentation  ->  Application  ->  Domain

``terminal_game.shell`` is the only package that may name the windowing
toolkit.
"""
