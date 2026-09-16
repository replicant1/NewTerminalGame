# -*- coding: utf-8 -*-
"""WI-17 — the window's manners, as far as they can be checked with no window.

**No window is created anywhere in this file.**  The toolkit is WI-3's
:class:`RecordingToolkit` throughout, and the one thing here that touches the
real tree reads it as text.

What this module deliberately does **not** contain is as important as what it
does.  WI-3's tests already own *closing twice closes once*, *the timer stops
before the window goes*, and *a collaborator that raises still loses its
window*.  WI-2's tests already own *no caret is ever asked for on the
surface*, with a recording canvas that would notice one.  WI-9's tests already
own *every other key means nothing*.  Re-asserting any of them here would turn
one defect into several red files across several items, which is the thing
section 4 of the plan tells us not to do.

So this module owns three joins and one rule that nothing owned before:

* the exercise script is **bounded** and cannot be asked for something that
  would never happen;
* its report tells the truth about reaping and about failure;
* :func:`exit_code_for` **notices a failure the event loop did not raise** —
  the hazard WI-18 inherited, and now checks for itself;
* **no production module constructs a text-entry widget**, which is SCRN-7's
  half that lives in the window rather than on the surface.

*What used to be here and no longer is:* the key-to-intent dispatch.  It
belonged to nobody when this was written; WI-18 has since landed the real
one and ``tests/test_game.py`` owns it.
"""

import ast
import os
import unittest

from terminal_game.shell.toolkit import KeyPress, PixelSize
from tools.window_manners import (
    DEFAULT_LIFETIME_MS,
    Exercise,
    FallingOverCollaborator,
    KeyDispatcher,
    exit_code_for,
    expected_to_fail,
)

from .house_rules import REPOSITORY_ROOT, python_files
from .recording_toolkit import RecordingToolkit

#: A size, deliberately not 40 x 30 of anything: the exercise is told its
#: pixels, exactly as the window owner is.
A_SIZE = PixelSize(width=400, height=570)


class SilentCollaborator:
    def __init__(self):
        self.ticks = 0
        self.keys = []

    def on_tick(self):
        self.ticks += 1

    def on_key(self, key):
        self.keys.append(key)


class FakeSession:
    """Stands in for WI-15's session: records what it was asked to do.

    Only the three things a key can ask for.  What the real session *does*
    with them is WI-15's, and is not asserted here.
    """

    def __init__(self):
        self.asked = []
        self.state = None

    def tick(self):
        self.asked.append(("tick", None))

    def move(self, direction):
        self.asked.append(("move", direction))

    def quit(self):
        self.asked.append(("quit", None))


def _exercise(toolkit, collaborator=None, **kwargs):
    return Exercise(
        toolkit, A_SIZE, collaborator or SilentCollaborator(), **kwargs
    )


class TheExerciseCannotRunUnboundedTest(unittest.TestCase):
    """A script that waited on a person would block the user's screen."""

    def setUp(self):
        self.toolkit = RecordingToolkit()

    def test_the_backstop_is_scheduled_at_the_stated_lifetime(self):
        exercise = _exercise(self.toolkit, lifetime_ms=2500)

        exercise.run()

        self.assertIn(2500, self.toolkit.scheduled_delays)

    def test_the_backstop_is_scheduled_before_the_event_loop_is_entered(self):
        # Scheduling it afterwards would be scheduling it never: control does
        # not come back until the loop has already been left.
        exercise = _exercise(self.toolkit, lifetime_ms=2500)

        exercise.run()

        self.assertLess(
            self.toolkit.index_of("schedule_once"),
            self.toolkit.index_of("run_event_loop"),
        )

    def test_the_backstop_really_does_end_the_session(self):
        # Fire whatever is due until the session ends; nothing else in this
        # exercise ever asks for it, so only the backstop can have done it.
        exercise = _exercise(self.toolkit, lifetime_ms=2500)
        self.toolkit.event_loop_body = self.toolkit.fire_due_timer

        exercise.run()

        self.assertTrue(exercise.owner.session_ended)

    def test_every_scripted_action_is_scheduled_before_the_loop(self):
        exercise = _exercise(self.toolkit, lifetime_ms=2500)
        exercise.at(400, lambda: None)
        exercise.at(800, lambda: None)

        exercise.run()

        self.assertEqual(
            [400, 800, 2500],
            self.toolkit.scheduled_delays[: len(exercise.script) + 1],
        )

    def test_an_action_at_or_past_the_backstop_is_refused(self):
        # It would be scheduled against a window that has already gone, so
        # it would silently never happen.  Refusing says so.
        exercise = _exercise(self.toolkit, lifetime_ms=2000)

        with self.assertRaises(ValueError):
            exercise.at(2000, lambda: None)
        with self.assertRaises(ValueError):
            exercise.at(2400, lambda: None)
        self.assertEqual((), exercise.script)

    def test_the_default_lifetime_is_short_enough_to_borrow_a_screen_for(self):
        # Somebody is sitting in front of this screen.
        self.assertLessEqual(DEFAULT_LIFETIME_MS, 5000)
        self.assertEqual(DEFAULT_LIFETIME_MS, _exercise(self.toolkit).lifetime_ms)


