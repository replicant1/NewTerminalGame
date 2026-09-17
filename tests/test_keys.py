"""Input translation — CTRL-1, CTRL-4, CTRL-5.

Mostly a table, tested as a table. Two parts are worth more than that.

**CTRL-5 is tested against a spread and against near-misses.** Letters,
digits, modifiers, function keys and navigation keys are the spread the plan
asks for; the near-misses — ``"up"``, ``"<Key-Up>"``, ``"Up "`` — are what
pin the contract, because they are the shapes a wiring mistake actually
takes. A translator that lowercased, or that accepted binding names, would
pass the spread and fail these.

**One test asks a real Tk whether these keysyms exist.** The module names no
toolkit and cannot, so the risk it carries is that a key name is simply
misspelled: the arrows would silently stop working and no amount of
table-testing would notice. Tk validates keysym names at bind time, so the
test binds all six on the withdrawn session root — and binds a deliberate
nonsense name too, to show that acceptance means something.
"""

from __future__ import annotations

from typing import List, Optional

import pytest

from terminal_game.application.turn import Intent
from terminal_game.domain.maze import Direction
from terminal_game.presentation.keys import (
    ARROW_INTENTS,
    QUIT_KEYSYMS,
    TRANSLATED_KEYSYMS,
    intent_for,
)

#: The spread the plan asks for: *"letters, digits, modifiers, function
#: keys"*, plus the navigation and whitespace keys a player's hand actually
#: lands on next to the arrows.
MEANINGLESS_KEYSYMS = [
    # letters, including ones adjacent to q on the keyboard
    "a", "w", "s", "d", "z", "A", "W", "P", "R",
    # digits
    "0", "1", "5", "9",
    # modifiers
    "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
    "Meta_L", "Meta_R", "Caps_Lock", "Super_L",
    # function keys
    "F1", "F2", "F5", "F11", "F12",
    # navigation, which sit next to the arrows and are the likeliest misfire
    "Home", "End", "Prior", "Next", "Insert", "Delete",
    # whitespace and control
    "space", "Return", "Tab", "BackSpace", "Escape", "Linefeed",
    # punctuation
    "period", "comma", "slash", "minus", "plus", "question",
    # the numeric keypad's own arrows, which are not the arrow keys
    "KP_Up", "KP_Down", "KP_Left", "KP_Right", "KP_Enter", "KP_5",
]

#: Shapes a wiring mistake takes, rather than keys a player presses.
NEAR_MISSES = [
    "up", "down", "left", "right",          # wrong case
    "UP", "DOWN", "LEFT", "RIGHT",
    "<Key-Up>", "<Up>", "<Key-q>",          # binding names, not keysyms
    "Key-Up", "Up ", " Up", "Up\n",         # not quite a keysym
    "qq", "QQ", "quit", "Q ",
    "",                                      # nothing at all
]


# --------------------------------------------------------------------------
# CTRL-1 — the four arrow keys
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "keysym,intent",
    [
        ("Up", Intent.MOVE_NORTH),
        ("Down", Intent.MOVE_SOUTH),
        ("Left", Intent.MOVE_WEST),
        ("Right", Intent.MOVE_EAST),
    ],
)
def test_each_arrow_key_means_its_move(keysym, intent) -> None:
    assert intent_for(keysym) is intent


@pytest.mark.parametrize(
    "keysym,direction",
    [
        ("Up", Direction.NORTH),
        ("Down", Direction.SOUTH),
        ("Left", Direction.WEST),
        ("Right", Direction.EAST),
    ],
)
def test_each_arrow_key_reaches_the_direction_it_should(keysym, direction) -> None:
    """The whole way through to a direction, because that is what the player
    sees. Up is north, and north is towards row zero."""
    intent = intent_for(keysym)
    assert intent is not None
    assert intent.direction is direction


def test_the_four_arrows_cover_the_four_directions_exactly() -> None:
    """No direction is unreachable and none is reachable two ways."""
    directions = [intent_for(keysym).direction for keysym in ARROW_INTENTS]
    assert set(directions) == set(Direction)
    assert len(directions) == len(set(directions)) == 4


def test_the_arrows_are_the_only_keys_that_move() -> None:
    movers = {k for k in TRANSLATED_KEYSYMS if intent_for(k).is_move}
    assert movers == set(ARROW_INTENTS)


# --------------------------------------------------------------------------
# CTRL-4 — both cases of q
# --------------------------------------------------------------------------


