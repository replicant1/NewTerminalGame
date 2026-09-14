"""What the launcher would actually say to the desktop.

Every assertion here is about script text, because the text is what reaches the
desktop. Caution C1 — "never act on the front window" — is a claim about the
words in a script, so it is checked against the words in the script.
"""

import re
import unittest

from launcher import script
from launcher.geometry import Point

#: Ways of naming a window that are not its identity. Any of these appearing in
#: a script that acts on the game's window would mean the launcher could reach
#: out and size, move or close one of the player's own windows instead.
POSITIONAL_OR_TITLE = (
    "front window",
    "frontmost window",
    "window 1",
    "first window",
    "last window",
    "some window",
    "every window",
    "windows whose",
    "custom title is",
    "custom title contains",
    "name is",
    "name contains",
    "whose name",
)

WINDOW_ID = 7653

#: Every builder that acts on a window that already exists. If one is added
#: later without being listed here, it is not covered by the rules below — and
#: the last test in this file is what notices.
CALLS_ON_THE_CAPTURED_WINDOW = (
    ("configure_window", lambda: script.configure_window(WINDOW_ID)),
    ("window_size", lambda: script.window_size(WINDOW_ID)),
    (
        "set_window_position",
        lambda: script.set_window_position(WINDOW_ID, Point(432, 332)),
    ),
    ("window_is_busy", lambda: script.window_is_busy(WINDOW_ID)),
    ("close_window", lambda: script.close_window(WINDOW_ID)),
    ("window_is_visible", lambda: script.window_is_visible(WINDOW_ID)),
)

ALL_CALLS = CALLS_ON_THE_CAPTURED_WINDOW + (
    ("reference_window_geometry", script.reference_window_geometry),
    ("visible_screen_bounds", script.visible_screen_bounds),
    ("open_window_running", lambda: script.open_window_running("/bin/echo hello")),
)


class EveryCallNamesTheCapturedIdentity(unittest.TestCase):
    def test_each_one_addresses_the_window_by_its_id(self):
        for name, build in CALLS_ON_THE_CAPTURED_WINDOW:
            call = build()
            self.assertIn(
                "window id %d" % WINDOW_ID,
                call.source,
                "%s does not name the captured window id" % name,
            )

    def test_none_of_them_names_a_window_by_position_or_by_title(self):
        for name, build in CALLS_ON_THE_CAPTURED_WINDOW:
            source = build().source.lower()
            for phrase in POSITIONAL_OR_TITLE:
                self.assertNotIn(
                    phrase, source, "%s reaches for %r" % (name, phrase)
                )

    def test_a_different_window_id_produces_a_different_script(self):
        for name, build in CALLS_ON_THE_CAPTURED_WINDOW:
            mine = build().source
            self.assertNotIn("window id 99999", mine, name)

    def test_the_id_is_the_only_window_reference_in_each_script(self):
        # The word "window" should never appear except as part of the by-id
        # specifier. The one other place the terminal's vocabulary uses it is
        # the title component "window size", which names no window at all.
        pattern = re.compile(r"\bwindow\b(?!\s+id\s+%d\b)(?!\s+size\b)" % WINDOW_ID)
        for name, build in CALLS_ON_THE_CAPTURED_WINDOW:
            leftovers = pattern.findall(build().source)
            self.assertEqual([], leftovers, "%s names a window some other way" % name)


class EveryCallIsBounded(unittest.TestCase):
    def test_each_carries_a_positive_timeout(self):
        for name, build in ALL_CALLS:
            call = build()
            self.assertIsInstance(call.timeout, float, name)
            self.assertGreater(call.timeout, 0.0, name)

    def test_each_script_bounds_the_apple_event_itself(self):
        # The subprocess bound is the backstop; this is the one that fires first
        # and gives back a usable error instead of a killed process.
        for name, build in ALL_CALLS:
            call = build()
            self.assertIn("with timeout of", call.source, name)
            self.assertIn("end timeout", call.source, name)

    def test_the_scripted_bound_matches_the_calls_own_timeout(self):
        for name, build in ALL_CALLS:
            call = build()
            seconds = re.search(r"with timeout of (\d+) seconds", call.source)
            self.assertIsNotNone(seconds, name)
            self.assertGreaterEqual(int(seconds.group(1)), 1, name)
            self.assertLessEqual(int(seconds.group(1)), call.timeout + 1, name)


class TheReferenceWindowQuery(unittest.TestCase):
    def test_it_asks_the_desktop_what_is_frontmost(self):
        source = script.reference_window_geometry().source
        self.assertIn("frontmost is true", source)
        self.assertIn("System Events", source)

    def test_it_returns_a_rectangle_built_from_position_and_size(self):
        source = script.reference_window_geometry().source
        self.assertIn("position of referenceWindow", source)
        self.assertIn("size of referenceWindow", source)
        self.assertIn("refX + refW", source)
        self.assertIn("refY + refH", source)

    def test_it_never_mentions_the_terminal_application(self):
        # If it did, it could be measuring a window the launcher itself made.
        self.assertNotIn('"Terminal"', script.reference_window_geometry().source)


