"""The Presentation layer: a domain state turned into characters and colours.

This is where screen geometry lives — two terminal columns to a maze square,
three-column actor glyphs, the 40 x 30 frame — precisely so that none of it is
in the Domain (architecture caution C5). Presentation reads the Domain and
never the other way about: nothing under `terminalgame/domain/` imports
anything from here, and `tests/test_layering.py` holds both halves of that to
account.

Presentation reads a key from nobody, writes to no terminal and sleeps never.
It knows the *names* of the colours the specification asks for, which live in
the screen port, but nothing about how a terminal produces them.
"""
