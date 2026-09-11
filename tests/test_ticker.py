"""The one deadline — GHOST-1.

The ghost moves "about seven times a second". What makes that true over a long
game is not the tick length but the way the deadline advances: adding a tick
to the *deadline* throws away however late the loop was, and adding a tick to
*now* keeps it and keeps it and keeps it.

The drift test below is the one that matters. It runs a hundred deliberately
late ticks through both forms and shows what each does, so the property is
pinned by a comparison rather than by a tolerance somebody can widen.
"""

import unittest

from termgame import ticker


class TickLengthTest(unittest.TestCase):
    def test_the_ghost_is_due_about_seven_times_a_second(self):
        self.assertAlmostEqual(7.0, 1.0 / ticker.GHOST_TICK_SECONDS, places=9)

    def test_a_tick_is_about_143_milliseconds(self):
        self.assertAlmostEqual(0.142857, ticker.GHOST_TICK_SECONDS, places=6)


class FirstDeadlineTest(unittest.TestCase):
    """START-5 — the first picture is on screen a whole tick before anything
    moves."""

    def test_the_first_deadline_is_one_whole_tick_after_now(self):
        self.assertAlmostEqual(
            100.0 + ticker.GHOST_TICK_SECONDS,
            ticker.first_deadline(100.0),
            places=12,
        )

    def test_nothing_is_due_the_instant_the_game_starts(self):
        now = 100.0
        self.assertFalse(ticker.is_due(now, ticker.first_deadline(now)))


class WaitTest(unittest.TestCase):
    """How long the loop waits for a key: all the time there is, and no more."""

    def test_before_the_deadline_it_waits_the_time_remaining(self):
        # Exact in binary, so exact here: halves, quarters, eighths.
        self.assertEqual(500, ticker.wait_milliseconds(10.0, 10.5))
        self.assertEqual(250, ticker.wait_milliseconds(10.0, 10.25))
        self.assertEqual(125, ticker.wait_milliseconds(10.0, 10.125))
        self.assertEqual(142, ticker.wait_milliseconds(0.0, ticker.GHOST_TICK_SECONDS))

    def test_the_wait_is_the_time_remaining_to_within_a_millisecond(self):
        # A tenth of a second is not exact in binary: 10.1 - 10.0 comes out as
        # 0.09999999999999787, and truncating that gives 99 rather than 100.
        # The loop turns over once more and paints once more, at a quarter of
        # a millisecond, so it is a wart and not a defect — but it is why
        # nothing here asserts an exact millisecond on a dirty float.
        for thousandths in range(1, 1000):
            remaining = thousandths / 1000.0
            waited = ticker.wait_milliseconds(0.0, remaining)
            self.assertLessEqual(abs(waited - thousandths), 1)

    def test_the_wait_shrinks_as_the_deadline_approaches(self):
        deadline = 5.0
        waits = [ticker.wait_milliseconds(5.0 - n / 100.0, deadline) for n in range(5, 0, -1)]
        self.assertEqual(sorted(waits, reverse=True), waits)
        self.assertGreater(waits[0], waits[-1])

    def test_at_the_deadline_it_does_not_wait_at_all(self):
        self.assertEqual(0, ticker.wait_milliseconds(5.0, 5.0))

    def test_past_the_deadline_it_does_not_wait_at_all(self):
        # A negative timeout makes ncurses block for ever, which would stop
        # the ghost the moment the loop ran a hair late.
        self.assertEqual(0, ticker.wait_milliseconds(5.5, 5.0))
        self.assertEqual(0, ticker.wait_milliseconds(9999.0, 5.0))

    def test_the_wait_is_never_negative_anywhere_in_a_long_run(self):
        deadline = 0.0
        for step in range(500):
            now = step * 0.01
            self.assertGreaterEqual(ticker.wait_milliseconds(now, deadline), 0)
            if ticker.is_due(now, deadline):
                deadline = ticker.advanced(deadline)

    def test_the_wait_never_overshoots_the_deadline(self):
        # Truncation, not rounding: waking a fraction early costs one turn of
        # the loop; waking late costs a tick.
        for thousandths in range(1, 1000):
            remaining = thousandths / 1000.0
            waited = ticker.wait_milliseconds(0.0, remaining) / 1000.0
            self.assertLessEqual(waited, remaining + 1e-12)


