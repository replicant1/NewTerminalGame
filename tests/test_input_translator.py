# -*- coding: utf-8 -*-
"""WI-9 — the input translator."""

from __future__ import annotations

import contextlib
import io
import unittest

from terminal_game.domain.maze import Direction
from terminal_game.presentation.input_translator import (
    ARROW_KEYS,
    QUIT,
    QUIT_KEYS,
    Intent,
    IntentKind,
    move,
    translate,
)

#: A representative spread of keys the game must ignore, as the toolkit
#: reports them: (keysym, char).  Letters, digits, punctuation, whitespace,
#: the editing and navigation keys, the function keys, the modifier keys
#: themselves, and modified keys.
IGNORED_KEYS = [
    # letters, including the ones next to q on the keyboard
    ("a", "a"), ("w", "w"), ("s", "s"), ("d", "d"), ("z", "z"),
    ("A", "A"), ("W", "W"), ("Z", "Z"),
    # digits
    ("0", "0"), ("1", "1"), ("9", "9"),
    # punctuation and whitespace
    ("space", " "), ("Return", "\r"), ("Tab", "\t"), ("period", "."),
    ("comma", ","), ("slash", "/"), ("minus", "-"),
    # editing and navigation
    ("Escape", "\x1b"), ("BackSpace", "\x08"), ("Delete", "\x7f"),
    ("Home", ""), ("End", ""), ("Prior", ""), ("Next", ""),
    # function keys
    ("F1", ""), ("F5", ""), ("F12", ""),
    # the modifier keys themselves
    ("Shift_L", ""), ("Control_L", ""), ("Alt_L", ""), ("Meta_L", ""),
    ("Caps_Lock", ""), ("Super_L", ""),
    # modified letters: the keysym survives, the character does not
    ("q", "\x11"), ("Q", "\x11"), ("c", "\x03"), ("d", "\x04"),
    # a keysym that is nearly an arrow but is not one
    ("Up_", ""), ("up", ""), ("UP", ""), ("KP_Up", ""), ("Uparrow", ""),
    # nothing at all
    ("", ""),
]


class TheFourArrowKeys(unittest.TestCase):
    """CTRL-1 — each arrow moves the player one square in its own direction."""

    def test_up_is_north(self):
        self.assertEqual(move(Direction.NORTH), translate("Up", ""))

    def test_down_is_south(self):
        self.assertEqual(move(Direction.SOUTH), translate("Down", ""))

    def test_left_is_west(self):
        self.assertEqual(move(Direction.WEST), translate("Left", ""))

    def test_right_is_east(self):
        self.assertEqual(move(Direction.EAST), translate("Right", ""))

    def test_the_four_arrows_map_to_four_different_directions(self):
        directions = {
            translate(keysym, "").direction for keysym in ARROW_KEYS
        }

        self.assertEqual(set(Direction), directions)

    def test_up_moves_up_the_screen_and_down_moves_down_it(self):
        # The one way to get this wrong is to mix up the row axis, so say it
        # in terms of the row rather than in terms of the name.
        self.assertEqual(-1, translate("Up", "").direction.row_step)
        self.assertEqual(1, translate("Down", "").direction.row_step)
        self.assertEqual(-1, translate("Left", "").direction.column_step)
        self.assertEqual(1, translate("Right", "").direction.column_step)

    def test_an_arrow_is_a_move_and_carries_a_direction(self):
        intent = translate("Left", "")

        self.assertEqual(IntentKind.MOVE, intent.kind)
        self.assertIsNotNone(intent.direction)


class TheQuitKey(unittest.TestCase):
    """CTRL-4 — `q`, upper or lower case, quits."""

    def test_lower_case_q_quits(self):
        self.assertEqual(QUIT, translate("q", "q"))

    def test_upper_case_q_quits(self):
        self.assertEqual(QUIT, translate("Q", "Q"))

    def test_quitting_carries_no_direction(self):
        self.assertEqual(IntentKind.QUIT, translate("q", "q").kind)
        self.assertIsNone(translate("q", "q").direction)

    def test_both_cases_give_the_very_same_intent(self):
        self.assertEqual(translate("q", "q"), translate("Q", "Q"))

    def test_a_control_modified_q_does_not_quit(self):
        # The keysym survives the modifier but the character does not, which
        # is the only thing that distinguishes them at this seam.
        self.assertIsNone(translate("q", "\x11"))


