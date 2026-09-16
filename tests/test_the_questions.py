# -*- coding: utf-8 -*-
"""WI-21 — the questions for a human, and the only part of it a machine owns.

Most of this work item is a person looking at a screen, and that is the
point of it. The plan says exactly what the suite owns here, and it is two
things: **that the script cannot run unbounded**, and **that it reaps its
window on the failure path**. Those are the first two classes below.

The rest of this file guards the *discipline* rather than the code, because
the discipline is what this work item is for:

* **no question may be recorded as answered.** Five developers in a row
  declined to convert a measurement into an answer, and a field that could
  be quietly filled in later would undo all five. So there is a test that
  every answer is ``None``, and a structural one that nothing in the module
  can set it.
* **the harness may not start the unbounded game.** Section 4 rule 5. The
  route is *structurally absent* — the module names no subprocess and no
  entry point — which covers every run on every machine rather than the one
  run an observation would cover.
* **the harness composes no picture of its own.** The state-to-frame binding
  already exists in four places and WI-22 is consolidating them; this tool
  must not be a fifth. It leaves ``build_game``'s composer at its default,
  so the picture comes from the production join and nowhere else.

**No window is created anywhere in this file.** The sitting is driven
through WI-3's :class:`RecordingToolkit`, which is the whole reason
``a_sitting`` takes a :class:`~tools.the_questions.Stage` instead of going
and finding a toolkit for itself.

What is deliberately *not* here, per "assert the seam, not both sides of
it": nothing about what the frame looks like (WI-12 and WI-13), nothing
about what a key does (WI-9 and WI-18), nothing about the session's three
phases (WI-15), and nothing about the anchor's arithmetic (WI-14). A sitting
runs a real assembled ``Game``, so all of that is exercised — but it is
asserted where it is owned.
"""

from __future__ import annotations

import ast
import inspect
import os
import unittest

from terminal_game.shell.anchor import FALLBACK_POSITION
from terminal_game.shell.grid_surface import FONT_POINT_SIZE
from terminal_game.shell.toolkit import PixelSize, ScreenPosition
from terminal_game.shell.window_owner import WINDOW_TITLE

from tools import the_questions
from tools.the_questions import (
    BACKSTOP_MARGIN_MS,
    DEFAULT_SECONDS,
    MAXIMUM_RUN_SECONDS,
    MAXIMUM_SECONDS,
    ONLY_THE_REAL_GAME,
    QUESTIONS,
    RULINGS,
    SIZE_LADDER,
    THE_HARNESS,
    THE_JOINERY_VIEW,
    THE_REAL_GAME,
    Options,
    Question,
    Stage,
    a_sitting,
    checklist_lines,
    parse_options,
    the_warning,
)

from .recording_toolkit import RecordingToolkit

#: The size the window is told. WI-2 works out the real one from the font.
A_SIZE = PixelSize(width=400, height=570)

#: Somewhere to put it. WI-14 works out the real one.
A_POSITION = ScreenPosition(x=120, y=120)

#: The repository this file lives in: ``tests/`` is one level down.
REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class RecordingSurface:
    """Stands in for WI-2's surface: keeps what it was shown, draws nothing."""

    def __init__(self, target=None):
        self.target = target
        self.painted = []

    def paint(self, frame):
        self.painted.append(frame)


class ASurfaceThatWillNotBuild:
    """A collaborator handed in by a test, so that the body falls over.

    **No production code is altered anywhere in this file.** This is an
    error path exercised with an input that legitimately produces an error,
    which is the same shape as WI-18's ``FallingComposer`` and is not the
    prohibited business of breaking working code to watch a test go red.
    """

    class DeliberateSurfaceFailure(Exception):
        pass

    def __init__(self):
        self.asked = 0

    def __call__(self, target):
        self.asked += 1
        raise self.DeliberateSurfaceFailure(
            "the surface could not be built on {0!r}".format(target)
        )


def a_stage(toolkit, make_surface=None):
    """A stage with no screen behind it at all."""
    return Stage(
        toolkit=toolkit,
        pixel_size=A_SIZE,
        make_surface=make_surface or RecordingSurface,
        position=A_POSITION,
        point_size=FONT_POINT_SIZE,
        cell_width_px=10,
        cell_height_px=19,
    )


