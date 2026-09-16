# -*- coding: utf-8 -*-
"""The register of what no machine can settle.

The one that matters: **no human check can be recorded as verified.** The
register has nowhere to write an answer — not a field set to False, no field
at all — and there is a test that says so, because a checklist an agent can
tick is not a checklist.

The instrument that runs the other half is `smoketest`, tested in
``tests/test_smoketest.py``.
"""

from __future__ import annotations

import contextlib
import inspect
import io
import unittest

from needs_a_person import checks
from needs_a_person.__main__ import EXIT_OK
from needs_a_person.__main__ import main as register_main


class AskingForTheRegisterOpensNothing(unittest.TestCase):
    """This half opens nothing, and there is no way to make it."""

    def _run(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = register_main(argv)
        return code, out.getvalue()

    def test_with_no_arguments_it_prints_the_register(self):
        code, said = self._run([])
        self.assertEqual(EXIT_OK, code)
        self.assertIn("THE HUMAN CHECKS", said)

    def test_it_takes_no_arguments_and_says_so(self):
        # There is nothing to configure about a list of things a person has
        # to look at, and a flag would invite somebody to ask this half to do
        # something it cannot. The two halves are two commands now.
        with contextlib.redirect_stderr(io.StringIO()) as complaint:
            code = register_main(["--run"])
        self.assertEqual(2, code)
        self.assertIn("python3 -m smoketest", complaint.getvalue())

    def test_the_refusal_is_reachable_from_the_real_command_line(self):
        # The bug this catches: `main()` took argv=None from `__main__` and
        # never looked at sys.argv, so the check above was dead at the only
        # place it is ever exercised for real. A test that calls
        # `main(["--run"])` passes either way.
        import sys as _sys
        saved = _sys.argv
        _sys.argv = ["python3 -m needs_a_person", "--run"]
        try:
            with contextlib.redirect_stderr(io.StringIO()) as complaint:
                with contextlib.redirect_stdout(io.StringIO()):
                    code = register_main()
        finally:
            _sys.argv = saved
        self.assertEqual(2, code)
        self.assertIn("python3 -m smoketest", complaint.getvalue())

    def test_it_points_at_the_half_that_a_machine_can_do(self):
        _, said = self._run([])
        self.assertIn("python3 -m smoketest", said)


class TheHumanChecksCannotBeTicked(unittest.TestCase):
    """A checklist an agent can mark done is not a checklist."""

    def test_a_check_has_nowhere_to_record_an_answer(self):
        # Not a field set to False. No field at all.
        for field in ("passed", "verified", "ok", "result", "answer", "status"):
            self.assertNotIn(field, checks.HumanCheck._fields, field)

    def test_the_rendered_register_carries_no_pass_or_tick_column(self):
        # A scan for the word "verified" would be the wrong test: GHOST-1's
        # entry has to SAY the mechanism is verified, because §11.11 requires
        # both lines. What must not exist is somewhere to record an answer.
        rendered = checks.render()
        for marker in ("[x]", "[ ]", "PASS", "FAIL", "✓"):
            self.assertNotIn(marker, rendered, marker)

    def test_the_register_says_in_its_own_words_that_none_is_verified(self):
        self.assertIn("None of these is recorded as verified", checks.render())

    def test_every_check_says_why_no_machine_can_answer_it(self):
        # The load-bearing field. Without it somebody will automate one of
        # these badly and delete it from the list.
        for check in checks.ALL:
            self.assertTrue(check.why_machine_cannot.strip(), check.name)
            self.assertGreater(len(check.why_machine_cannot), 80, check.name)

    def test_every_check_has_steps_and_something_to_look_for(self):
        for check in checks.ALL:
            self.assertTrue(check.steps, check.name)
            self.assertTrue(check.look_for, check.name)
            for step in check.steps:
                self.assertGreater(len(step), 10, (check.name, step))

    def test_every_check_names_the_requirements_it_settles(self):
        for check in checks.ALL:
            self.assertTrue(check.codes, check.name)
            for code in check.codes:
                self.assertRegex(code, r"^(Q\d|[A-Z]+-\d+[a-z]?)$")

    def test_the_checks_the_specification_most_needs_are_all_there(self):
        # The five colours, the font, flicker, placement, the title, a real
        # keyboard and the permission. If one of these is ever dropped, it
        # should take a failing test to do it.
        covered = set(checks.CODES_NEEDING_A_PERSON)
        for code in ("SCRN-3", "SCRN-4", "SCRN-5", "SCRN-6", "SCRN-7",
                     "WIN-2", "WIN-3", "WIN-4", "CTRL-1", "END-6", "Q2", "Q3"):
            self.assertIn(code, covered, code)

    def test_win_three_is_recorded_as_not_met_rather_than_as_a_question(self):
        # It is the one requirement this project knows it does not meet, and
        # the register must not soften that into "have a look".
        self.assertIn("NOT MET", checks.TITLE_BAR.why_machine_cannot)

    def test_the_ghost_confinement_is_two_lines_and_not_one(self):
        # Plan §11.11: the mechanism is verified, and the purpose clause is a
        # human check with the measurement beside it. Both halves, or a reader
        # takes it for a defect.
        why = checks.GHOST_CONFINEMENT.why_machine_cannot
        self.assertIn("mechanism is verified", why)
        self.assertIn("1.6%", why)
        self.assertIn("GHOST-2", why)

    def test_the_register_renders_without_losing_anything(self):
        rendered = checks.render()
        for check in checks.ALL:
            self.assertIn(check.name.upper(), rendered)
            self.assertIn(check.question, rendered)
            for code in check.codes:
                self.assertIn(code, rendered)