@pytest.mark.parametrize("keysym", ["q", "Q"])
def test_either_case_of_q_quits(keysym) -> None:
    """CTRL-4: *"pressing ``q`` (upper or lower case) quits at once."*"""
    assert intent_for(keysym) is Intent.QUIT


def test_quitting_is_not_a_move() -> None:
    """So a session that dispatches on ``is_move`` cannot walk into a wall
    because somebody pressed q."""
    assert intent_for("q").is_move is False
    assert intent_for("q").direction is None


def test_both_cases_of_q_are_the_same_intent() -> None:
    assert intent_for("q") is intent_for("Q")


# --------------------------------------------------------------------------
# CTRL-5 — everything else means nothing, silently
# --------------------------------------------------------------------------


@pytest.mark.parametrize("keysym", MEANINGLESS_KEYSYMS)
def test_no_other_key_does_anything(keysym) -> None:
    """CTRL-5, over the spread the plan asks for."""
    assert intent_for(keysym) is None


@pytest.mark.parametrize("keysym", NEAR_MISSES)
def test_a_key_name_that_is_nearly_right_still_means_nothing(keysym) -> None:
    """The contract is exact keysyms, and these are the shapes of getting it
    wrong: wrong case, a binding name instead of a keysym, stray whitespace.

    A translator that lowercased its input, or that stripped ``<Key-...>``,
    would pass every other test in this file and fail here — which is the
    point of having them.
    """
    assert intent_for(keysym) is None


def test_the_spread_does_not_accidentally_contain_a_real_key() -> None:
    """Otherwise the sweep above would be asserting something false and the
    fixture, not the code, would be what was wrong."""
    overlap = set(MEANINGLESS_KEYSYMS + NEAR_MISSES) & set(TRANSLATED_KEYSYMS)
    assert overlap == set()


def test_only_six_keys_mean_anything_at_all() -> None:
    assert len(TRANSLATED_KEYSYMS) == 6
    assert set(TRANSLATED_KEYSYMS) == set(ARROW_INTENTS) | set(QUIT_KEYSYMS)


def test_a_meaningless_key_is_discarded_silently(capsys) -> None:
    """CTRL-5's second half: *"nothing typed is echoed."*

    Not merely that nothing is drawn — that nothing is written anywhere at
    all. A translator that logged unknown keys would be echoing them
    somewhere a player could eventually find them.
    """
    for keysym in MEANINGLESS_KEYSYMS + NEAR_MISSES:
        intent_for(keysym)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_translation_keeps_no_record_of_what_it_was_asked() -> None:
    """A pure lookup: asking twice gives the same answer, and asking about
    one key does not change the answer for another."""
    assert intent_for("Up") is Intent.MOVE_NORTH
    for keysym in MEANINGLESS_KEYSYMS:
        intent_for(keysym)
    assert intent_for("Up") is Intent.MOVE_NORTH
    assert intent_for("Zzz") is None


def test_the_translation_table_cannot_be_changed_through_a_returned_value() -> None:
    """``ARROW_INTENTS`` is handed out; a caller that mutated it would change
    what the arrow keys do for everybody."""
    borrowed = dict(ARROW_INTENTS)
    borrowed["Up"] = Intent.QUIT
    assert intent_for("Up") is Intent.MOVE_NORTH


# --------------------------------------------------------------------------
# The one test that asks the toolkit whether these keys exist
# --------------------------------------------------------------------------


def test_every_translated_keysym_is_one_tk_recognises(tk_root) -> None:
    """The risk this module carries that a table cannot catch: a misspelling.

    ``keys.py`` names no toolkit — the Presentation layer's rule forbids it —
    so nothing else checks that ``"Up"`` is what Tk actually calls that key.
    If it were ``"UpArrow"``, every other test here would pass and the arrows
    would do nothing in the finished game.

    Tk validates keysym names when a binding is registered, so registering
    all six is the check. No window: the session root is withdrawn before the
    first turn of the event loop, and no event is generated or delivered.
    """
    for keysym in TRANSLATED_KEYSYMS:
        tk_root.bind("<Key-{}>".format(keysym), lambda event: None)


def test_tk_rejects_a_keysym_that_does_not_exist(tk_root) -> None:
    """So that the test above means something.

    Without this, a Tk that accepted any string at all would make the check
    vacuous and a misspelling would sail through it.
    """
    with pytest.raises(Exception) as raised:
        tk_root.bind("<Key-NotARealKeysym>", lambda event: None)
    assert "keysym" in str(raised.value)
