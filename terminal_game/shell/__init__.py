"""Shell layer — the window, the event loop, and the pixels.

This is the **only** package in which the windowing toolkit may be named, and
even here it is confined to the modules that must have it
(:mod:`terminal_game.shell.tk_grid` is one).  Everything else in the shell
takes its collaborator as an argument, so it can be driven by a recording
double in a test with no window anywhere.

**No automated test in this project may construct a toolkit window.**  Not
once, not withdrawn, not "just to check".  Anything that has to appear on
screen is a separate script a person runs deliberately, and it is never named
``test_*``.

Responsibility boundary inside the shell (implementation plan, WI-2/WI-3):

* **The window owner** owns the window, the tick timer and key delivery.
* **The character grid surface** owns everything inside the pixels.

The surface tells the window owner how many pixels it needs; the window owner
tells the surface nothing about the game.  Neither reaches into the other.
"""
