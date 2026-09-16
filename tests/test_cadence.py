"""The ghost's cadence — GHOST-1."""

import unittest

from terminal_game.shell.cadence import GHOST_TICKS_PER_SECOND, TICK_INTERVAL_MS


class GhostCadenceTest(unittest.TestCase):
    def test_the_cadence_is_seven_ticks_a_second(self):
        # GHOST-1: "about seven times a second".
        self.assertEqual(7, GHOST_TICKS_PER_SECOND)

    def test_the_interval_is_that_cadence_to_the_nearest_millisecond(self):
        self.assertEqual(
            round(1000 / GHOST_TICKS_PER_SECOND),
            TICK_INTERVAL_MS,
            "the interval must be 1000/7 ms rounded, not a hand-picked number",
        )

    def test_the_interval_gives_about_seven_ticks_a_second(self):
        ticks_a_second = 1000 / TICK_INTERVAL_MS
        self.assertAlmostEqual(7.0, ticks_a_second, delta=0.05)


if __name__ == "__main__":
    unittest.main()
