# -*- coding: utf-8 -*-
"""WI-4 — that the skeleton is wired up, and nothing else.

**These tests own the join and only the join.** What the window does is
WI-3's and is asserted in ``test_window_owner.py``; what the surface does is
WI-2's and is asserted in ``test_grid_surface.py``; what the picture says is
WI-1's. One broken wire should turn one test red here, and none of the
others.

So: that the surface is built on the drawing target the *window* handed back,
that the frame reaches the surface, that ticks and keys reach the journal,
that ``q`` ends the session, and that the run is bounded. Nothing about
titles, sizes, colours, glyphs or cadence — all of those already have owners.

No window is created anywhere in this file.
"""

import unittest

from terminal_game.presentation.frame import Colour, Frame
from terminal_game.shell.toolkit import KeyPress, PixelSize
from tools.walking_skeleton import (
    DEFAULT_LIFETIME_SECONDS,
    QUIT_KEYSYMS,
    Journal,
    WalkingSkeleton,
)

from .recording_toolkit import RecordingToolkit

A_SIZE = PixelSize(width=400, height=570)


class RecordingSurface:
    """Stands in for WI-2's character grid surface."""

    def __init__(self, target):
        self.target = target
        self.painted = []

    def paint(self, frame):
        self.painted.append(frame)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def _skeleton(toolkit, frame=None, journal=None, **kwargs):
    made = []

    def make_surface(target):
        surface = RecordingSurface(target)
        made.append(surface)
        return surface

    skeleton = WalkingSkeleton(
        toolkit,
        A_SIZE,
        make_surface,
        frame if frame is not None else Frame.blank(),
        journal if journal is not None else Journal(),
        **kwargs
    )
    return skeleton, made


class TheSurfaceIsBuiltOnTheWindowsDrawingTargetTest(unittest.TestCase):
    """The WI-2 / WI-3 join: the whole reason this item exists."""

    def setUp(self):
        self.toolkit = RecordingToolkit()

    def test_the_surface_is_given_the_target_the_window_handed_back(self):
        skeleton, made = _skeleton(self.toolkit)

        skeleton.open()

        self.assertEqual(1, len(made))
        self.assertIs(self.toolkit.drawing_target, made[0].target)

    def test_there_is_one_surface_and_one_window(self):
        # DEV-B's surface_on docstring: use the target the owner already made,
        # so there is one canvas and not two.
        skeleton, made = _skeleton(self.toolkit)

        skeleton.open()

        self.assertEqual(1, len(made))
        self.assertEqual(1, self.toolkit.count("create_window"))

    def test_the_window_is_asked_for_the_pixel_size_the_metrics_gave(self):
        # The surface's metrics own the size; the window takes it. That is the
        # only thing that crosses from WI-2 to WI-3.
        skeleton, _ = _skeleton(self.toolkit)

        skeleton.open()

        self.assertEqual(A_SIZE, self.toolkit.window_spec.size)

    def test_the_frame_reaches_the_surface(self):
        picture = Frame.from_text("\n".join(["x" * 37] * 30), Colour.WALL_BLUE)
        skeleton, made = _skeleton(self.toolkit, frame=picture)

        skeleton.open()

        self.assertEqual([picture], made[0].painted)

    def test_the_surface_is_reachable_once_the_window_is_open(self):
        skeleton, made = _skeleton(self.toolkit)

        self.assertIsNone(skeleton.surface)
        skeleton.open()
        self.assertIs(made[0], skeleton.surface)


class WhatArrivesReachesTheJournalTest(unittest.TestCase):
    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.clock = FakeClock()
        self.journal = Journal(clock=self.clock)

    def test_a_tick_is_recorded(self):
        skeleton, _ = _skeleton(self.toolkit, journal=self.journal)
        skeleton.open()
        self.toolkit.event_loop_body = self.toolkit.fire_due_timer

        skeleton.run()

        self.assertEqual(1, self.journal.ticks)

    def test_a_key_is_recorded_by_name(self):
        skeleton, _ = _skeleton(self.toolkit, journal=self.journal)
        skeleton.open()

        self.toolkit.press("Up")
        self.toolkit.press("Left")

        self.assertEqual(["Up", "Left"], self.journal.keys)

    def test_the_journal_reports_the_cadence_it_saw(self):
        self.journal.tick()
        self.clock.advance(0.143)
        self.journal.tick()
        self.clock.advance(0.143)
        self.journal.tick()

        self.assertEqual(3, self.journal.ticks)
        self.assertEqual(143.0, self.journal.observed_tick_interval_ms)

    def test_the_journal_reports_no_cadence_before_two_ticks(self):
        self.assertIsNone(self.journal.observed_tick_interval_ms)
        self.journal.tick()
        self.assertIsNone(self.journal.observed_tick_interval_ms)


