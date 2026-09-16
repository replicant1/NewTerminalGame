"""The repeating tick, built from the toolkit's one-shot scheduler.

No window is created anywhere in this file.
"""

import unittest

from terminal_game.shell.tick_timer import TickTimer

from .recording_toolkit import RecordingToolkit


class TickTimerTest(unittest.TestCase):
    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.ticks = []
        self.timer = TickTimer(self.toolkit, 143, lambda: self.ticks.append("tick"))

    def test_a_fresh_timer_has_scheduled_nothing(self):
        self.assertFalse(self.timer.is_running)
        self.assertEqual([], self.toolkit.scheduled_delays)

    def test_starting_schedules_one_callback_at_the_interval(self):
        self.timer.start()

        self.assertTrue(self.timer.is_running)
        self.assertEqual([143], self.toolkit.scheduled_delays)

    def test_starting_twice_does_not_schedule_a_second_callback(self):
        self.timer.start()
        self.timer.start()

        self.assertEqual([143], self.toolkit.scheduled_delays)

    def test_each_expiry_delivers_one_tick_and_arms_the_next(self):
        self.timer.start()

        self.toolkit.fire_due_timer()
        self.assertEqual(["tick"], self.ticks)
        self.assertEqual([143, 143], self.toolkit.scheduled_delays)

        self.toolkit.fire_due_timer()
        self.assertEqual(["tick", "tick"], self.ticks)
        self.assertEqual([143, 143, 143], self.toolkit.scheduled_delays)

    def test_stopping_cancels_the_callback_that_was_waiting(self):
        self.timer.start()
        self.timer.stop()

        self.assertFalse(self.timer.is_running)
        self.assertEqual(0, self.toolkit.pending_count)
        self.assertEqual(1, self.toolkit.count("cancel_scheduled"))

    def test_a_stopped_timer_delivers_no_further_ticks(self):
        self.timer.start()
        self.toolkit.fire_due_timer()
        self.timer.stop()

        self.assertEqual(["tick"], self.ticks)
        self.assertEqual(0, self.toolkit.pending_count)

    def test_stopping_a_timer_that_never_started_is_harmless(self):
        self.timer.stop()

        self.assertFalse(self.timer.is_running)
        self.assertEqual(0, self.toolkit.count("cancel_scheduled"))

    def test_stopping_twice_cancels_once(self):
        self.timer.start()
        self.timer.stop()
        self.timer.stop()

        self.assertEqual(1, self.toolkit.count("cancel_scheduled"))

    def test_a_tick_that_stops_the_timer_does_not_arm_another(self):
        # A tick is how the ghost catches the player, so a tick may well be
        # what ends the session.
        timer = TickTimer(self.toolkit, 143, lambda: timer.stop())
        timer.start()

        self.toolkit.fire_due_timer()

        self.assertFalse(timer.is_running)
        self.assertEqual(0, self.toolkit.pending_count)
        self.assertEqual([143], self.toolkit.scheduled_delays)

    def test_a_tick_that_raises_leaves_nothing_scheduled(self):
        def explode():
            raise ValueError("the collaborator fell over")

        timer = TickTimer(self.toolkit, 143, explode)
        timer.start()

        with self.assertRaises(ValueError):
            self.toolkit.fire_due_timer()

        self.assertEqual(
            0,
            self.toolkit.pending_count,
            "a callback left scheduled would fire into a half-dead session",
        )

    def test_the_interval_is_the_one_it_was_given(self):
        self.assertEqual(143, self.timer.interval_ms)


if __name__ == "__main__":
    unittest.main()