class EveryOtherKeyIsDiscarded(unittest.TestCase):
    """CTRL-5 — no other key does anything."""

    def test_a_representative_spread_of_keys_maps_to_nothing(self):
        for keysym, char in IGNORED_KEYS:
            self.assertIsNone(
                translate(keysym, char),
                "{0!r} (char {1!r}) should do nothing".format(keysym, char),
            )

    def test_the_spread_is_a_real_spread_and_not_an_empty_list(self):
        # A test that iterates an empty list passes and proves nothing.
        self.assertGreater(len(IGNORED_KEYS), 40)

    def test_the_spread_covers_the_cases_that_are_easy_to_get_wrong(self):
        keysyms = [keysym for keysym, _ in IGNORED_KEYS]

        # a modified form of a key the game *does* use
        self.assertIn(("q", "\x11"), IGNORED_KEYS)
        # a bare modifier key
        self.assertIn("Control_L", keysyms)
        # a function key
        self.assertIn("F1", keysyms)
        # something that looks like an arrow but is not one
        self.assertIn("KP_Up", keysyms)
        # the keys a player might reach for instead of the arrows
        for wasd in ("w", "a", "s", "d"):
            self.assertIn(wasd, keysyms)

    def test_every_printable_ascii_character_other_than_q_does_nothing(self):
        for code in range(32, 127):
            character = chr(code)
            if character in QUIT_KEYS:
                continue

            self.assertIsNone(
                translate(character, character),
                "{0!r} should do nothing".format(character),
            )

    def test_something_that_is_not_text_at_all_does_nothing(self):
        self.assertIsNone(translate(None, ""))
        self.assertIsNone(translate("Up", None))
        self.assertIsNone(translate(7, ""))


class NothingIsEchoedAnywhere(unittest.TestCase):
    """CTRL-5's other half — nothing typed is echoed anywhere."""

    def test_translating_every_kind_of_key_writes_nothing_to_any_stream(self):
        keys = (
            [(keysym, "") for keysym in ARROW_KEYS]
            + [("q", "q"), ("Q", "Q")]
            + IGNORED_KEYS
        )
        out, err = io.StringIO(), io.StringIO()

        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            for keysym, char in keys:
                translate(keysym, char)

        self.assertEqual("", out.getvalue())
        self.assertEqual("", err.getvalue())

    def test_the_translator_imports_nothing_it_could_emit_through(self):
        # Only module-level names can be checked this way, so this asserts
        # what it can actually see: that no output-capable module has been
        # imported. The real guarantee is the stream capture above.
        import terminal_game.presentation.input_translator as translator

        names = set(vars(translator))

        for module in ("sys", "os", "logging", "warnings", "traceback"):
            self.assertNotIn(
                module,
                names,
                "the translator imports {0!r}, which it could emit "
                "through".format(module),
            )

    def test_no_line_of_the_translator_writes_anything(self):
        import inspect

        import terminal_game.presentation.input_translator as translator

        # Strip the docstrings: they discuss echoing at length, and it is the
        # executable lines that matter.
        source = inspect.getsource(translator)
        executable = "".join(source.split('"""')[::2])

        for emitter in ("print(", ".write(", "stdout", "stderr", "log"):
            self.assertNotIn(
                emitter,
                executable,
                "the translator contains {0!r}".format(emitter),
            )


class TheIntentVocabulary(unittest.TestCase):
    """What WI-15 will consume.  Announced under the first-lander rule."""

    def test_there_are_two_kinds_of_intent_and_no_more(self):
        # GAME-3: no pause, no restart, no level select.
        self.assertEqual({"MOVE", "QUIT"}, {kind.name for kind in IntentKind})

    def test_an_intent_is_a_value_that_compares_equal(self):
        self.assertEqual(move(Direction.NORTH), move(Direction.NORTH))
        self.assertNotEqual(move(Direction.NORTH), move(Direction.SOUTH))
        self.assertNotEqual(move(Direction.NORTH), QUIT)

    def test_the_directions_are_the_ones_the_rest_of_the_game_uses(self):
        # Announced: the direction vocabulary is the one WI-5 landed, which
        # WI-7's ghost policy also uses. There is not a second one.
        from terminal_game.domain import maze

        for direction in ARROW_KEYS.values():
            self.assertIsInstance(direction, maze.Direction)

    def test_a_move_in_something_that_is_not_a_direction_is_refused(self):
        with self.assertRaises(ValueError):
            move("up")

    def test_the_translator_names_no_toolkit_and_no_shell(self):
        # Presentation may name Application and Domain, and not the Shell.
        import inspect

        import terminal_game.presentation.input_translator as translator

        source = inspect.getsource(translator)
        executable = "".join(source.split('"""')[::2])

        self.assertNotIn("tkinter", executable)
        self.assertNotIn("terminal_game.shell", executable)


if __name__ == "__main__":
    unittest.main()
