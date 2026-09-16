"""Presentation layer — composes the picture, never draws it.

Nothing in this package may import a windowing toolkit, and nothing in it may
name the Shell.  Everything it produces is a plain value that can be compared
as text in a test with no window anywhere near it.

What is here so far:

* :mod:`terminal_game.presentation.frame` — ``Colour``, ``Cell``, ``Frame``
  and ``FrameBuilder``: the picture as a 30 x 40 value, and the colour
  vocabulary the whole project draws from (WI-1).
* :mod:`terminal_game.presentation.input_translator` — ``translate``, and the
  **intent vocabulary** ``Intent``, ``IntentKind``, ``QUIT`` and ``move``:
  the four arrows become Move, ``q`` and ``Q`` become Quit, everything else
  becomes nothing (WI-9).

Still to come: the wall glyph resolver (WI-8), the frame composer (WI-12) and
the status line (WI-13).

Two vocabularies other lanes should use rather than redeclare
-------------------------------------------------------------
* **Intents** are :class:`~terminal_game.presentation.input_translator.Intent`
  (WI-9).  WI-15's session controller consumes them.
* **Directions** are *not* declared here.  They are
  :class:`terminal_game.domain.maze.Direction`, landed by WI-5; WI-7's ghost
  policy and WI-9's translator both conform to it, and WI-11 and WI-15 should
  too.
"""
