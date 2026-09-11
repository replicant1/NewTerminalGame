"""The AppleScript this project composes, asserted as text.

The scripts cannot be executed in a test, so the guard is on what they say.
This is the cheapest guard in the project against rule 1 of plan section 2.6:
*never touch a window you did not open*. If somebody ever writes
``close front window``, or closes by title or by index, a test here goes red
before it reaches a person's screen.
"""

import re
import unittest

from termgame import window

WINDOW_ID = 2486


def acting_scripts():
    """Every script that *acts on* a window, i.e. everything but the two
    read-only reference queries and the census."""
    return {
        "configure": window.script_configure_window(WINDOW_ID),
        "move": window.script_move_window(WINDOW_ID, 130, 230),
        "state": window.script_tab_state(WINDOW_ID),
        "close": window.script_close_window(WINDOW_ID),
        "visible": window.script_window_visible(WINDOW_ID),
        "name": window.script_window_name(WINDOW_ID),
    }


class AddressingTest(unittest.TestCase):
    """Rule 1: the captured id, and nothing else."""

    def test_every_acting_script_addresses_the_captured_id(self):
        for label, script in acting_scripts().items():
            self.assertIn(
                "first window whose id is %d" % WINDOW_ID,
                script,
                "%s does not address the captured window id" % label,
            )

    def test_no_acting_script_says_front_window(self):
        for label, script in acting_scripts().items():
            self.assertNotIn("front window", script, "%s says front window" % label)

    def test_no_acting_script_matches_on_a_title(self):
        for label, script in acting_scripts().items():
            self.assertNotIn(
                "whose name", script, "%s selects a window by title" % label
            )
            self.assertNotIn(
                "custom title of window",
                script,
                "%s selects a window by title" % label,
            )

    def test_no_acting_script_addresses_a_window_by_index(self):
        # "window 1", "window 2", ... -- the enumerate-and-guess mistake.
        pattern = re.compile(r"\bwindow\s+\d")
        for label, script in acting_scripts().items():
            self.assertIsNone(
                pattern.search(script), "%s addresses a window by index" % label
            )

    def test_the_only_window_this_module_can_name_is_by_id(self):
        # Every mention of "window" in an acting script is either the phrase
        # that selects by id, or a local variable holding the result of it.
        for label, script in acting_scripts().items():
            for line in script.splitlines():
                # "title displays window size" is a tab property, not a way of
                # naming a window.
                line = line.replace("title displays window size", "")
                if "window" not in line:
                    continue
                self.assertTrue(
                    "first window whose id is %d" % WINDOW_ID in line
                    or "gameWindow" in line,
                    "%s names a window some other way: %r" % (label, line),
                )


class CloseTest(unittest.TestCase):
    """Rules 2 and 3: never close a busy tab, and never close a live game."""

    def test_the_close_is_guarded_in_the_same_script(self):
        script = window.script_close_window(WINDOW_ID)
        busy_at = script.index("busy of gameTab is false")
        processes_at = script.index("(count of processes of gameTab) is 0")
        close_at = script.index("close gameWindow")
        self.assertLess(busy_at, close_at, "the close is not guarded by busy")
        self.assertLess(
            processes_at, close_at, "the close is not guarded by the process count"
        )

    def test_the_close_needs_both_halves_of_the_guard(self):
        # busy alone is false for the whole of a running game (measured), so a
        # close guarded only by busy would shut the window on a live game; the
        # process count alone would not protect against the modal sheet.
        script = window.script_close_window(WINDOW_ID)
        self.assertIn(
            "if busy of gameTab is false and (count of processes of gameTab) is 0",
            script,
        )

    def test_the_running_test_reads_both_busy_and_the_process_count(self):
        script = window.script_tab_state(WINDOW_ID)
        self.assertIn("busy of gameTab", script)
        self.assertIn("count of processes of gameTab", script)

    def test_the_close_reports_which_of_the_two_happened(self):
        script = window.script_close_window(WINDOW_ID)
        self.assertIn('return "closed"', script)
        self.assertIn('return "busy"', script)

    def test_liveness_is_read_with_visible_not_exists(self):
        # Terminal keeps a stale window object after a close.
        script = window.script_window_visible(WINDOW_ID)
        self.assertIn("visible of", script)
        self.assertNotIn("exists", script)


