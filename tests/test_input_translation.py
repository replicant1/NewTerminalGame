"""WI-6: input translation (CTRL-1, CTRL-4, CTRL-5).

Key names are Tk keysyms, as the shell delivers them (lane C, PR #123:
``Window.run`` passes ``event.keysym`` to ``on_key``).
"""

from __future__ import annotations

import string

import pytest

from terminal_game.presentation.input_translation import (MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT,
                                                          MOVE_UP, NOTHING, QUIT, translate)


@pytest.mark.parametrize("key, intent", [
    ("Up", MOVE_UP), ("Down", MOVE_DOWN), ("Left", MOVE_LEFT), ("Right", MOVE_RIGHT),
])
def test_c1_the_arrow_keys_translate_to_the_four_moves(key, intent):
    assert translate(key) == intent


def test_c1_the_four_moves_are_four_different_intents():
    assert len({translate(k) for k in ("Up", "Down", "Left", "Right")}) == 4


@pytest.mark.parametrize("key", ["q", "Q"])
def test_c2_q_and_Q_both_translate_to_quit(key):
    """Caps Lock on, or Shift held, makes Tk report ``Q``; either way it is quit."""
    assert translate(key) == QUIT


# Tk keysyms for every other kind of key the claim names.
NAMED_OTHERS = [
    "space", "Return", "KP_Enter", "Escape", "Tab", "ISO_Left_Tab", "BackSpace", "Delete",
    *["F%d" % n for n in range(1, 21)],
    "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L", "Meta_R",
    "Super_L", "Super_R", "Caps_Lock", "Num_Lock", "Mode_switch",
    "Home", "End", "Prior", "Next", "Insert", "Help", "Menu",
    "KP_Up", "KP_Down", "KP_Left", "KP_Right",
    "comma", "period", "slash", "minus", "equal", "bracketleft", "bracketright",
    "semicolon", "apostrophe", "grave", "backslash", "exclam", "at", "numbersign",
]
LETTERS_AND_DIGITS = [c for c in string.ascii_letters + string.digits if c not in "qQ"]
LOOKALIKES = ["up", "UP", "down", "left", "right", "Quit", "quit", "qq", " q", "q ", "", "Q\n"]


@pytest.mark.parametrize("key", NAMED_OTHERS + LETTERS_AND_DIGITS + LOOKALIKES)
def test_c3_every_other_key_translates_to_nothing(key):
    assert translate(key) is NOTHING


def test_c3_only_six_key_names_translate_to_anything():
    """Across every key name above plus the six, exactly the six give an intent."""
    names = NAMED_OTHERS + LETTERS_AND_DIGITS + LOOKALIKES + ["Up", "Down", "Left", "Right", "q", "Q"]
    assert sorted(k for k in names if translate(k) is not NOTHING) == \
        sorted(["Up", "Down", "Left", "Right", "q", "Q"])


@pytest.mark.parametrize("value", [None, 81, b"q"])
def test_something_that_is_not_a_key_name_translates_to_nothing(value):
    assert translate(value) is NOTHING
