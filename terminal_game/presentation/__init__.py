"""Presentation layer — composes the picture, never draws it.

Nothing in this package may import a windowing toolkit, and nothing in it may
name the Shell.  Everything it produces is a plain value that can be compared
as text in a test with no window anywhere near it.

What is here — all of it; nothing in this package is still to come:

* :mod:`terminal_game.presentation.frame` — ``Colour``, ``Cell``, ``Frame``
  and ``FrameBuilder``: the picture as a 30 x 40 value, and the colour
  vocabulary the whole project draws from (WI-1).
* :mod:`terminal_game.presentation.input_translator` — ``translate``, and the
  **intent vocabulary** ``Intent``, ``IntentKind``, ``QUIT`` and ``move``:
  the four arrows become Move, ``q`` and ``Q`` become Quit, everything else
  becomes nothing (WI-9).
* :mod:`terminal_game.presentation.wall_glyphs` — the double-line glyphs a
  wall square is drawn as, the connector rule, and ``wall_layer``: the whole
  wall skeleton as cells (WI-8).
* :mod:`terminal_game.presentation.frame_composer` — ``compose_frame``: a
  game state becomes rows 0–28, with the dots and the two actor motifs laid
  over WI-8's wall layer and row 29 placed exactly as it is handed over
  (WI-12).
* :mod:`terminal_game.presentation.status_line` — ``status_row`` and
  ``status_text``: row 29 as a value, and **the only status-line literals
  in the project** (WI-13).
* :mod:`terminal_game.presentation.picture` — ``frame_for``: **a game state
  in, the whole picture out.**  Rows 0–28 from the composer with row 29
  under them, and the one place SCRN-1 is a single statement rather than
  two halves that happen to agree (WI-22).
* :mod:`terminal_game.presentation.specimen` — the specimen picture from
  ``docs/FUNCTIONAL_REQUIREMENTS.md`` as data, normative for the
  grid-to-screen mapping under assumption A6.  Data, not behaviour.

**If you want a complete frame for a game state, call ``frame_for``.**  The
Shell's composition root, the headless game apparatus and the on-screen
tools all go through it; writing ``compose_frame(state, status_row(...))``
anywhere else is the duplication WI-22 removed.

Vocabularies other lanes should use rather than redeclare
----------------------------------------------------------
* **Intents** are :class:`~terminal_game.presentation.input_translator.Intent`
  (WI-9).  WI-15's session controller consumes them.
* **Wall glyphs and the connector rule** are WI-8's, in
  :mod:`~terminal_game.presentation.wall_glyphs`; the composer declares none
  of them and takes ``wall_layer`` whole.
* **The dot glyph and the two actor motifs** are WI-12's, in
  :mod:`~terminal_game.presentation.frame_composer`; WI-8 declares none of
  them.
* **Row 29** is WI-13's and arrives as a value.  No module here and no test
  here may contain a status-line literal.
* **Directions** are *not* declared here.  They are
  :class:`terminal_game.domain.maze.Direction`, landed by WI-5; WI-7's ghost
  policy and WI-9's translator both conform to it, and WI-11 does too.
"""
