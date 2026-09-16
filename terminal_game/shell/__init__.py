"""The Shell: the window, the event loop, the tick timer, key delivery, and
the pixels.

This is the only layer permitted to name the windowing toolkit, and within it
only two modules actually do: :mod:`terminal_game.shell.tk_toolkit` (the
window, the timer and key events — WI-3) and
:mod:`terminal_game.shell.tk_grid` (the drawing — WI-2).  Everything else in
the shell takes its collaborator as an argument, so it can be driven by a
recording double in a test with no window anywhere.

**No automated test in this project may construct a toolkit window.**  Not
once, not withdrawn, not "just to check".  Anything that has to appear on
screen is a separate script a person runs deliberately, and it is never named
``test_*``.

Responsibility boundary inside the shell (implementation plan, WI-2 / WI-3):

* **The window owner** owns the window, the tick timer and key delivery.
* **The character grid surface** owns everything inside the pixels.

The surface works out how many pixels 40 x 30 character cells need and the
window owner is *told* that number; the window owner tells the surface nothing
about the game.  The one thing that crosses is the drawing target that
:meth:`WindowOwner.open` returns, which is what the surface paints into.
"""