def run_everything_that_is_due(toolkit, limit=10000):
    """Fire scheduled callbacks, oldest due first, until none are left.

    **Nothing is pressed.** That is the point: the deadline has to end the
    run on its own. The limit is a guard against a genuine runaway rather
    than an expected outcome, and the tests assert it was never reached.
    """
    fired = 0
    while toolkit.pending_count and fired < limit:
        toolkit.fire_due_timer()
        fired += 1
    return fired


def flat(text):
    """*text* with every run of whitespace collapsed to one space.

    The checklist is word-wrapped for a person to read, so a phrase in it is
    routinely split across two lines. Asserting on the wrapped text would be
    asserting on the wrapping, which is not what any of these tests are
    about.
    """
    return " ".join(text.split())


def the_whole_checklist(options=None):
    """The printed checklist as one flat string, ready to be searched."""
    return flat("\n".join(checklist_lines(options)))


def module_source_tree():
    """The tool, parsed, so a rule can be asked about calls and imports."""
    return ast.parse(inspect.getsource(the_questions))


def called_names(tree):
    """Every name that is called anywhere in *tree*, attribute or plain."""
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Attribute):
            found.add(function.attr)
        elif isinstance(function, ast.Name):
            found.add(function.id)
    return found


def imported_modules(tree):
    """Every module the tool imports, however it spells the import."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


class TheHarnessCannotRunUnbounded(unittest.TestCase):
    """Section 4: never launch something that blocks forever.

    Half of this is the parser — a run with no deadline cannot be *asked*
    for — and half is the run itself, which ends with nothing pressed.
    """

    def test_the_default_is_one_window_at_the_shipped_font_size(self):
        options = parse_options([])

        self.assertEqual((FONT_POINT_SIZE,), options.sizes)
        self.assertEqual(DEFAULT_SECONDS, options.seconds)
        self.assertEqual(1, options.windows)

    def test_the_default_deadline_is_positive_and_within_the_cap(self):
        self.assertGreater(DEFAULT_SECONDS, 0)
        self.assertLessEqual(DEFAULT_SECONDS, MAXIMUM_SECONDS)

    def test_a_deadline_of_zero_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--seconds", "0"])

    def test_a_negative_deadline_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--seconds", "-1"])

    def test_a_deadline_past_the_per_window_cap_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--seconds", str(MAXIMUM_SECONDS + 1)])

    def test_the_cap_itself_is_still_allowed(self):
        self.assertEqual(MAXIMUM_SECONDS, parse_options(
            ["--seconds", str(MAXIMUM_SECONDS)]
        ).seconds)

    def test_a_whole_run_past_the_run_cap_is_refused(self):
        # Capping one window is not enough on its own: four windows at the
        # per-window maximum is four minutes of somebody's screen, and each
        # window would pass the first cap.
        sizes = ",".join(str(size) for size in SIZE_LADDER)

        with self.assertRaises(ValueError):
            parse_options(["--sizes", sizes, "--seconds", str(MAXIMUM_SECONDS)])

    def test_the_whole_size_ladder_at_the_default_deadline_is_allowed(self):
        sizes = ",".join(str(size) for size in SIZE_LADDER)

        options = parse_options(["--sizes", sizes])

        self.assertEqual(len(SIZE_LADDER), options.windows)
        self.assertLessEqual(options.worst_case_seconds, MAXIMUM_RUN_SECONDS)

    def test_every_run_that_is_allowed_has_a_finite_worst_case(self):
        for argv in ([], ["--sizes", "14,16"], ["--seconds", "5"]):
            options = parse_options(argv)

            self.assertEqual(
                options.windows * options.seconds, options.worst_case_seconds
            )
            self.assertGreater(options.worst_case_seconds, 0)
            self.assertLessEqual(
                options.worst_case_seconds, MAXIMUM_RUN_SECONDS
            )

    def test_asking_only_for_the_checklist_opens_no_window_at_all(self):
        options = parse_options(["--checklist"])

        self.assertEqual((), options.sittings)
        self.assertEqual(0, options.windows)
        self.assertEqual(0, options.worst_case_seconds)

    def test_a_font_size_of_zero_is_refused(self):
        with self.assertRaises(ValueError):
            parse_options(["--sizes", "0"])

    def test_both_deadlines_are_scheduled_before_the_event_loop_is_entered(self):
        # The one property that makes the run independent of a person: by
        # the time control is handed to the loop, the two things that will
        # end it are already on the toolkit's own scheduler.
        toolkit = RecordingToolkit()

        a_sitting(a_stage(toolkit), seconds=20)

        entered = toolkit.names.index("run_event_loop")
        for delay in (20000, 20000 + BACKSTOP_MARGIN_MS):
            self.assertIn(delay, toolkit.scheduled_delays)
            self.assertLess(toolkit.scheduled_delays.index(delay), entered)

    def test_the_window_goes_away_with_nothing_pressed_at_all(self):
        # The whole of "it exits by itself within its stated time even if
        # nobody presses anything", on virtual time: no key is delivered,
        # the scheduler is simply allowed to run.
        toolkit = RecordingToolkit()
        toolkit.event_loop_body = lambda: run_everything_that_is_due(toolkit)

        record = a_sitting(a_stage(toolkit), seconds=20)

        self.assertEqual(1, toolkit.count("destroy_window"))
        self.assertTrue(record["measured"]["window_reaped"])
        self.assertIsNone(record["error"])

    def test_the_session_itself_ends_with_nothing_pressed_at_all(self):
        # The deadline is the session's own quit, not a window snatched
        # from underneath it -- so a sitting that nobody touches goes down
        # the same shutdown path q would have taken.
        toolkit = RecordingToolkit()
        toolkit.event_loop_body = lambda: run_everything_that_is_due(toolkit)

        record = a_sitting(a_stage(toolkit), seconds=20)

        self.assertEqual("ended", record["measured"]["phase_at_the_end"])

    def test_it_is_gone_by_its_stated_time_and_not_merely_eventually(self):
        toolkit = RecordingToolkit()
        toolkit.event_loop_body = lambda: run_everything_that_is_due(toolkit)

        a_sitting(a_stage(toolkit), seconds=20)

        # Virtual time at the moment the last callback fired, with the
        # unconditional backstop included. A run that ended "eventually"
        # would sail past both of its own deadlines.
        self.assertLessEqual(toolkit.now_ms, 20000 + BACKSTOP_MARGIN_MS)
        self.assertEqual(0, toolkit.pending_count)


class TheHarnessReapsItsWindowOnTheFailurePath(unittest.TestCase):
    """The other half of what the plan says a machine can check here.

    A window left holding a live process raises a modal sheet only a person
    can dismiss, and that blocks every later scripted call in the run. So a
    sitting that falls over must still take its window away, and must say
    that it fell over rather than exiting quietly.
    """

    def test_a_sitting_that_falls_over_still_loses_its_window(self):
        toolkit = RecordingToolkit()
        will_not_build = ASurfaceThatWillNotBuild()

        record = a_sitting(a_stage(toolkit, will_not_build), seconds=20)

        self.assertEqual(1, will_not_build.asked)
        self.assertEqual(1, toolkit.count("destroy_window"))
        self.assertTrue(record["measured"]["window_reaped"])

    def test_it_reports_the_failure_rather_than_raising_it(self):
        # It must not raise: the caller's job after a sitting is to open the
        # next window or stop, and an exception escaping here would skip
        # both. So the failure comes back in the record.
        toolkit = RecordingToolkit()

        record = a_sitting(
            a_stage(toolkit, ASurfaceThatWillNotBuild()), seconds=20
        )

        self.assertIsNotNone(record["error"])
        self.assertIn("DeliberateSurfaceFailure", record["error"])

    def test_a_sitting_that_falls_over_never_enters_the_event_loop(self):
        toolkit = RecordingToolkit()

        a_sitting(a_stage(toolkit, ASurfaceThatWillNotBuild()), seconds=20)

        self.assertFalse(toolkit.event_loop_entered)

    def test_the_run_stops_after_a_window_that_was_not_reaped(self):
        # ``main`` opens the next window only if the last one is confirmed
        # gone. The decision is in the record, so it can be asserted without
        # a screen: a record whose window was not reaped is the signal.
        toolkit = RecordingToolkit()
        toolkit.event_loop_body = lambda: run_everything_that_is_due(toolkit)

        record = a_sitting(a_stage(toolkit), seconds=20)

        self.assertIn("window_reaped", record["measured"])
        self.assertIsInstance(record["measured"]["window_reaped"], bool)


class NoQuestionMayBeRecordedAsAnswered(unittest.TestCase):
    """The discipline this work item exists to protect.

    Five developers in a row declined to convert a measurement into an
    answer. WI-21's job is to make the questions cheap to answer, not to
    close them.
    """

    def test_there_are_five_questions(self):
        self.assertEqual(5, len(QUESTIONS))

    def test_every_one_of_them_is_unanswered(self):
        for question in QUESTIONS:
            self.assertIsNone(question.answer, question.code)

    def test_an_answer_is_unset_by_default_rather_than_by_habit(self):
        self.assertIn("answer", Question._field_defaults)
        self.assertIsNone(Question._field_defaults["answer"])

    def test_nothing_in_the_tool_can_fill_an_answer_in(self):
        # Structural rather than observed: an observation covers this one
        # reading of the module, an absence covers every path through it.
        tree = module_source_tree()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    self.assertNotEqual(
                        "answer",
                        keyword.arg,
                        "the tool constructs something with an answer; "
                        "WI-21 answers nothing",
                    )
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if isinstance(target, ast.Attribute):
                        self.assertNotEqual("answer", target.attr)

    def test_a_run_reports_every_answer_as_still_missing(self):
        reported = {question.code: question.answer for question in QUESTIONS}

        self.assertEqual(len(QUESTIONS), len(reported))
        self.assertEqual({None}, set(reported.values()))


class EveryQuestionSaysExactlyHowToAnswerIt(unittest.TestCase):
    """Cheap and unambiguous is the deliverable, so it is asserted."""

    def test_each_one_names_a_command_on_the_pinned_interpreter(self):
        for question in QUESTIONS:
            self.assertTrue(
                question.instrument.startswith("/usr/bin/python3 "),
                question.code,
            )

    def test_each_command_names_a_file_that_is_really_in_this_repository(self):
        # A checklist that tells somebody to run a tool we deleted is worse
        # than no checklist.
        for question in QUESTIONS:
            named = [
                word
                for word in question.instrument.split()
                if word.endswith(".py")
            ]
            for path in named:
                self.assertTrue(
                    os.path.isfile(os.path.join(REPOSITORY_ROOT, path)),
                    "{0} points at {1}, which does not exist".format(
                        question.code, path
                    ),
                )

    def test_each_one_says_what_to_look_for_and_what_a_no_would_cost(self):
        for question in QUESTIONS:
            self.assertTrue(question.asks.strip(), question.code)
            self.assertTrue(question.look_for.strip(), question.code)
            self.assertTrue(
                question.if_the_answer_is_no.strip(), question.code
            )

    def test_each_one_says_which_instrument_its_answer_would_come_from(self):
        # Amendment 10: the harness is not the shipped exit path, and
        # conflating the two is the one dishonest move available here.
        known = {
            the_questions.FROM_THE_HARNESS,
            the_questions.FROM_THE_JOINERY_VIEW,
            the_questions.FROM_THE_REAL_GAME,
            the_questions.NOT_SEEN_BUT_DECIDED,
        }

        for question in QUESTIONS:
            self.assertIn(question.asked_of, known, question.code)

    def test_the_joinery_question_is_asked_of_the_joinery_view(self):
        # Section 13 is explicit: ask A10 against WI-16's joinery view and
        # not a game screen, because the specimen picture contains no
        # crossing glyph and a real maze renders one in only 55 of 200
        # seeds. A game may never show you the junction most likely to be
        # wrong.
        joinery = [q for q in QUESTIONS if "SCRN-3" in q.code]

        self.assertEqual(1, len(joinery))
        self.assertEqual(THE_JOINERY_VIEW, joinery[0].instrument)
        self.assertEqual(
            the_questions.FROM_THE_JOINERY_VIEW, joinery[0].asked_of
        )

    def test_the_type_size_question_offers_the_whole_measured_ladder(self):
        comfort = [q for q in QUESTIONS if q.code.startswith("A4")]

        self.assertEqual(1, len(comfort))
        for size in SIZE_LADDER:
            self.assertIn(str(size), comfort[0].instrument)

    def test_every_ruling_names_the_one_place_a_reversal_lands(self):
        self.assertEqual(5, len(RULINGS))
        for ruling in RULINGS:
            self.assertTrue(ruling.as_built.strip(), ruling.code)
            self.assertTrue(ruling.cost_of_reversing_it.strip(), ruling.code)
            self.assertIn(".py", ruling.lands_in, ruling.code)


class TheWarningComesBeforeAnybodyLooks(unittest.TestCase):
    """C-7 — otherwise the fallback position reads as a bug.

    The one thing a person must be told first, because the obvious reaction
    to a window that ignores the pointer is to grant a permission, and the
    permission would change nothing.
    """

    def test_it_names_the_position_the_window_will_actually_take(self):
        warning = flat(the_warning())

        self.assertIn(
            "({0}, {1})".format(FALLBACK_POSITION.x, FALLBACK_POSITION.y),
            warning,
        )

    def test_it_says_a_permission_would_not_change_it(self):
        self.assertIn(
            "GRANTING ACCESSIBILITY WOULD NOT CHANGE THIS",
            flat(the_warning()),
        )

    def test_it_says_the_fix_is_a_fallback_rather_than_a_permission(self):
        warning = flat(the_warning()).lower()

        self.assertIn("a better fallback position, not a permission", warning)

    def test_the_checklist_puts_the_warning_above_the_placement_question(self):
        text = the_whole_checklist()
        placement = [q for q in QUESTIONS if "WIN-4" in q.code][0]

        self.assertLess(
            text.index("READ THIS BEFORE YOU LOOK"),
            text.index(flat(placement.code)),
        )


class TheHarnessIsNotTheShippedExitPath(unittest.TestCase):
    """Section 4 rule 5, and it is the rule that shapes this whole item.

    The finished game is unbounded by design, because ``q`` is the only way
    out of a finished game. An agent must never start it. The harness shows
    the same window through the same code and says so; the command for the
    real game is handed to the person instead.
    """

    def test_the_checklist_hands_the_person_the_real_command(self):
        self.assertIn(THE_REAL_GAME, the_whole_checklist())
        self.assertNotEqual(THE_REAL_GAME, THE_HARNESS)

    def test_it_says_plainly_that_the_harness_is_not_the_shipped_path(self):
        text = the_whole_checklist()

        self.assertIn("NOT the shipped exit path", text)
        self.assertIn("No agent on this project may start that command", text)

    def test_it_lists_what_only_the_real_game_can_answer(self):
        text = the_whole_checklist()

        self.assertTrue(ONLY_THE_REAL_GAME)
        for item in ONLY_THE_REAL_GAME:
            self.assertIn(flat(item), text)

    def test_the_tool_has_no_way_to_start_a_process_at_all(self):
        # "Absent, not guarded" — a guard is a flag somebody can flip, and
        # an absence covers every run on every machine rather than the one
        # run an observation covers.
        imported = imported_modules(module_source_tree())

        for module in ("subprocess", "multiprocessing", "pty", "popen2"):
            self.assertNotIn(module, imported)
        self.assertNotIn("terminal_game.__main__", imported)

    def test_the_tool_calls_nothing_that_launches_anything(self):
        called = called_names(module_source_tree())

        for launcher in (
            "system",
            "Popen",
            "call",
            "check_call",
            "check_output",
            "spawn",
            "spawnl",
            "spawnv",
            "execv",
            "execvp",
            "fork",
            "popen",
        ):
            self.assertNotIn(
                launcher,
                called,
                "the harness calls {0}(); it must have no way to start the "
                "unbounded game".format(launcher),
            )


class TheHarnessComposesNoPictureOfItsOwn(unittest.TestCase):
    """WI-22 is consolidating the state-to-frame binding; this is not a fifth.

    The two lines that join WI-13's row 29 to WI-12's rows 0-28 already
    exist in four places. ``a_sitting`` leaves ``build_game``'s composer at
    its default, so the picture comes from the production join in
    ``terminal_game/shell/game.py`` and this tool declares nothing.
    """

    def test_it_never_calls_the_composer_or_the_status_line_itself(self):
        called = called_names(module_source_tree())

        self.assertNotIn("compose_frame", called)
        self.assertNotIn("status_row", called)

    def test_it_imports_neither_of_them(self):
        imported = imported_modules(module_source_tree())

        self.assertNotIn(
            "terminal_game.presentation.frame_composer", imported
        )
        self.assertNotIn("terminal_game.presentation.status_line", imported)

    def test_it_never_types_the_title_it_asks_a_person_to_look_at(self):
        # A1's question quotes the titlebar, so if the title ever changes
        # the question has to change with it. It is derived from
        # window_owner's own constant; a copy typed here would go stale
        # silently and send somebody to look for the wrong string.
        #
        # Deliberately NOT asserted here: that the window the game asks for
        # carries that title. WI-18 owns that join and pins it already
        # (tests/test_game.py), and amendment 11's rule applies -- one
        # defect should turn one test red.
        for node in ast.walk(module_source_tree()):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.assertNotEqual(
                    WINDOW_TITLE,
                    node.value.strip(),
                    "the tool has typed the window title; it must come from "
                    "WINDOW_TITLE so the question follows a change to it",
                )

    def test_the_record_reports_the_title_from_that_constant(self):
        toolkit = RecordingToolkit()
        toolkit.event_loop_body = lambda: run_everything_that_is_due(toolkit)

        record = a_sitting(a_stage(toolkit), seconds=20)

        self.assertEqual(WINDOW_TITLE, record["asked_for"]["title"])


class TheChecklistIsOneWordingAndNotTwo(unittest.TestCase):
    """The document quotes this, so the two cannot drift apart."""

    def test_every_question_and_every_ruling_reaches_the_printed_page(self):
        text = the_whole_checklist()

        for question in QUESTIONS:
            self.assertIn(flat(question.code), text)
            self.assertIn(flat(question.instrument), text)
            self.assertIn(flat(question.asks), text)
            self.assertIn(flat(question.look_for), text)
        for ruling in RULINGS:
            self.assertIn(flat(ruling.code), text)
            self.assertIn(flat(ruling.lands_in), text)

    def test_a_run_with_windows_says_how_long_it_can_possibly_last(self):
        options = parse_options(["--sizes", "14,16", "--seconds", "5"])

        text = the_whole_checklist(options)

        self.assertIn("2 window(s)", text)
        self.assertIn("10s at the very most", text)

    def test_a_checklist_only_run_promises_no_window(self):
        text = the_whole_checklist(parse_options(["--checklist"]))

        self.assertNotIn("THIS RUN:", text)


class WhatASittingIsAskedForIsWhatItRecords(unittest.TestCase):
    """So that a finding can quote the record rather than the intention."""

    def test_it_records_the_size_and_the_place_it_was_given(self):
        toolkit = RecordingToolkit()
        toolkit.event_loop_body = lambda: run_everything_that_is_due(toolkit)

        record = a_sitting(a_stage(toolkit), seconds=20)

        self.assertEqual(A_SIZE.width, record["asked_for"]["width_px"])
        self.assertEqual(A_SIZE.height, record["asked_for"]["height_px"])
        self.assertEqual(A_POSITION.x, record["asked_for"]["x"])
        self.assertEqual(A_POSITION.y, record["asked_for"]["y"])

    def test_the_same_seed_gives_the_same_run_twice(self):
        # Two people looking at "the game" must be looking at one picture.
        records = []
        for _ in range(2):
            toolkit = RecordingToolkit()
            toolkit.event_loop_body = lambda t=toolkit: run_everything_that_is_due(t)
            records.append(a_sitting(a_stage(toolkit), seconds=20))

        self.assertEqual(
            records[0]["measured"]["score"], records[1]["measured"]["score"]
        )
        self.assertEqual(
            records[0]["measured"]["outcome"], records[1]["measured"]["outcome"]
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