class TheReportTellsTheTruthTest(unittest.TestCase):
    """The report is the only thing anyone reads afterwards."""

    def setUp(self):
        self.toolkit = RecordingToolkit()

    def test_a_clean_run_records_no_error_and_a_reaped_window(self):
        report = _exercise(self.toolkit).run()

        self.assertIsNone(report["error"])
        self.assertTrue(report["measured"]["window_reaped"])

    def test_a_loop_that_raises_is_recorded_rather_than_swallowed(self):
        def explode():
            raise OSError("the window server went away")

        self.toolkit.event_loop_body = explode

        report = _exercise(self.toolkit).run()

        self.assertIn("OSError", report["error"])
        self.assertIn("the window server went away", report["error"])

    def test_a_window_that_survived_is_reported_as_not_reaped(self):
        # The exercise asks; it does not assume.  A run that left a window
        # behind must say so, because that is the one outcome a person has to
        # clear up by hand.
        report = _exercise(self.toolkit).run(still_there=lambda target: True)

        self.assertFalse(report["measured"]["window_reaped"])

    def test_the_report_names_the_exercise_and_the_process(self):
        report = _exercise(self.toolkit, name="keys").run()

        self.assertEqual("keys", report["exercise"])
        self.assertEqual(os.getpid(), report["pid"])


class NoticingAFailureTheLoopDidNotRaiseTest(unittest.TestCase):
    """The hazard WI-18 inherits, encoded as four lines.

    Tk swallows an exception raised inside an ``after()`` callback, so the
    session routes a failure into the same shutdown path ``q`` uses and keeps
    it on ``session.failure`` instead of raising.  The event loop then returns
    normally.  **Measured on a real window** (see
    ``docs/findings/WI-17-real-window-manners.md``): the window was reaped,
    nothing was printed, and ``run()`` returned with no exception at all.
    Unless somebody reads that field, a crashed game exits looking clean.
    """

    def test_a_run_with_nothing_wrong_is_a_clean_exit(self):
        report = {"error": None, "measured": {"window_reaped": True}}

        self.assertEqual(0, exit_code_for(report))

    def test_an_exception_out_of_the_loop_is_not_a_clean_exit(self):
        report = {"error": "Boom: x", "measured": {"window_reaped": True}}

        self.assertEqual(1, exit_code_for(report))

    def test_a_recorded_session_failure_is_not_a_clean_exit(self):
        # Nothing raised, the window went away tidily, and the game still
        # crashed.  This is the whole point.
        report = {
            "error": None,
            "measured": {"window_reaped": True, "session_failure": "Boom: x"},
        }

        self.assertEqual(1, exit_code_for(report))

    def test_a_window_left_behind_is_not_a_clean_exit(self):
        report = {"error": None, "measured": {"window_reaped": False}}

        self.assertEqual(1, exit_code_for(report))

    def test_the_two_failure_exercises_are_the_ones_expected_to_fail(self):
        # A clean exit from either of them would mean the failure went
        # unnoticed, so the script inverts its exit code for exactly these.
        self.assertTrue(expected_to_fail("fail-collaborator"))
        self.assertTrue(expected_to_fail("fail-session"))
        for clean in ("window", "keys", "close"):
            self.assertFalse(expected_to_fail(clean))


class TheExercisesNotebookTest(unittest.TestCase):
    """What the ``keys`` exercise records, and only that.

    **The dispatch itself is no longer here.**  When this module was written
    WI-18 had not landed and :class:`KeyDispatcher` did its own translating;
    it now delegates to WI-18's
    :class:`~terminal_game.shell.game.GameCollaborator`, whose tests in
    ``tests/test_game.py`` own *an arrow becomes a move, ``q`` becomes a
    quit, an unmapped key becomes nothing*.  Re-asserting that here would
    turn one defect in three lines into two red files.

    What is left is the notebook, which is genuinely this script's: without
    it the exercise's report could not show an arrow key becoming a move.
    """

    def setUp(self):
        self.session = FakeSession()
        self.dispatcher = KeyDispatcher(self.session)

    def press(self, keysym, char=""):
        self.dispatcher.on_key(KeyPress(keysym=keysym, char=char))

    def test_it_records_every_key_and_what_each_one_became(self):
        self.press("Left")
        self.press("z", "z")
        self.press("Q", "Q")

        self.assertEqual(["Left", "z", "Q"], self.dispatcher.keys_delivered)
        self.assertEqual(["move", None, "quit"], self.dispatcher.intents)

    def test_it_counts_the_ticks_it_passed_on(self):
        self.dispatcher.on_tick()
        self.dispatcher.on_tick()

        self.assertEqual(2, self.dispatcher.ticks)
        self.assertEqual([("tick", None), ("tick", None)], self.session.asked)

    def test_it_notes_where_the_player_was_after_each_key(self):
        # Recorded from the session rather than worked out, which is what
        # lets the report show a move having happened.
        self.press("Up")
        self.press("z", "z")

        self.assertEqual(2, len(self.dispatcher.player_after_each_key))


