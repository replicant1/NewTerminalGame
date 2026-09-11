"""``./verify`` — the harness, and the one property a harness lives or dies by.

*A harness that cannot say what broke is not a harness* (implementation plan,
WI-10). So the tests that matter most here are the ones that **break a stage on
purpose** and read what comes out: the stage's name, its position in the run,
what it was for, what went wrong, and what it printed. If any of those stop
appearing, ``./verify`` becomes a program that says "something is wrong" and
nothing else.

Nothing in this file opens a window, runs the suite recursively, or shells out.
Every stage that would do any of those takes its runner as a parameter, and
every one of them is given a fake here. The two stages that are pure — the
play-throughs and the reading of the corner measurement — are run for real.
"""

import importlib.machinery
import importlib.util
import io
import os
import random
import stat
import unittest

from termgame import theme, view, window
from termgame.model import Outcome, SCREEN_COLS, SCREEN_ROWS

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFY_PATH = os.path.join(REPO_ROOT, "verify")


def load_verify():
    """Import ``verify``, which has no ``.py`` extension by design."""
    loader = importlib.machinery.SourceFileLoader("verify_script", VERIFY_PATH)
    spec = importlib.util.spec_from_loader("verify_script", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


verify = load_verify()


class FakeRunner(object):
    """Stands in for ``run_command``. Records what it was asked to run."""

    def __init__(self, status, output=""):
        self.status = status
        self.output = output
        self.calls = []

    def __call__(self, command, cwd, timeout=None):
        self.calls.append((tuple(command), cwd))
        return self.status, self.output


def stage_that(name, ok, detail="", output="", proves="what it was for"):
    """A stage whose result is decided here, for driving ``run_stages``."""

    def run(root):
        return verify.StageResult(name, proves, ok, detail, output, 0.5)

    return verify.Stage(name.replace(" ", "-"), name, proves, run)


# ==========================================================================
# The executable itself
# ==========================================================================


class TheHarnessIsAnExecutableLikeTheOthers(unittest.TestCase):
    def test_it_is_executable_and_names_the_pinned_interpreter(self):
        mode = os.stat(VERIFY_PATH).st_mode
        self.assertTrue(mode & stat.S_IXUSR, "verify is not executable")
        with io.open(VERIFY_PATH, encoding="utf-8") as handle:
            self.assertEqual("#!/usr/bin/python3", handle.readline().strip())

    def test_it_runs_the_one_pinned_test_command_and_no_other(self):
        # Implementation plan §2.2. Every developer reports counts from this
        # exact command; a harness that ran a different one would report
        # numbers nobody else could reproduce.
        self.assertEqual(
            ("/usr/bin/python3", "-m", "unittest", "discover", "-s", "tests"),
            verify.TEST_COMMAND,
        )

    def test_it_runs_wi_8s_launch_smoke_rather_than_its_own_copy(self):
        self.assertEqual(("./launch-smoke",), verify.SMOKE_COMMAND)
        self.assertTrue(
            os.access(os.path.join(REPO_ROOT, "launch-smoke"), os.X_OK),
            "./launch-smoke is not there to be run",
        )


class TheStagesOnOffer(unittest.TestCase):
    def test_the_default_run_is_the_three_the_plan_names(self):
        self.assertEqual(("suite", "smoke", "play"), verify.DEFAULT_STAGES)
        self.assertEqual(
            ["suite", "smoke", "play"],
            [stage.short for stage in verify.chosen_stages()],
        )

    def test_corner_is_opt_in_and_is_added_last(self):
        self.assertEqual(
            ["suite", "smoke", "play", "corner"],
            [stage.short for stage in verify.chosen_stages(corner=True)],
        )

    def test_only_picks_out_one_stage(self):
        chosen = verify.chosen_stages(only=["play"])
        self.assertEqual(["play"], [stage.short for stage in chosen])

    def test_an_unknown_stage_name_is_refused_and_the_real_ones_listed(self):
        with self.assertRaises(ValueError) as raised:
            verify.chosen_stages(only=["wibble"])
        message = str(raised.exception)
        self.assertIn("wibble", message)
        self.assertIn("suite", message)
        self.assertIn("corner", message)

    def test_every_stage_says_what_it_proves(self):
        for stage in verify.all_stages():
            self.assertTrue(stage.proves.strip(), stage.name)
            self.assertGreater(len(stage.proves), 30, stage.name)

    def test_both_window_opening_stages_are_marked_as_such(self):
        # The listing warns a person before they run something that puts a
        # window on their screen.
        opens = [stage.short for stage in verify.all_stages() if stage.opens_a_window]
        self.assertEqual(["smoke", "corner"], opens)


# ==========================================================================
# THE POINT OF THE WHOLE FILE — a broken stage must be named
# ==========================================================================


class WhenAStageFailsTheOutputSaysWhichOne(unittest.TestCase):
    """Break a stage deliberately and read what comes out."""

    def run_three(self, first=True, second=True, third=True):
        out = io.StringIO()
        stages = [
            stage_that("the test suite", first, "the suite went red"),
            stage_that(
                "the launch smoke",
                second,
                "./launch-smoke exited 1",
                output="FAIL the window we opened is no longer visible",
                proves="a real window opens and closes and nothing else moves",
            ),
            stage_that("the scripted play-through", third, "row 3 differs"),
        ]
        results, ok = verify.run_stages(stages, out=out, root=REPO_ROOT)
        return out.getvalue(), results, ok

    def test_the_failing_stage_is_named_with_its_position_in_the_run(self):
        text, _results, ok = self.run_three(second=False)
        self.assertFalse(ok)
        self.assertIn("FAILED at stage 2 of 3: the launch smoke", text)

    def test_the_banner_says_what_that_stage_was_for(self):
        text, _results, _ok = self.run_three(second=False)
        self.assertIn(
            "what it proves:  a real window opens and closes and nothing "
            "else moves",
            text,
        )

    def test_the_banner_says_what_actually_went_wrong(self):
        text, _results, _ok = self.run_three(second=False)
        self.assertIn("what went wrong: ./launch-smoke exited 1", text)

    def test_the_failing_stages_own_output_is_printed_under_it(self):
        text, _results, _ok = self.run_three(second=False)
        self.assertIn("FAIL the window we opened is no longer visible", text)

    def test_the_stages_that_passed_are_named_too_so_the_failure_is_placed(self):
        text, _results, _ok = self.run_three(second=False)
        self.assertIn("The stages that passed: the test suite", text)
        self.assertIn("the scripted play-through", text.rsplit("passed:", 1)[1])

    def test_a_passing_stage_is_never_reported_as_the_one_that_failed(self):
        text, _results, _ok = self.run_three(second=False)
        self.assertNotIn("FAILED at stage 1 of 3", text)
        self.assertNotIn("FAILED at stage 3 of 3", text)

    def test_every_failing_stage_is_named_not_only_the_first(self):
        # "The suite is red and so is the smoke" is a different morning from
        # "only the smoke is red", and stopping at the first failure would
        # hide the difference.
        text, _results, ok = self.run_three(first=False, third=False)
        self.assertFalse(ok)
        self.assertIn("FAILED at stage 1 of 3: the test suite", text)
        self.assertIn("FAILED at stage 3 of 3: the scripted play-through", text)
        self.assertIn("2 of 3 stages failed", text)

    def test_all_three_green_says_so_and_returns_true(self):
        text, results, ok = self.run_three()
        self.assertTrue(ok)
        self.assertTrue(all(result.ok for result in results))
        self.assertIn("VERIFICATION PASSED -- 3 of 3 stages", text)
        self.assertNotIn("FAILED", text)

    def test_a_green_run_still_points_at_the_things_only_a_person_can_check(self):
        text, _results, _ok = self.run_three()
        self.assertIn("docs/findings/WI-10-human-checks.md", text)

    def test_the_progress_line_marks_the_failing_stage_as_it_happens(self):
        # Printed before the banner, so somebody watching a slow run learns
        # which stage went wrong at the moment it did.
        text, _results, _ok = self.run_three(second=False)
        self.assertIn("[2/3] the launch smoke ... FAILED", text)
        self.assertIn("[1/3] the test suite ... ok", text)

    def test_a_passing_stage_keeps_its_output_to_itself_by_default(self):
        out = io.StringIO()
        verify.run_stages(
            [stage_that("a chatty stage", True, "fine", "a measurement worth having")],
            out=out,
            root=REPO_ROOT,
        )
        self.assertNotIn("a measurement worth having", out.getvalue())

    def test_verbose_prints_what_a_passing_stage_printed(self):
        # How a measurement taken by a stage that passed -- the corner
        # stage's -- gets read and written down.
        out = io.StringIO()
        verify.run_stages(
            [stage_that("a chatty stage", True, "fine", "a measurement worth having")],
            out=out,
            root=REPO_ROOT,
            verbose=True,
        )
        self.assertIn("a measurement worth having", out.getvalue())

    def test_a_very_long_output_is_tailed_and_says_it_was_tailed(self):
        out = io.StringIO()
        noisy = "\n".join("line %d" % index for index in range(200))
        verify.run_stages(
            [stage_that("a noisy stage", False, "it went wrong", noisy)],
            out=out,
            root=REPO_ROOT,
        )
        text = out.getvalue()
        self.assertIn("earlier lines not shown", text)
        self.assertIn("line 199", text)
        self.assertNotIn("line 0\n", text)


class MainReturnsTheRightStatus(unittest.TestCase):
    def test_an_unknown_stage_name_exits_two_rather_than_pretending_to_pass(self):
        import contextlib

        complaint = io.StringIO()
        with contextlib.redirect_stderr(complaint):
            status = verify.main(["--only", "nonsense"])
        self.assertEqual(2, status)
        self.assertIn("no such stage: nonsense", complaint.getvalue())

    def test_listing_the_stages_exits_zero_and_runs_nothing(self):
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            status = verify.main(["--list"])
        self.assertEqual(0, status)
        self.assertIn("the bottom-right cell in a real window", buffer.getvalue())
        self.assertIn("OPENS A REAL WINDOW", buffer.getvalue())


# ==========================================================================
# Stage 1 — the test suite
# ==========================================================================


class TheTestSuiteStage(unittest.TestCase):
    def test_a_green_run_quotes_the_runners_own_summary_line(self):
        runner = FakeRunner(0, "....\n----\nRan 567 tests in 11.669s\n\nOK (skipped=2)\n")
        result = verify.stage_the_test_suite(REPO_ROOT, run=runner)
        self.assertTrue(result.ok)
        self.assertIn("Ran 567 tests in 11.669s", result.detail)
        self.assertIn("OK (skipped=2)", result.detail)

    def test_a_red_run_fails_and_quotes_the_failure_count(self):
        runner = FakeRunner(
            1, "F...\nRan 567 tests in 11.7s\n\nFAILED (failures=1)\n"
        )
        result = verify.stage_the_test_suite(REPO_ROOT, run=runner)
        self.assertFalse(result.ok)
        self.assertIn("FAILED (failures=1)", result.detail)
        self.assertIn("exited 1", result.detail)

    def test_the_exact_pinned_command_is_what_gets_run(self):
        runner = FakeRunner(0, "Ran 1 test\n\nOK\n")
        verify.stage_the_test_suite(REPO_ROOT, run=runner)
        self.assertEqual([(verify.TEST_COMMAND, REPO_ROOT)], runner.calls)

    def test_a_run_that_never_finished_is_a_failure_that_says_so(self):
        runner = FakeRunner(None, "half of something")
        result = verify.stage_the_test_suite(REPO_ROOT, run=runner)
        self.assertFalse(result.ok)
        self.assertIn("did not complete", result.detail)

    def test_output_with_no_summary_line_is_said_plainly(self):
        runner = FakeRunner(0, "nothing useful here\n")
        result = verify.stage_the_test_suite(REPO_ROOT, run=runner)
        self.assertIn("printed no summary line", result.detail)


# ==========================================================================
# Stage 2 — the launch smoke
# ==========================================================================


class TheLaunchSmokeStage(unittest.TestCase):
    def test_it_runs_the_smoke_program_rather_than_doing_the_work_itself(self):
        runner = FakeRunner(0, "run 1: PASS in 9.7s\nall 1 run(s) passed\n")
        result = verify.stage_the_launch_smoke(REPO_ROOT, run=runner)
        self.assertTrue(result.ok)
        self.assertEqual([(("./launch-smoke",), REPO_ROOT)], runner.calls)

    def test_a_green_smoke_quotes_the_smokes_own_verdict(self):
        runner = FakeRunner(0, "ok   the window is titled\nrun 1: PASS in 9.7s\n")
        result = verify.stage_the_launch_smoke(REPO_ROOT, run=runner)
        self.assertIn("PASS", result.detail)

    def test_a_failing_smoke_points_at_its_own_FAIL_lines(self):
        runner = FakeRunner(
            1,
            "ok   the supervisor reported the window id it captured\n"
            "FAIL the window is titled 'Terminal Game' -- it reads 'zsh'\n",
        )
        result = verify.stage_the_launch_smoke(REPO_ROOT, run=runner)
        self.assertFalse(result.ok)
        self.assertIn("exited 1", result.detail)
        self.assertIn("lines beginning FAIL", result.detail)
        self.assertIn("it reads 'zsh'", result.output)

    def test_a_smoke_that_never_returned_is_a_failure_that_says_so(self):
        result = verify.stage_the_launch_smoke(REPO_ROOT, run=FakeRunner(None, ""))
        self.assertFalse(result.ok)
        self.assertIn("did not complete", result.detail)


# ==========================================================================
# Stage 3 — the scripted play-throughs, run for real
# ==========================================================================


class TheScriptedScreenNeverBlocksForEver(unittest.TestCase):
    def test_an_exhausted_script_quits_rather_than_waiting(self):
        # The same rule as §2.6 rule 4, one level up: a driven game with no
        # way to end is a game that has to be killed.
        clock = verify.ScriptedClock()
        screen = verify.ScriptedScreen([], clock)
        self.assertEqual(ord("q"), screen.read_key(100))
        self.assertEqual(ord("q"), screen.read_key(100))

    def test_the_clock_moves_only_while_a_key_is_being_waited_for(self):
        clock = verify.ScriptedClock()
        screen = verify.ScriptedScreen([ord("z")], clock, seconds_per_key=0.25)
        self.assertEqual(0.0, clock())
        screen.read_key(100)
        self.assertEqual(0.25, clock())

    def test_a_frozen_clock_leaves_the_ghost_where_it_is(self):
        clock = verify.ScriptedClock()
        screen = verify.ScriptedScreen([ord("z")] * 3, clock, seconds_per_key=0.0)
        for _ in range(3):
            screen.read_key(100)
        self.assertEqual(0.0, clock())


class ThePlayThroughsReachTheEndingsTheyClaim(unittest.TestCase):
    """The claims that do not depend on any recorded picture.

    A recorded picture only ever proves that nothing changed. These say what
    the game was supposed to have done, and they would still fail on a wrong
    game whose picture had been re-recorded.
    """

    def setUp(self):
        self.games = dict(
            (game.fixture, game) for game in verify.play_throughs()
        )

    def play(self, fixture):
        return self.games[fixture].play()

    def test_the_won_game_clears_the_board_and_says_CLEARED(self):
        final, _rows = self.play("verify_final_cleared.txt")
        self.assertEqual(Outcome.CLEARED, final.outcome)
        self.assertEqual(frozenset(), final.dots)
        self.assertEqual(14, final.score)
        self.assertEqual((3, 1), tuple(final.player))

    def test_the_won_game_never_stepped_on_the_ghost(self):
        # A clear is only reachable because the ghost's square carries no dot
        # (END-3: the last dot on the ghost's square is a loss). If the state
        # builder ever put one there, this is what would notice.
        final, _rows = self.play("verify_final_cleared.txt")
        self.assertNotEqual(tuple(final.player), tuple(final.ghost))

    def test_the_lost_game_is_the_ghost_walking_onto_the_player(self):
        final, _rows = self.play("verify_final_caught.txt")
        self.assertEqual(Outcome.CAUGHT, final.outcome)
        self.assertEqual((1, 3), tuple(final.player))
        self.assertEqual(tuple(final.player), tuple(final.ghost))
        self.assertEqual(2, final.score)

    def test_the_lost_game_had_dots_left_so_it_really_was_a_catch(self):
        # If the board had emptied instead, CAUGHT would be the wrong reading
        # of a cleared board rather than evidence the ghost arrived.
        final, _rows = self.play("verify_final_caught.txt")
        self.assertTrue(final.dots)

    def test_the_ghost_only_moved_because_the_clock_moved(self):
        # GHOST-1, the other way round: the same script on a frozen clock
        # leaves the ghost where it started and the player uncaught.
        caught = self.games["verify_final_caught.txt"]
        frozen = verify.PlayThrough(
            caught.name,
            caught.state,
            caught.keys,
            0.0,
            caught.fixture,
            None,
        )
        final, _rows = frozen.play()
        self.assertEqual(Outcome.PLAYING, final.outcome)
        self.assertEqual((1, 9), tuple(final.ghost))

    def test_the_real_board_is_the_real_twenty_nine_by_nineteen_maze(self):
        final, _rows = self.play("verify_final_real_maze.txt")
        self.assertEqual((29, 19), (final.maze.height, final.maze.width))
        self.assertEqual((), __import__("termgame.maze", fromlist=["check"]).check(final.maze))

    def test_every_play_through_paints_a_thirty_by_forty_picture(self):
        for fixture in self.games:
            _final, rows = self.play(fixture)
            self.assertEqual(SCREEN_ROWS, len(rows), fixture)
            for index, row in enumerate(rows):
                self.assertEqual(SCREEN_COLS, len(row), "%s row %d" % (fixture, index))

    def test_the_status_row_of_every_final_picture_is_the_one_the_theme_says(self):
        for fixture, game in self.games.items():
            final, rows = self.play(fixture)
            self.assertIn(
                theme.status_text(final.outcome, final.score),
                rows[SCREEN_ROWS - 1],
                fixture,
            )

    def test_the_last_picture_painted_is_the_picture_of_the_final_state(self):
        # run_loop returns on `q` without painting again, so the last frame is
        # the one from the turn before. If it were not, every recorded picture
        # would be one move stale.
        for fixture, game in self.games.items():
            final, rows = self.play(fixture)
            self.assertEqual(tuple(view.render_rows(final)), tuple(rows), fixture)


class TheRecordedPicturesAreWhatTheGamePaints(unittest.TestCase):
    def test_each_play_through_ends_on_its_recorded_picture(self):
        for game in verify.play_throughs():
            _final, rows = game.play()
            self.assertIsNone(
                verify.compare_pictures(verify.read_fixture(game.fixture), tuple(rows)),
                game.fixture,
            )

    def test_the_whole_stage_is_green_against_the_recordings_in_the_repo(self):
        result = verify.stage_the_scripted_play_through(REPO_ROOT)
        self.assertTrue(result.ok, result.detail)
        self.assertIn("3 scripted games", result.detail)


class WhenTheFinalPictureIsWrong(unittest.TestCase):
    """Break the recording on purpose and read the complaint."""

    def setUp(self):
        import tempfile

        self.directory = tempfile.mkdtemp(prefix="termgame-verify-test-")
        self.saved = verify.FIXTURES
        verify.FIXTURES = self.directory

    def tearDown(self):
        import shutil

        verify.FIXTURES = self.saved
        shutil.rmtree(self.directory, ignore_errors=True)

    def a_game_with_a_doctored_recording(self, doctor):
        game = verify.play_throughs()[0]
        _final, rows = game.play()
        rows = list(rows)
        doctor(rows)
        verify.write_fixture(game.fixture, rows)
        return game

    def test_the_stage_fails_and_names_the_row_and_the_column(self):
        def doctor(rows):
            rows[3] = "!" + rows[3][1:]

        game = self.a_game_with_a_doctored_recording(doctor)
        result = verify.stage_the_scripted_play_through(REPO_ROOT, games=[game])
        self.assertFalse(result.ok)
        self.assertIn("row 3 differs", result.detail)
        self.assertIn("column 0", result.detail)
        self.assertIn("recorded:", result.detail)
        self.assertIn("painted:", result.detail)

    def test_a_recording_of_the_wrong_height_is_said_plainly(self):
        def doctor(rows):
            del rows[5]

        game = self.a_game_with_a_doctored_recording(doctor)
        result = verify.stage_the_scripted_play_through(REPO_ROOT, games=[game])
        self.assertFalse(result.ok)
        self.assertIn("rows", result.detail)

    def test_a_missing_recording_is_a_failure_and_not_a_crash(self):
        game = verify.play_throughs()[0]
        result = verify.stage_the_scripted_play_through(REPO_ROOT, games=[game])
        self.assertFalse(result.ok)
        self.assertIn("could not be read", result.detail)

    def test_the_stage_never_rewrites_a_recording_that_disagreed_with_it(self):
        # A harness that fixes its own expectations when they fail is not a
        # harness. Re-recording is --record, and only --record.
        def doctor(rows):
            rows[3] = "!" + rows[3][1:]

        game = self.a_game_with_a_doctored_recording(doctor)
        verify.stage_the_scripted_play_through(REPO_ROOT, games=[game])
        self.assertTrue(verify.read_fixture(game.fixture)[3].startswith("!"))


class ComparingTwoPictures(unittest.TestCase):
    def test_identical_pictures_compare_equal(self):
        rows = ("abc", "def")
        self.assertIsNone(verify.compare_pictures(rows, rows))

    def test_the_first_differing_row_is_the_one_reported(self):
        message = verify.compare_pictures(("aaa", "bbb", "ccc"), ("aaa", "bXb", "cXc"))
        self.assertIn("row 1 differs", message)
        self.assertIn("column 1", message)

    def test_a_different_number_of_rows_is_reported_as_such(self):
        message = verify.compare_pictures(("a", "b"), ("a",))
        self.assertIn("1 rows", message)
        self.assertIn("2", message)


class RecordingThePictures(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.directory = tempfile.mkdtemp(prefix="termgame-verify-record-")
        self.saved = verify.FIXTURES
        verify.FIXTURES = self.directory

    def tearDown(self):
        import shutil

        verify.FIXTURES = self.saved
        shutil.rmtree(self.directory, ignore_errors=True)

    def test_it_writes_one_file_per_play_through_and_they_read_back(self):
        out = io.StringIO()
        self.assertEqual(0, verify.record_the_pictures(out=out))
        for game in verify.play_throughs():
            _final, rows = game.play()
            self.assertEqual(tuple(rows), verify.read_fixture(game.fixture))

    def test_it_tells_the_person_to_read_the_diff(self):
        out = io.StringIO()
        verify.record_the_pictures(out=out)
        self.assertIn("Read the diff before you commit it", out.getvalue())

    def test_recording_is_never_one_of_the_stages(self):
        self.assertNotIn(
            "record", [stage.short for stage in verify.all_stages()]
        )


# ==========================================================================
# Stage 4 — the corner probe, without opening anything
# ==========================================================================


class TheCornerProbeChildIsSafeToLaunch(unittest.TestCase):
    """§2.6 rules 4 and 7, read off the source rather than trusted."""

    def setUp(self):
        self.source = verify.corner_probe_source(REPO_ROOT, "/tmp/out.json")

    def test_it_is_valid_python_at_the_pinned_interpreter(self):
        compile(self.source, "corner-probe", "exec")

    def test_it_is_a_shebang_script_for_the_pinned_interpreter(self):
        self.assertTrue(self.source.startswith("#!/usr/bin/python3\n"))

    def test_the_child_is_written_under_the_one_load_bearing_name(self):
        # Terminal composes the window title from the active process's name,
        # so this name is WIN-3 (§2.6 rule 7), not a label.
        self.assertEqual("Terminal Game", window.CHILD_NAME)

    def test_it_clears_the_working_directory_title_prefix_first(self):
        self.assertIn('sys.stdout.write("\\033]7;\\007")', self.source)

    def test_it_contains_nothing_that_would_block_for_ever(self):
        # A child that cannot end is a window that cannot be closed without
        # Terminal's modal confirmation sheet.
        for forbidden in ("input(", "sys.stdin.read", "raw_input", "os.read("):
            self.assertNotIn(forbidden, self.source, forbidden)

    def test_every_wait_in_it_is_bounded(self):
        self.assertIn("while time.time() - began <", self.source)
        self.assertNotIn("while True", self.source)

    def test_it_waits_for_the_window_to_become_forty_by_thirty_first(self):
        # curses reads the terminal size once, at initscr. The supervisor
        # resizes the tab after do script returns, so a probe that did not
        # wait could measure a window of whatever size Terminal opened.
        self.assertLess(
            self.source.index("os.get_terminal_size"),
            self.source.index("import curses"),
        )

    def test_it_measures_the_size_the_window_really_is(self):
        self.assertIn("(%d, %d)" % (window.ROWS, window.COLUMNS), self.source)

    def test_it_knows_where_the_package_is(self):
        self.assertIn(repr(REPO_ROOT), self.source)


class ReadingTheCornerMeasurement(unittest.TestCase):
    """The judgement, exercised without a window anywhere near it."""

    def a_good_result(self, **changes):
        measured = {
            "wanted": [30, 40],
            "size_from_the_os": [30, 40],
            "size_from_curses": [30, 40],
            "waited_for_the_size": 0.4,
            "addstr_at_the_corner": "addwstr() returned ERR",
            "insstr_at_the_corner": "no error",
            "paint": "no error",
            "matches": True,
            "last_row_in": "x" * 40,
            "last_row_out": "x" * 40,
            "curs_set": 1,
        }
        measured.update(changes)
        return measured

    def test_the_expected_measurement_passes_and_reports_both_calls(self):
        lines, failure = verify.read_the_corner_measurement(self.a_good_result())
        self.assertIsNone(failure)
        self.assertTrue(any("addwstr() returned ERR" in line for line in lines))
        self.assertTrue(any("insstr" in line for line in lines))

    def test_a_probe_that_wrote_nothing_is_a_failure_saying_so(self):
        _lines, failure = verify.read_the_corner_measurement(None)
        self.assertIn("wrote no result", failure)

    def test_a_window_of_the_wrong_size_invalidates_the_measurement(self):
        _lines, failure = verify.read_the_corner_measurement(
            self.a_good_result(size_from_curses=[24, 80])
        )
        self.assertIn("wrong window", failure)
        self.assertIn("(24, 80)", failure)

    def test_insstr_raising_at_the_corner_is_the_failure_that_matters(self):
        _lines, failure = verify.read_the_corner_measurement(
            self.a_good_result(insstr_at_the_corner="insstr() returned ERR")
        )
        self.assertIn("insstr at the bottom-right cell raised", failure)
        self.assertIn("C1", failure)

    def test_a_paint_that_raised_is_a_failure(self):
        _lines, failure = verify.read_the_corner_measurement(
            self.a_good_result(paint="error: addwstr() returned ERR")
        )
        self.assertIn("could not paint a whole picture", failure)

    def test_a_picture_that_did_not_arrive_intact_is_a_failure(self):
        _lines, failure = verify.read_the_corner_measurement(
            self.a_good_result(matches=False, last_row_out="y" * 40)
        )
        self.assertIn("not the picture that was painted", failure)

    def test_addstr_no_longer_raising_is_a_note_and_not_a_failure(self):
        # The guard in screen.paint would have become dead code. That is worth
        # knowing and is not this game being broken.
        lines, failure = verify.read_the_corner_measurement(
            self.a_good_result(addstr_at_the_corner="no error")
        )
        self.assertIsNone(failure)
        self.assertTrue(any("dead code" in line for line in lines))


class TheCornerStageCleansUpAfterItself(unittest.TestCase):
    """``reap`` — §2.6 rules 1, 3 and 6, with Terminal replaced."""

    def setUp(self):
        self.saved = (
            window.window_is_visible,
            window.close_when_idle,
            window.close_window,
        )
        self.closed = []

    def tearDown(self):
        (
            window.window_is_visible,
            window.close_when_idle,
            window.close_window,
        ) = self.saved

    def arrange(self, visible, closes):
        window.window_is_visible = lambda window_id: visible
        def close_when_idle(window_id, timeout=None):
            self.closed.append(window_id)
            return closes
        window.close_when_idle = close_when_idle
        window.close_window = lambda window_id: self.fail(
            "reap must never close a window without waiting for the child"
        )

    def test_a_window_that_has_already_gone_is_left_entirely_alone(self):
        self.arrange(visible=False, closes=True)
        out = io.StringIO()
        verify.reap(4242, out)
        self.assertEqual([], self.closed)
        self.assertEqual("", out.getvalue())

    def test_a_window_still_on_screen_is_closed_by_its_own_id(self):
        self.arrange(visible=True, closes=True)
        out = io.StringIO()
        verify.reap(4242, out)
        self.assertEqual([4242], self.closed)

    def test_a_busy_window_is_left_open_and_named_rather_than_forced(self):
        # Rule 3. A modal sheet can only be dismissed by a person and blocks
        # every AppleScript call in the system while it is up, so one window
        # somebody can close themselves is strictly the better outcome.
        self.arrange(visible=True, closes=False)
        out = io.StringIO()
        verify.reap(4242, out)
        text = out.getvalue()
        self.assertIn("LEFT OPEN", text)
        self.assertIn("4242", text)
        self.assertIn("modal sheet", text)

    def test_nothing_is_touched_when_no_window_was_ever_opened(self):
        self.arrange(visible=True, closes=True)
        verify.reap(None, io.StringIO())
        self.assertEqual([], self.closed)

    def test_a_terminal_that_will_not_answer_is_not_an_exception(self):
        def raises(window_id):
            raise window.WindowError("Terminal got an error")

        window.window_is_visible = raises
        verify.reap(4242, io.StringIO())  # must not raise

    def test_the_clean_up_is_no_more_forceful_than_play_itself(self):
        self.assertEqual(window.CLOSE_GRACE_SECONDS, verify.CORNER_CLEANUP_SECONDS)


if __name__ == "__main__":
    unittest.main()