class TheRunIsBoundedTest(unittest.TestCase):
    """It must end by itself, whatever anybody does or does not press."""

    def setUp(self):
        self.toolkit = RecordingToolkit()

    def test_q_ends_the_session(self):
        skeleton, _ = _skeleton(self.toolkit)
        skeleton.open()

        self.toolkit.press("q", "q")

        self.assertTrue(skeleton.owner.session_ended)
        self.assertEqual(1, self.toolkit.count("destroy_window"))

    def test_shifted_q_ends_the_session_too(self):
        # CTRL-4: upper or lower case.
        skeleton, _ = _skeleton(self.toolkit)
        skeleton.open()

        self.toolkit.press("Q", "Q")

        self.assertTrue(skeleton.owner.session_ended)

    def test_the_quit_keys_are_the_two_the_requirements_name(self):
        self.assertEqual({"q", "Q"}, set(QUIT_KEYSYMS))

    def test_another_key_does_not_end_the_session(self):
        skeleton, _ = _skeleton(self.toolkit)
        skeleton.open()

        for keysym in ("Up", "Down", "Left", "Right", "space", "Escape"):
            self.toolkit.press(keysym)

        self.assertFalse(skeleton.owner.session_ended)
        self.assertEqual(0, self.toolkit.count("destroy_window"))

    def test_a_deadline_is_scheduled_before_the_loop_is_entered(self):
        skeleton, _ = _skeleton(self.toolkit, lifetime_ms=3000)

        skeleton.run()

        scheduled_before_loop = [
            delay
            for name, delay in self.toolkit.operations[: self.toolkit.index_of("run_event_loop")]
            if name == "schedule_once"
        ]
        self.assertIn(3000, scheduled_before_loop)

    def test_the_deadline_ends_the_session(self):
        # Nobody presses anything; the window must still go away.
        skeleton, _ = _skeleton(self.toolkit, lifetime_ms=3000)

        def let_the_deadline_pass():
            while self.toolkit.pending_count:
                self.toolkit.fire_due_timer()

        self.toolkit.event_loop_body = let_the_deadline_pass
        skeleton.run()

        self.assertTrue(skeleton.owner.session_ended)
        self.assertEqual(1, self.toolkit.count("destroy_window"))

    def test_the_default_lifetime_is_bounded_and_short(self):
        self.assertGreater(DEFAULT_LIFETIME_SECONDS, 0)
        self.assertLessEqual(DEFAULT_LIFETIME_SECONDS, 60)

    def test_the_window_is_reaped_when_the_run_falls_over(self):
        # The skeleton's own failure path. That the *window owner* reaps on
        # its failure paths is WI-3's and is asserted there.
        def explode():
            raise OSError("the window server went away")

        self.toolkit.event_loop_body = explode
        skeleton, _ = _skeleton(self.toolkit)

        with self.assertRaises(OSError):
            skeleton.run()

        self.assertEqual(1, self.toolkit.count("destroy_window"))


class TheSpecimenPictureTest(unittest.TestCase):
    """That the skeleton paints the specimen, not something it made up."""

    def test_the_specimen_frame_is_the_picture_from_the_requirements(self):
        from terminal_game.presentation.specimen import SPECIMEN_ROWS
        from tools.walking_skeleton import specimen_frame

        frame = specimen_frame()

        self.assertEqual(
            list(SPECIMEN_ROWS),
            [frame.row_text(row).rstrip() for row in range(30)],
        )


if __name__ == "__main__":
    unittest.main()
