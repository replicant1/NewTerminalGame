# -*- coding: utf-8 -*-
"""WI-22 — the join: a game state in, the *whole* picture out.

This module holds one function and it exists for one reason.  SCRN-1 says
the window is **29 rows of maze with a status line under it**.  Until now
that was true of the running game only as two statements that happened to
agree: WI-12 owned rows 0–28 and placed whatever row 29 it was handed, WI-13
owned row 29 as a value, and **nobody owned the join**.  Every caller bound
the two together itself, so the two lines below existed in four places — one
in production and three in tools and test apparatus.

Amendment 10 of the implementation plan names that as a seam the plan
specified and no work item was asked to build:

    Turning a game state into a *complete* frame … belongs in Presentation,
    as a single ``state -> frame`` function … the only place SCRN-1's "top
    29 rows maze, bottom row status" is true as one statement rather than
    as two halves that happen to agree.

So this is where SCRN-1 is now asserted once.

What this module owns, and what it very deliberately does not
--------------------------------------------------------------
It owns **the join and nothing else**.  It decides that the status row
handed to the composer is the one built from *this* state's score and
outcome, and that is the whole of its content.

* **Rows 0–28 are WI-12's**, in
  :func:`~terminal_game.presentation.frame_composer.compose_frame`.  Not one
  glyph, colour or column is chosen here.
* **Row 29 is WI-13's**, in
  :func:`~terminal_game.presentation.status_line.status_row`.  **There is no
  status-line literal in this file and there must never be one** — A7
  confines every one of them to WI-13, and this module is precisely the kind
  of place where a second copy would be tempting.

The consequence for the suite, which is the point of writing it this way: a
defect in the wall glyphs turns WI-8's tests red, a defect in the status text
turns WI-13's red, and a defect in *the join* turns this module's tests red.
One defect, one file.

Layer
-----
Presentation.  It may name Application and Domain; it names no toolkit and
no part of the Shell.  It draws nothing — it returns a value, and the Shell's
surface is the only thing that turns that value into pixels.
"""

from __future__ import annotations

from ..domain.game_state import GameState
from .frame import Frame
from .frame_composer import compose_frame
from .status_line import status_row

__all__ = ["frame_for"]


def frame_for(state: GameState) -> Frame:
    """The whole picture for *state*: maze above, status line below.

    This is WI-15's ``compose`` seam — *a game state in, a frame out* — and
    the one place the two halves of SCRN-1 are put together.  Callers that
    want a picture of a game ask for it here rather than composing it
    themselves; the Shell's composition root, the headless game apparatus and
    the on-screen tools all go through this function.

    Nothing is taken from the state and nothing in it is modified: composing
    a picture is a question, not a move.
    """
    return compose_frame(state, status_row(state.score.points, state.outcome))
