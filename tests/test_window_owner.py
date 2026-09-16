"""The process's own window: how it is asked for, driven, and taken away.

No window is created anywhere in this file — the windowing toolkit is stood in
for by :class:`RecordingToolkit` throughout.
"""

import contextlib
import io
import unittest

from terminal_game.shell.cadence import TICK_INTERVAL_MS
from terminal_game.shell.toolkit import KeyPress, PixelSize, ScreenPosition
from terminal_game.shell.window_owner import (
    DEFAULT_WINDOW_POSITION,
    WINDOW_BACKGROUND,
    WINDOW_TITLE,
    WindowOwner,
)

from .recording_toolkit import RecordingToolkit

# The size the window owner is *told*.  Deliberately not 40 x 30 of anything:
# WI-3 knows pixels, and working out how many pixels a character grid needs is
# WI-2's business.
A_SIZE = PixelSize(width=512, height=600)


class RecordingCollaborator:
    """Stands in for the session controller (WI-15)."""

    def __init__(self):
        self.ticks = 0
        self.keys = []

    def on_tick(self):
        self.ticks += 1

    def on_key(self, key):
        self.keys.append(key)


class FallingOverCollaborator:
    """A collaborator that raises, to exercise the reaping path."""

    class Boom(Exception):
        pass

    def on_tick(self):
        raise self.Boom("the session fell over on a tick")

    def on_key(self, key):
        raise self.Boom("the session fell over on a key")


def _owner(toolkit, collaborator, **kwargs):
    return WindowOwner(toolkit, A_SIZE, collaborator, **kwargs)


class TheWindowItAsksForTest(unittest.TestCase):
    """WIN-1, WIN-2, WIN-3: what the window is."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.collaborator = RecordingCollaborator()
        self.owner = _owner(self.toolkit, self.collaborator)

    def test_it_is_titled_terminal_game(self):
        # WIN-3.  Under candidate 2 the process owns the window, so this is
        # the whole title and nothing composes parts onto it.
        self.owner.open()

        self.assertEqual("Terminal Game", self.toolkit.window_spec.title)
        self.assertEqual("Terminal Game", WINDOW_TITLE)

    def test_it_is_the_pixel_size_the_owner_was_told(self):
        # The surface (WI-2) works out the pixels; the window owner is told.
        self.owner.open()

        self.assertEqual(A_SIZE, self.toolkit.window_spec.size)

    def test_it_is_black_and_cannot_be_resized(self):
        # WIN-2: a black ground, and 40 x 30 cells and nothing else, so the
        # window cannot be dragged into some other shape.
        self.owner.open()

        self.assertEqual(WINDOW_BACKGROUND, self.toolkit.window_spec.background)
        self.assertEqual("black", self.toolkit.window_spec.background)
        self.assertFalse(self.toolkit.window_spec.resizable)

    def test_it_is_placed_at_the_fixed_offset_until_wi_14_lands(self):
        # WIN-4 proper needs a privileged query and is confined to WI-14.
        self.owner.open()

        self.assertEqual(DEFAULT_WINDOW_POSITION, self.toolkit.window_spec.position)

    def test_a_caller_may_place_it_where_it_likes(self):
        # This is the hook WI-14 will use; nothing else about WI-3 changes.
        somewhere = ScreenPosition(x=77, y=404)
        owner = _owner(self.toolkit, self.collaborator, position=somewhere)

        owner.open()

        self.assertEqual(somewhere, self.toolkit.window_spec.position)

    def test_opening_hands_back_the_surfaces_drawing_target(self):
        target = self.owner.open()

        self.assertIs(self.toolkit.drawing_target, target)
        self.assertIs(target, self.owner.drawing_target)

    def test_the_drawing_target_is_refused_before_the_window_exists(self):
        with self.assertRaises(RuntimeError):
            self.owner.drawing_target

    def test_opening_twice_creates_one_window(self):
        # WIN-1 asks for a window, singular.
        first = self.owner.open()
        second = self.owner.open()

        self.assertIs(first, second)
        self.assertEqual(1, self.toolkit.count("create_window"))

    def test_it_cannot_be_reopened_once_the_session_has_ended(self):
        self.owner.open()
        self.owner.end_session()

        with self.assertRaises(RuntimeError):
            self.owner.open()
        self.assertEqual(1, self.toolkit.count("create_window"))


class TheTickReachingTheCollaboratorTest(unittest.TestCase):
    """GHOST-1: the join between the timer and whoever is listening."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.collaborator = RecordingCollaborator()
        self.owner = _owner(self.toolkit, self.collaborator)

    def test_the_timer_runs_at_the_ghosts_cadence(self):
        self.assertEqual(TICK_INTERVAL_MS, self.owner.tick_interval_ms)

        self.owner.run()

        self.assertIn(TICK_INTERVAL_MS, self.toolkit.scheduled_delays)

    def test_nothing_ticks_until_the_session_is_run(self):
        self.owner.open()

        self.assertEqual([], self.toolkit.scheduled_delays)
        self.assertEqual(0, self.collaborator.ticks)

    def test_each_expiry_delivers_exactly_one_tick(self):
        self.owner.open()
        self.toolkit.event_loop_body = self.toolkit.fire_due_timer
        self.owner.run()

        self.assertEqual(1, self.collaborator.ticks)

    def test_ticks_keep_arriving_while_the_loop_runs(self):
        def three_ticks():
            for _ in range(3):
                self.toolkit.fire_due_timer()

        self.toolkit.event_loop_body = three_ticks
        self.owner.run()

        self.assertEqual(3, self.collaborator.ticks)

    def test_no_tick_arrives_after_the_session_has_ended(self):
        def tick_then_quit():
            self.toolkit.fire_due_timer()
            self.owner.end_session()

        self.toolkit.event_loop_body = tick_then_quit
        self.owner.run()

        self.assertEqual(1, self.collaborator.ticks)
        self.assertEqual(0, self.toolkit.pending_count)


