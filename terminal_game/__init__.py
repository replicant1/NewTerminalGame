"""Terminal Game — a simplified Pac-Man in a window of its own.

The layer dependency rule is fixed by the implementation plan and is not
negotiable inside a work item:

    shell  ->  presentation  ->  application  ->  domain

* ``domain`` names nothing above it, imports no windowing toolkit, reads no
  clock and creates no randomness — it is handed a random source.
* ``application`` may name ``domain`` and nothing above it.
* ``presentation`` may name ``application`` and ``domain``.  **It may not
  import the windowing toolkit.**
* ``shell`` is the only package in which the windowing toolkit may be named.

The one seam the whole test strategy hangs off: *the frame is a value*.  The
presentation layer does not draw, it returns a picture (see
:mod:`terminal_game.presentation.frame`).  The shell's surface is the only
thing that turns that value into pixels.
"""
