"""The colours the specification names, as pixels.

Six requirements name a colour in words, and somebody has to turn each word
into a number.  This module is the one place that happens, so that a colour is
changed here and nowhere else:

===========  =================================  ========================
Requirement  What it says                       Constant
===========  =================================  ========================
WIN-2        "on a black background"            :data:`GROUND`
SCRN-3       "blue double lines"                :data:`WALL`
SCRN-4       "a small dim gold square"          :data:`DOT`
SCRN-5       "a bright yellow block"            :data:`PLAYER`
SCRN-5       "a pink block"                     :data:`GHOST`
SCRN-6       "written in cyan"                  :data:`STATUS`
===========  =================================  ========================

**These were chosen by eye, like the font size**, and that is stated rather
than hidden.  Three of them are not really choices at all — black, bright
yellow and cyan each have one obvious answer.  The other three are a reading
of an adjective, and each one was picked so a reader can check the reasoning
rather than take it on trust:

* **blue** is the arcade maze blue the specimen picture is drawn in the style
  of, rather than a pure ``#0000ff`` that glares;
* **dim gold** is CSS ``darkgoldenrod`` — gold with the brightness taken out,
  which is exactly what the adjective asks for;
* **pink** is CSS ``hotpink``, which reads as pink beside bright yellow rather
  than as a pale wash on black.

If a human looks at the running game and disagrees with any of them, the fix is
one constant here and the test that quotes it.  That is the same shape as
assumption P4 for the font size.

**Every colour is written as ``#rrggbb``** and not as a toolkit colour name.
Names like ``"pink"`` are resolved by the toolkit, which means the pixel a
player sees would depend on the toolkit's own table rather than on this file,
and a test could only assert the name back.  A hex triple is the colour.

Nothing here imports anything.  The colours are data, which is what lets the
whole Presentation layer above the painter stay data too.
"""

from __future__ import annotations

from typing import Dict, FrozenSet

# --------------------------------------------------------------------------
# The ground
# --------------------------------------------------------------------------

#: WIN-2's black background.  This is the colour of every cell that has nothing
#: in it, and the colour behind every glyph that does.
GROUND = "#000000"

# --------------------------------------------------------------------------
# The things drawn on it
# --------------------------------------------------------------------------

#: SCRN-3's blue, for the double-line wall glyphs and the lone block.
WALL = "#2121de"

#: SCRN-4's dim gold, for the dot on an uneaten corridor square.  CSS
#: ``darkgoldenrod``.  It has to stay legible on :data:`GROUND` while still
#: reading as *dim* beside :data:`PLAYER`, which is the brightest thing on the
#: screen and sometimes sits right next to it.
DOT = "#b8860b"

#: SCRN-5's bright yellow, for the player.
PLAYER = "#ffff00"

#: SCRN-5's pink, for the ghost.  CSS ``hotpink``.  SCRN-5 asks that the two
#: actors "can be told apart by colour and by outline", so this has to differ
#: from :data:`PLAYER` in hue and not merely in brightness — which it does, and
#: :func:`distinct_actor_colours` is the check that says so.
GHOST = "#ff69b4"

#: SCRN-6's cyan, for row 29.
STATUS = "#00ffff"


#: Every colour this project draws with, by the name the requirements use for
#: it.  A painter never needs this — it asks for the constant it wants — but a
#: test that walks every colour does, and so does anyone auditing which
#: requirement a colour belongs to.
BY_REQUIREMENT = {
    "WIN-2": GROUND,
    "SCRN-3": WALL,
    "SCRN-4": DOT,
    "SCRN-5 player": PLAYER,
    "SCRN-5 ghost": GHOST,
    "SCRN-6": STATUS,
}  # type: Dict[str, str]

#: Every colour, without the requirement labels.
ALL_COLOURS = frozenset(BY_REQUIREMENT.values())  # type: FrozenSet[str]


def is_colour(value: object) -> bool:
    """Whether ``value`` is a ``#rrggbb`` triple this module would accept.

    The painter uses this to refuse anything that is not a colour before it
    reaches the toolkit, so that a mistake fails where it was made rather than
    as a Tcl error several frames later.
    """
    if not isinstance(value, str):
        return False
    if len(value) != 7 or not value.startswith("#"):
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value[1:])


def distinct_actor_colours() -> bool:
    """Whether SCRN-5's two actors differ in colour, which they must.

    SCRN-5 asks for the player and the ghost to be distinguishable "by colour
    and by outline".  The outline half is a matter of which glyphs WI-4 picks;
    the colour half is settled here, and this is the question in a form a test
    can ask.
    """
    return PLAYER != GHOST