class CreatingTheWindow(unittest.TestCase):
    def test_the_command_is_execed_so_the_tab_falls_idle_when_it_exits(self):
        source = script.open_window_running("/bin/echo hi").source
        self.assertIn('do script "exec /bin/echo hi"', source)

    def test_the_identity_is_captured_from_the_tab_the_call_just_created(self):
        source = script.open_window_running("/bin/echo hi").source
        self.assertIn("set launchedTab to do script", source)
        self.assertIn("first window whose tabs contains launchedTab", source)
        self.assertIn("set launchedId to id of launchedWindow", source)

    def test_it_yields_the_window_id_and_nothing_else(self):
        self.assertTrue(
            script.open_window_running("/bin/echo hi").source.endswith(
                "launchedId as text"
            )
        )

    def test_the_capture_is_in_the_same_script_as_the_creation(self):
        # Two scripts would leave a gap in which another window could be made.
        call = script.open_window_running("/bin/echo hi")
        self.assertLess(
            call.source.index("do script"),
            call.source.index("tabs contains launchedTab"),
        )


class TheCommandString(unittest.TestCase):
    def test_quotes_and_backslashes_are_escaped(self):
        self.assertEqual(
            r'"a \"b\" c\\d"', script.applescript_string('a "b" c\\d')
        )

    def test_a_newline_in_a_command_is_refused_rather_than_escaped(self):
        # `do script` types its argument at a shell prompt, so a newline would
        # run a second command nobody wrote.
        for bad in ("game\nrm -rf /", "game\rwhoami", "game\x00"):
            self.assertRaises(ValueError, script.applescript_string, bad)

    def test_a_command_with_a_quote_in_it_survives_into_the_script(self):
        source = script.open_window_running('python3 -c "print(1)"').source
        self.assertIn(r'exec python3 -c \"print(1)\"', source)


class ConfiguringTheWindow(unittest.TestCase):
    def setUp(self):
        self.source = script.configure_window(WINDOW_ID).source

    def test_it_sets_forty_columns_and_thirty_rows(self):
        self.assertIn("set number of columns of gameTab to 40", self.source)
        self.assertIn("set number of rows of gameTab to 30", self.source)

    def test_it_titles_the_window_terminal_game(self):
        self.assertIn('set custom title of gameTab to "Terminal Game"', self.source)
        self.assertIn("set title displays custom title of gameTab to true", self.source)

    def test_it_turns_off_every_other_title_component_it_can_reach(self):
        for switch in ("device name", "shell path", "window size", "file name"):
            self.assertIn(
                "set title displays %s of gameTab to false" % switch, self.source
            )

    def test_the_ground_is_black(self):
        self.assertIn("set background color of gameTab to {0, 0, 0}", self.source)

    def test_the_typeface_is_fixed_width_and_set_before_the_grid(self):
        self.assertIn('set font name of gameTab to "Menlo"', self.source)
        self.assertIn("set font size of gameTab to 14", self.source)
        self.assertLess(
            self.source.index("font size"), self.source.index("number of columns")
        )

    def test_nothing_is_written_to_a_saved_settings_set(self):
        # Assumption A3: the player's saved preferences are left alone. Every
        # property goes to this window's own tab.
        self.assertNotIn("settings set", self.source)
        self.assertNotIn("default settings", self.source)
        self.assertNotIn("startup settings", self.source)

    def test_a_different_size_or_title_can_be_asked_for(self):
        other = script.configure_window(
            WINDOW_ID, columns=80, rows=24, title="Something Else", font_size=18
        ).source
        self.assertIn("set number of columns of gameTab to 80", other)
        self.assertIn("set number of rows of gameTab to 24", other)
        self.assertIn('set custom title of gameTab to "Something Else"', other)
        self.assertIn("set font size of gameTab to 18", other)


class AskingWhetherItIsSafeToClose(unittest.TestCase):
    def test_busy_is_read_from_the_captured_windows_own_tab(self):
        source = script.window_is_busy(WINDOW_ID).source
        self.assertIn("busy of selected tab of window id %d" % WINDOW_ID, source)

    def test_a_window_that_has_gone_away_reports_itself_not_busy(self):
        source = script.window_is_busy(WINDOW_ID).source
        self.assertIn("on error", source)
        self.assertIn("set tabBusy to false", source)

    def test_closing_names_the_captured_window_and_only_that(self):
        source = script.close_window(WINDOW_ID).source
        self.assertIn("close window id %d" % WINDOW_ID, source)
        self.assertNotIn("close every", source)
        self.assertNotIn("quit", source)

    def test_going_is_checked_with_visible_and_not_with_exists(self):
        source = script.window_is_visible(WINDOW_ID).source
        self.assertIn("visible of window id %d" % WINDOW_ID, source)
        self.assertNotIn("exists", source)

    def test_a_window_that_cannot_be_addressed_at_all_reports_gone(self):
        source = script.window_is_visible(WINDOW_ID).source
        self.assertIn('set stillVisible to "gone"', source)


class NothingQuitsTheTerminalApplication(unittest.TestCase):
    def test_no_script_anywhere_quits_or_closes_more_than_one_window(self):
        # The player's other windows are in the same application.
        for name, build in ALL_CALLS:
            source = build().source.lower()
            self.assertNotIn("quit application", source, name)
            self.assertNotIn("close every window", source, name)
            self.assertNotIn("close windows", source, name)


class TheListOfBuildersIsComplete(unittest.TestCase):
    def test_every_public_builder_in_the_module_is_covered_by_these_rules(self):
        exported = {
            name
            for name in dir(script)
            if not name.startswith("_")
            and callable(getattr(script, name))
            and getattr(getattr(script, name), "__module__", None) == script.__name__
        }
        exported -= {"applescript_string", "window_ref", "ScriptCall"}
        self.assertEqual(sorted(name for name, _ in ALL_CALLS), sorted(exported))


if __name__ == "__main__":
    unittest.main()