class DueTest(unittest.TestCase):
    def test_it_is_not_due_before_the_deadline(self):
        self.assertFalse(ticker.is_due(4.999, 5.0))

    def test_it_is_due_at_the_deadline_exactly(self):
        self.assertTrue(ticker.is_due(5.0, 5.0))

    def test_it_is_due_after_the_deadline(self):
        self.assertTrue(ticker.is_due(5.001, 5.0))


class DriftTest(unittest.TestCase):
    """The reason `advanced` takes no `now`."""

    #: How late the loop is when it notices each tick, in seconds. The
    #: architect measured a mean of 4.15 ms and a max of 5.08 ms on this
    #: machine; 5 ms is a fair, slightly pessimistic stand-in.
    LATENESS = 0.005

    def test_a_hundred_late_ticks_land_exactly_where_they_should(self):
        start = 1000.0
        deadline = ticker.first_deadline(start)
        for _ in range(100):
            now = deadline + self.LATENESS  # noticed late, every single time
            self.assertTrue(ticker.is_due(now, deadline))
            deadline = ticker.advanced(deadline)
        self.assertAlmostEqual(
            start + 101 * ticker.GHOST_TICK_SECONDS, deadline, places=9
        )

    def test_the_hundredth_tick_has_not_slipped_by_even_a_millisecond(self):
        deadline = ticker.first_deadline(0.0)
        for _ in range(99):
            deadline = ticker.advanced(deadline)
        # 100 ticks at 1/7 s is 14.2857 s.
        self.assertLess(abs(deadline - 100.0 / 7.0), 0.001)

    def test_resetting_to_now_instead_would_have_lost_half_a_second(self):
        # The mistake this function exists to make unwritable. Same hundred
        # ticks, same lateness, deadline reset to `now + tick` each time.
        drifting = ticker.first_deadline(0.0)
        for _ in range(100):
            now = drifting + self.LATENESS
            drifting = now + ticker.GHOST_TICK_SECONDS
        additive = ticker.first_deadline(0.0)
        for _ in range(100):
            additive = ticker.advanced(additive)
        self.assertAlmostEqual(0.5, drifting - additive, places=6)

    def test_seventy_ticks_take_ten_seconds(self):
        # The architect measured 70 ticks in 10.005 s against a real clock —
        # 6.997 ticks/s. The deadline arithmetic on its own should account for
        # none of that 5 ms: it is all in the getch timeout.
        start = 0.0
        deadline = ticker.first_deadline(start)
        for _ in range(69):
            deadline = ticker.advanced(deadline)
        self.assertLess(abs((deadline - start) - 10.0), 0.001)

    def test_lateness_never_accumulates_however_erratic_the_clock(self):
        # A clock that is late by a different amount every time, including
        # once by more than a whole tick.
        latenesses = [0.001, 0.004, 0.2, 0.0, 0.05, 0.009]
        deadline = ticker.first_deadline(0.0)
        expected = ticker.first_deadline(0.0)
        for index in range(120):
            _now = deadline + latenesses[index % len(latenesses)]
            deadline = ticker.advanced(deadline)
            expected = expected + ticker.GHOST_TICK_SECONDS
            self.assertAlmostEqual(expected, deadline, places=9)


class TickParameterTest(unittest.TestCase):
    """Every function takes the tick length, so a test can use round numbers."""

    def test_a_custom_tick_is_honoured_throughout(self):
        self.assertEqual(1000, ticker.wait_milliseconds(0.0, 1.0))
        self.assertEqual(1.0, ticker.first_deadline(0.0, tick=1.0))
        self.assertEqual(2.0, ticker.advanced(1.0, tick=1.0))


if __name__ == "__main__":
    unittest.main()