class TheDeliberateFailureIsAnInputNotAMutationTest(unittest.TestCase):
    """The failing collaborator fails because it was asked to, on a parameter.

    Recorded as a test rather than a comment because the prohibition in
    section 4 is easy to breach by accident: no working code is edited to
    make anything go red, here or in the script.
    """

    def test_it_ticks_normally_until_the_tick_it_was_told_to_fail_on(self):
        collaborator = FallingOverCollaborator(fail_on_tick=3)

        collaborator.on_tick()
        collaborator.on_tick()

        self.assertEqual(2, collaborator.ticks)

    def test_it_fails_on_the_tick_it_was_told_to(self):
        collaborator = FallingOverCollaborator(fail_on_tick=2)

        collaborator.on_tick()
        with self.assertRaises(FallingOverCollaborator.DeliberateFailure):
            collaborator.on_tick()


class NoTextCaretCanExistTest(unittest.TestCase):
    """SCRN-7's half that lives in the window rather than on the surface.

    WI-2 already pins the surface's half thoroughly — the canvas is
    configured with a zero-width caret and its recording double would notice
    ``focus`` or ``icursor`` being called.  What nothing guarded is the
    simpler statement underneath it: **the application builds no widget that
    has a caret in the first place.**  A ``Text`` added to the window in some
    later item would show a blinking cursor and no existing test would care.

    This is an architecture guard in the same family as WI-10's six rules,
    and it is not a duplicate of any of them; it is kept out of
    ``tests/house_rules.py`` because that is DEV-C's landed file.
    """

    #: Tk widgets that show an insertion cursor.  ``Listbox`` and ``Label``
    #: are not here because they have none.
    CARET_WIDGETS = frozenset(("Entry", "Text", "Spinbox", "Combobox"))

    #: The canvas methods that would give a text item the focus, which is the
    #: only way a caret appears on a canvas.
    CARET_CALLS = frozenset(("icursor",))

    #: What the application is.  ``tests`` may do as it likes, and ``tools``
    #: is scripts a person runs — but neither may grow a caret either, so
    #: both are inspected.
    INSPECTED = ("terminal_game", "tools")

    def _modules(self):
        found = []
        for package in self.INSPECTED:
            for relative in python_files(REPOSITORY_ROOT, package):
                path = os.path.join(REPOSITORY_ROOT, relative)
                with open(path, "r", encoding="utf-8") as handle:
                    found.append((relative, ast.parse(handle.read(), relative)))
        return found

    def test_it_has_something_to_inspect(self):
        # A guard that inspected nothing would pass for ever and mean
        # nothing.  The shell is where a widget would be built, so it must
        # be among what was read.
        modules = self._modules()

        self.assertGreater(len(modules), 10)
        self.assertIn(
            os.path.join("terminal_game", "shell", "tk_toolkit.py"),
            [relative for relative, _ in modules],
        )

    def test_no_module_constructs_a_widget_that_has_a_caret(self):
        offenders = []
        for relative, tree in self._modules():
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = _called_name(node.func)
                if name in self.CARET_WIDGETS:
                    offenders.append("{0}:{1} {2}".format(relative, node.lineno, name))

        self.assertEqual(
            [],
            offenders,
            "SCRN-7: nothing on screen may show a text caret, and these "
            "widgets have one",
        )

    def test_nothing_gives_a_canvas_text_item_an_insertion_cursor(self):
        offenders = []
        for relative, tree in self._modules():
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = _called_name(node.func)
                if name in self.CARET_CALLS:
                    offenders.append("{0}:{1} {2}".format(relative, node.lineno, name))

        self.assertEqual([], offenders)


def _called_name(function):
    """The bare name being called, however it was reached."""
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


class TheSuiteStillOpensNothingTest(unittest.TestCase):
    """Importing this module's subject must not reach the window server."""

    def test_no_toolkit_interpreter_has_been_created(self):
        # ``tools.window_manners`` imports the Tk adapter only inside
        # ``main``, so importing it here is harmless — and this is where that
        # would stop being true.
        import tkinter

        self.assertIsNone(tkinter._default_root)


if __name__ == "__main__":
    unittest.main()