class SettingsTest(unittest.TestCase):
    """WIN-2 and the WIN-3 title components."""

    def test_the_tab_is_set_to_forty_by_thirty(self):
        script = window.script_configure_window(WINDOW_ID)
        self.assertIn("set number of columns of gameTab to 40", script)
        self.assertIn("set number of rows of gameTab to 30", script)

    def test_the_tab_is_menlo_eighteen_on_black(self):
        script = window.script_configure_window(WINDOW_ID)
        self.assertIn('set font name of gameTab to "Menlo-Regular"', script)
        self.assertIn("set font size of gameTab to 18", script)
        self.assertIn("set background color of gameTab to {0, 0, 0}", script)

    def test_every_scriptable_title_component_is_turned_off(self):
        script = window.script_configure_window(WINDOW_ID)
        for component in (
            "custom title",
            "device name",
            "shell path",
            "window size",
            "file name",
        ):
            self.assertIn(
                "set title displays %s of gameTab to false" % component, script
            )

    def test_the_custom_title_is_never_switched_on(self):
        # Measured: setting it true gives "Terminal Game - Terminal Game".
        script = window.script_configure_window(WINDOW_ID)
        self.assertNotIn("set title displays custom title of gameTab to true", script)
        self.assertNotIn("set custom title", script)

    def test_settings_are_applied_to_our_tab_and_nothing_global(self):
        script = window.script_configure_window(WINDOW_ID)
        self.assertNotIn("default settings", script)
        self.assertNotIn("settings set", script)

    def test_alternative_settings_are_honoured(self):
        settings = window.WindowSettings(
            columns=80, rows=24, font_name="Courier", font_size=12,
            background_color=(1, 2, 3),
        )
        script = window.script_configure_window(WINDOW_ID, settings)
        self.assertIn("set number of columns of gameTab to 80", script)
        self.assertIn('set font name of gameTab to "Courier"', script)
        self.assertIn("set background color of gameTab to {1, 2, 3}", script)


class OpenTest(unittest.TestCase):
    """WIN-1: the window is identified by having watched it appear."""

    def test_the_new_window_is_found_from_the_tab_do_script_returned(self):
        script = window.script_open_window("exec '/tmp/Terminal Game'")
        self.assertIn("set newTab to do script", script)
        self.assertIn("first window whose tabs contains newTab", script)
        self.assertIn("return id of newWindow as text", script)

    def test_the_new_window_is_not_found_by_being_frontmost(self):
        script = window.script_open_window("exec '/tmp/Terminal Game'")
        self.assertNotIn("front window", script)

    def test_the_command_is_quoted_into_the_applescript_string(self):
        script = window.script_open_window('exec "/tmp/od" "d"')
        self.assertIn('do script "exec \\"/tmp/od\\" \\"d\\""', script)


class MoveTest(unittest.TestCase):
    def test_the_position_is_written_to_our_window_only(self):
        script = window.script_move_window(WINDOW_ID, 130, 230)
        self.assertIn(
            "set position of (first window whose id is %d) to {130, 230}" % WINDOW_ID,
            script,
        )


class ReadOnlyQueryTest(unittest.TestCase):
    """The two reference queries run *before* a window of ours exists."""

    def test_the_front_window_query_takes_the_frontmost_visible_window(self):
        # Measured: `front window` answered with a hidden window parked at
        # (-898, 76), which is on none of this machine's three displays.
        script = window.script_front_position()
        self.assertIn("if visible of w then", script)
        self.assertIn("set p to position of w", script)

    def test_the_front_window_query_only_reads(self):
        script = window.script_front_position()
        self.assertNotIn("set position", script)
        self.assertNotIn("close", script)

    def test_the_front_window_query_says_none_when_nothing_is_visible(self):
        self.assertIn('return "none"', window.script_front_position())

    def test_the_tty_query_only_reads(self):
        script = window.script_reference_position("/dev/ttys004")
        self.assertIn('tty of tab 1 of w is "/dev/ttys004"', script)
        self.assertNotIn("close", script)
        self.assertNotIn("set position", script)

    def test_the_tty_query_says_none_when_no_tab_matches(self):
        self.assertIn('return "none"', window.script_reference_position("/dev/ttys004"))

    def test_the_census_counts_only_visible_windows(self):
        # Measured: a closed window stays in Terminal's `windows` collection
        # and only `visible` goes false, so a census over all windows never
        # matches itself across a close.
        script = window.script_visible_window_ids()
        self.assertIn("if visible of w then", script)

    def test_the_census_only_reads_ids(self):
        script = window.script_visible_window_ids()
        self.assertIn("id of w as text", script)
        self.assertNotIn("close", script)
        self.assertNotIn("set position", script)


if __name__ == "__main__":
    unittest.main()
