"""The adapter between script text and typed values."""

import unittest

from launcher.desktop import Desktop, WindowSettings
from launcher.geometry import Point, Rect, Size
from launcher.runner import AutomationError
from tests.launcher_fakes import RecordingRunner


class ReadingTheDesktopsAnswers(unittest.TestCase):
    def test_the_reference_window_comes_back_as_a_rectangle(self):
        desktop = Desktop(
            RecordingRunner({"reference_window_geometry": "-879,84,-282,469"})
        )
        self.assertEqual(Rect(-879, 84, -282, 469), desktop.reference_window())

    def test_the_screen_bounds_come_back_as_a_rectangle(self):
        # The real measured value from this machine, negatives and all.
        desktop = Desktop(
            RecordingRunner({"visible_screen_bounds": "-3509,-1440,1611,982"})
        )
        self.assertEqual(Rect(-3509, -1440, 1611, 982), desktop.visible_screen())

    def test_the_window_id_comes_back_as_an_integer(self):
        desktop = Desktop(RecordingRunner({"open_window_running": "7653"}))
        self.assertEqual(7653, desktop.open_window_running("/bin/echo hi"))

    def test_the_window_size_comes_back_in_points(self):
        desktop = Desktop(RecordingRunner({"window_size": "357,558"}))
        self.assertEqual(Size(357, 558), desktop.window_size(7653))

    def test_a_move_reports_where_the_window_actually_ended_up(self):
        # Not where it was asked to go: the desktop is free to disagree, and a
        # caller that trusted its own arithmetic would never find out.
        desktop = Desktop(RecordingRunner({"set_window_position": "0,25"}))
        self.assertEqual(Point(0, 25), desktop.move(7653, Point(-40, -10)))

    def test_visible_comes_back_as_a_boolean(self):
        desktop = Desktop(RecordingRunner({"window_is_visible": "false"}))
        self.assertIs(False, desktop.is_visible(7653))

    def test_the_process_list_comes_back_as_names_and_empty_means_idle(self):
        desktop = Desktop(RecordingRunner(
            {"window_processes": ["login|Python", "", "   "]}))
        self.assertEqual(["login", "Python"], desktop.processes(7653))
        self.assertEqual([], desktop.processes(7653))
        self.assertEqual([], desktop.processes(7653))

    def test_there_is_no_second_way_to_ask_whether_it_is_safe_to_close(self):
        # WI-13 removed `is_busy`. Stated as a test so that putting it back is
        # a deliberate act rather than a convenience somebody adds in passing.
        self.assertFalse(hasattr(Desktop, "is_busy"))

    def test_a_window_the_desktop_can_no_longer_address_is_not_visible(self):
        desktop = Desktop(RecordingRunner({"window_is_visible": "gone"}))
        self.assertIs(False, desktop.is_visible(7653))

    def test_the_terminals_own_spacing_and_decimals_are_tolerated(self):
        desktop = Desktop(RecordingRunner({"window_size": " 357.0 , 558.0 "}))
        self.assertEqual(Size(357, 558), desktop.window_size(7653))


class WhenTheAnswerIsNonsense(unittest.TestCase):
    def test_a_rectangle_with_the_wrong_number_of_parts_is_refused(self):
        desktop = Desktop(RecordingRunner({"visible_screen_bounds": "0,0,1440"}))
        self.assertRaises(AutomationError, desktop.visible_screen)

    def test_a_window_id_that_is_not_a_number_is_refused(self):
        desktop = Desktop(
            RecordingRunner({"open_window_running": "Terminal got an error"})
        )
        self.assertRaises(AutomationError, desktop.open_window_running, "/bin/echo hi")

    def test_a_visible_answer_that_is_neither_true_nor_false_is_refused(self):
        desktop = Desktop(RecordingRunner({"window_is_visible": "maybe"}))
        self.assertRaises(AutomationError, desktop.is_visible, 7653)


class WhatTheAdapterSends(unittest.TestCase):
    def test_the_window_settings_reach_the_script(self):
        runner = RecordingRunner({"configure_window": "ok"})
        Desktop(runner).configure(7653)
        source = runner.source_of("configure_window")
        self.assertIn("set number of columns of gameTab to 40", source)
        self.assertIn("set number of rows of gameTab to 30", source)
        self.assertIn('set custom title of gameTab to "Terminal Game"', source)

    def test_different_settings_can_be_asked_for(self):
        runner = RecordingRunner({"configure_window": "ok"})
        Desktop(runner, WindowSettings(columns=80, rows=24, title="Other")).configure(1)
        source = runner.source_of("configure_window")
        self.assertIn("set number of columns of gameTab to 80", source)
        self.assertIn('set custom title of gameTab to "Other"', source)

    def test_the_adapter_holds_no_idea_of_a_current_window(self):
        # Every method takes the id it is to act on, so there is no state for a
        # later call to drift onto the wrong window through.
        runner = RecordingRunner(
            {"configure_window": "ok", "close_window": "closed"}
        )
        desktop = Desktop(runner)
        desktop.configure(111)
        desktop.close(222)
        self.assertIn("window id 111", runner.source_of("configure_window"))
        self.assertIn("window id 222", runner.source_of("close_window"))


if __name__ == "__main__":
    unittest.main()
