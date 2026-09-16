"""Tests for the Domain layer.

The Domain names nothing above it, so **no test in this package needs a
window, a clock or a global random source**, and none uses one.  Anything
that varies is handed in: a maze comes from a seeded ``random.Random``, and
the same seed twice gives the same maze.
"""