class TheKeyReachingTheCollaboratorTest(unittest.TestCase):
    """CTRL-1, CTRL-4, CTRL-5 at the Shell's level: delivery, not meaning."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.collaborator = RecordingCollaborator()
        self.owner = _owner(self.toolkit, self.collaborator)
        self.owner.open()

    def test_a_key_press_is_handed_on_unchanged(self):
        delivered = self.toolkit.press("Up")

        self.assertEqual([delivered], self.collaborator.keys)
        self.assertIs(delivered, self.collaborator.keys[0])

    def test_the_key_keeps_both_its_name_and_its_character(self):
        self.toolkit.press("q", "q")

        self.assertEqual([KeyPress(keysym="q", char="q")], self.collaborator.keys)

    def test_the_shell_reads_no_meaning_into_the_key(self):
        # Interpreting keys is WI-9's, in Presentation.  The Shell passes on
        # whatever arrives, including keys the game will ignore.
        for keysym in ("Up", "Down", "Left", "Right", "q", "Q", "F5", "space"):
            self.toolkit.press(keysym)

        self.assertEqual(
            ["Up", "Down", "Left", "Right", "q", "Q", "F5", "space"],
            [key.keysym for key in self.collaborator.keys],
        )

    def test_nothing_pressed_is_echoed_anywhere(self):
        # CTRL-5: "nothing typed is echoed into the maze" — and, at this
        # level, not onto a console either.
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            for keysym in ("Up", "q", "Z", "Escape"):
                self.toolkit.press(keysym, keysym[0])

        self.assertEqual("", out.getvalue())
        self.assertEqual("", err.getvalue())


class EndingTheSessionTest(unittest.TestCase):
    """WIN-5: the window goes away, once, by whatever route the session ended."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.collaborator = RecordingCollaborator()
        self.owner = _owner(self.toolkit, self.collaborator)

    def test_the_timer_is_stopped_before_the_window_is_closed(self):
        self.owner.run()
        self.owner.end_session()

        names = self.toolkit.names
        self.assertIn("cancel_scheduled", names)
        self.assertIn("destroy_window", names)
        self.assertLess(
            self.toolkit.index_of("cancel_scheduled"),
            self.toolkit.index_of("destroy_window"),
            "a tick must not fire into a window that has already gone",
        )

    def test_the_event_loop_is_left_before_the_window_is_closed(self):
        self.owner.open()
        self.owner.end_session()

        self.assertLess(
            self.toolkit.index_of("stop_event_loop"),
            self.toolkit.index_of("destroy_window"),
        )

    def test_the_window_is_closed_exactly_once(self):
        self.owner.open()
        self.owner.end_session()

        self.assertEqual(1, self.toolkit.count("destroy_window"))
        self.assertFalse(self.owner.is_open)
        self.assertTrue(self.owner.session_ended)

    def test_ending_twice_is_safe_and_still_closes_once(self):
        self.owner.open()
        self.owner.end_session()
        self.owner.end_session()

        self.assertEqual(1, self.toolkit.count("destroy_window"))

    def test_running_to_completion_closes_the_window_once(self):
        # The ordinary route: q ends the session from inside the loop, the
        # loop returns, and run()'s own cleanup must not close a second time.
        self.toolkit.event_loop_body = self.owner.end_session

        self.owner.run()

        self.assertEqual(1, self.toolkit.count("destroy_window"))

    def test_ending_a_session_that_never_opened_a_window_closes_nothing(self):
        self.owner.end_session()

        self.assertEqual(0, self.toolkit.count("destroy_window"))
        self.assertTrue(self.owner.session_ended)

    def test_the_windows_own_close_button_ends_the_session(self):
        # Otherwise the window would go and the process would stay: the
        # orphan WIN-5 exists to prevent.
        self.owner.open()

        self.toolkit.request_close()

        self.assertTrue(self.owner.session_ended)
        self.assertEqual(1, self.toolkit.count("destroy_window"))


class ReapingOnTheFailurePathTest(unittest.TestCase):
    """A window left holding a live process is the one thing we must not do."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.owner = _owner(self.toolkit, FallingOverCollaborator())

    def test_a_collaborator_that_raises_on_a_tick_still_loses_its_window(self):
        self.toolkit.event_loop_body = self.toolkit.fire_due_timer

        with self.assertRaises(FallingOverCollaborator.Boom):
            self.owner.run()

        self.assertEqual(1, self.toolkit.count("destroy_window"))
        self.assertEqual(0, self.toolkit.pending_count)

    def test_a_collaborator_that_raises_on_a_key_still_loses_its_window(self):
        self.owner.open()

        with self.assertRaises(FallingOverCollaborator.Boom):
            self.toolkit.press("Up")

        self.assertEqual(1, self.toolkit.count("destroy_window"))

    def test_an_event_loop_that_raises_still_loses_its_window(self):
        def explode():
            raise OSError("the window server went away")

        self.toolkit.event_loop_body = explode

        with self.assertRaises(OSError):
            self.owner.run()

        self.assertEqual(1, self.toolkit.count("destroy_window"))

    def test_running_opens_the_window_if_it_is_not_open_yet(self):
        owner = _owner(self.toolkit, RecordingCollaborator())

        owner.run()

        self.assertEqual(1, self.toolkit.count("create_window"))
        self.assertTrue(self.toolkit.event_loop_entered)


if __name__ == "__main__":
    unittest.main()
