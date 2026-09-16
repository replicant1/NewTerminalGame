# -*- coding: utf-8 -*-
"""WI-20a and WI-20b — the sweep cannot drift out of step with the spec.

*WI-20b added the second half of this file.*  The first landing checked that
the document and the tree agree about what **exists**.  This landing adds the
four things the finished sweep **claims**, because a completed traceability
document fails in a different way from an incomplete one: an incomplete one is
merely unhelpful, and a finished one that quietly rounds an open question up to
a tick is worse than having none at all.

So, below the four existence checks:

5. **The document says it is finished, and nothing in it is still outstanding.**
6. **CTRL-5 is not ticked** — it is honoured for letters and not for modified
   arrows (A11), and a row carrying a tick would be a lie about what the game
   does with control-Up.
7. **No row claims test coverage for something only a person has seen work**
   (amendment 9).  Two Shell functions cannot be reached by a suite forbidden
   from constructing a toolkit interpreter; they are declared, not cited.
8. **Every open question is still recorded as open**, and every measurement
   this run took is still cited.  A tidy-up that drops one is exactly how a
   project stops being able to say what it has and has not done.

None of the eight can pass over an empty set: each asserts a floor first.


A traceability document is only worth having while it is true, and the way
it stops being true is quiet: a requirement is added, or a test is renamed,
and the document still reads as though everything is covered. Checked by eye
it stays wrong until somebody re-reads all forty-nine rows.

So four things were checked from the first landing, and they are different
things:

1. **Every requirement code in the specification appears in the sweep**, and
   exactly once. This is what the plan asks for.
2. **The sweep invents no code** the specification does not have.
3. **Every test the sweep names exists** — the file, the class, and the
   method. A citation is a promise that something is pinned, and a renamed
   test turns that promise into a lie without anybody noticing.
4. **Every document the sweep cites exists.** WI-20b's test list asks for
   this; it costs nothing to have it from the first landing.

The sweep names no tests in this file, and this file asserts nothing about
what any requirement *means*. It checks that the document and the tree still
agree about what exists, and that the document has not quietly changed what it
claims.
"""

from __future__ import annotations

import ast
import collections
import os
import re
import unittest

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPECIFICATION = os.path.join(REPOSITORY_ROOT, "docs", "FUNCTIONAL_REQUIREMENTS.md")

#: The sweep sits beside the specification, the architecture and the plan
#: rather than under one of the four per-something directories, because it is
#: about the whole project and not about any one work item. It carries no
#: work-item code for the same reason: somebody who was not on this run
#: should not need to know what "WI-20a" was to understand what they have.
#: One file, written twice — WI-20a creates it, WI-20b completes it in place.
SWEEP = os.path.join(REPOSITORY_ROOT, "docs", "TRACEABILITY.md")

#: The requirement families the specification uses. Listing them rather than
#: matching any capitalised word keeps a stray "PR-8" out of the count.
FAMILIES = (
    "GAME",
    "WIN",
    "SCRN",
    "MAZE",
    "START",
    "CTRL",
    "GHOST",
    "SCORE",
    "END",
    "STAT",
)

#: A requirement code as the specification writes it, in bold at the head of
#: its bullet: ``- **SCRN-3** The walls are drawn as…``
DECLARED = re.compile(
    r"^\s*-\s+\*\*(" + "|".join(FAMILIES) + r")-(\d+)\*\*", re.MULTILINE
)

#: A code anywhere in running text.
MENTIONED = re.compile(r"\b(?:" + "|".join(FAMILIES) + r")-\d+\b")

#: A row of one of the sweep's tables: ``| SCRN-3 | WI-8 | … |``
SWEEP_ROW = re.compile(
    r"^\|\s*((?:" + "|".join(FAMILIES) + r")-\d+)\s*\|", re.MULTILINE
)

#: A test citation: ``tests/test_x.py::Class`` or ``…::Class::method``.
CITED_TEST = re.compile(
    r"`(tests/[A-Za-z0-9_]+\.py)::([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:::([A-Za-z_][A-Za-z0-9_]*))?`"
)

#: A document citation: a backticked path under ``docs/``.
CITED_DOCUMENT = re.compile(r"`(docs/[A-Za-z0-9_./-]+\.md)`")


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def declared_codes():
    """Every requirement code the specification declares, in order."""
    return ["{0}-{1}".format(family, number) for family, number in DECLARED.findall(read(SPECIFICATION))]


def swept_codes():
    """Every code the sweep has a table row for, in order."""
    return SWEEP_ROW.findall(read(SWEEP))


def row_for(code):
    """The whole table row for *code*, as a list of its cells.

    Added in WI-20b, because three of its checks are about what one
    particular row says rather than about the document as a whole.  Returns
    an empty list if the code has no row, which the callers assert against
    rather than skipping over.
    """
    wanted = re.compile(r"^\|\s*" + re.escape(code) + r"\s*\|(.*)$", re.MULTILINE)
    found = wanted.search(read(SWEEP))
    if found is None:
        return []
    return [cell.strip() for cell in found.group(1).split("|")]


def lines_naming(needle):
    """Every line of the sweep containing *needle*."""
    return [line for line in read(SWEEP).splitlines() if needle in line]


def section_thirteen():
    """The sweep's *what is open* section, from its heading to the end.

    The open questions are the part of this document a later tidy-up is most
    likely to shorten, because every one of them reads like an unfinished
    job.  They are not: a gap written down is a different thing from a gap
    nobody noticed, and this is where the difference is kept.
    """
    text = read(SWEEP)
    heading = "\n## 13."
    if heading not in text:
        return ""
    return text[text.index(heading) :]


class TheSpecificationIsReadCorrectly(unittest.TestCase):
    """If this file cannot find the requirements, nothing below means anything."""

    def test_the_specification_is_where_it_is_expected_to_be(self):
        self.assertTrue(
            os.path.isfile(SPECIFICATION),
            "{0} is not there".format(SPECIFICATION),
        )

    def test_the_sweep_is_where_it_is_expected_to_be(self):
        self.assertTrue(os.path.isfile(SWEEP), "{0} is not there".format(SWEEP))

    def test_there_are_forty_nine_requirement_codes(self):
        """The number the plan states, asserted so a silent parse failure
        cannot make every check below pass over an empty set.
        """
        self.assertEqual(49, len(declared_codes()))

    def test_every_family_is_represented(self):
        families = {code.split("-")[0] for code in declared_codes()}

        self.assertEqual(set(FAMILIES), families)

    def test_no_code_is_declared_twice_in_the_specification(self):
        repeated = [
            code
            for code, count in collections.Counter(declared_codes()).items()
            if count > 1
        ]

        self.assertEqual([], repeated)


class TheSweepCoversTheSpecification(unittest.TestCase):
    """The check the plan asks for, in both directions."""

    def test_every_requirement_code_appears_in_the_sweep(self):
        missing = sorted(set(declared_codes()) - set(swept_codes()))

        self.assertEqual(
            [],
            missing,
            "not traced in the sweep: {0}".format(", ".join(missing)),
        )

    def test_each_code_appears_exactly_once(self):
        repeated = sorted(
            code
            for code, count in collections.Counter(swept_codes()).items()
            if count > 1
        )

        self.assertEqual(
            [],
            repeated,
            "traced more than once: {0}".format(", ".join(repeated)),
        )

    def test_the_sweep_invents_no_requirement(self):
        invented = sorted(set(swept_codes()) - set(declared_codes()))

        self.assertEqual(
            [],
            invented,
            "not in the specification: {0}".format(", ".join(invented)),
        )

    def test_the_two_lists_are_the_same_length(self):
        self.assertEqual(49, len(swept_codes()))


class EveryTestTheSweepNamesExists(unittest.TestCase):
    """A citation is a promise; a renamed test turns it into a lie.

    Parsed rather than imported, so this costs nothing and cannot run
    anybody's module-level code a second time.
    """

    @classmethod
    def setUpClass(cls):
        cls.citations = CITED_TEST.findall(read(SWEEP))
        cls.parsed = {}

    def classes_and_methods(self, relative_path):
        if relative_path not in self.parsed:
            tree = ast.parse(read(os.path.join(REPOSITORY_ROOT, relative_path)))
            found = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    found[node.name] = {
                        sub.name
                        for sub in node.body
                        if isinstance(sub, ast.FunctionDef)
                    }
            self.parsed[relative_path] = found
        return self.parsed[relative_path]

    def test_the_sweep_actually_cites_some_tests(self):
        """So the three checks below cannot pass over an empty list."""
        self.assertGreaterEqual(len(self.citations), 40)

    def test_every_cited_file_exists(self):
        missing = sorted(
            {
                path
                for path, _class, _method in self.citations
                if not os.path.isfile(os.path.join(REPOSITORY_ROOT, path))
            }
        )

        self.assertEqual([], missing)

    def test_every_cited_class_exists(self):
        missing = []
        for path, class_name, _method in self.citations:
            if class_name not in self.classes_and_methods(path):
                missing.append("{0}::{1}".format(path, class_name))

        self.assertEqual([], sorted(set(missing)))

    def test_every_cited_method_exists(self):
        missing = []
        for path, class_name, method in self.citations:
            if not method:
                continue
            methods = self.classes_and_methods(path).get(class_name, set())
            if method not in methods:
                missing.append(
                    "{0}::{1}::{2}".format(path, class_name, method)
                )

        self.assertEqual([], sorted(set(missing)))

    def test_every_cited_method_is_a_test(self):
        """A citation pointing at a helper would pin nothing."""
        not_tests = sorted(
            {
                "{0}::{1}::{2}".format(path, class_name, method)
                for path, class_name, method in self.citations
                if method and not method.startswith("test_")
            }
        )

        self.assertEqual([], not_tests)


class EveryDocumentTheSweepCitesExists(unittest.TestCase):
    """WI-20b's test list asks for this; it is free from the first landing."""

    @classmethod
    def setUpClass(cls):
        cls.citations = sorted(set(CITED_DOCUMENT.findall(read(SWEEP))))

    def test_the_sweep_actually_cites_some_documents(self):
        self.assertGreaterEqual(len(self.citations), 5)

    def test_every_cited_document_exists(self):
        missing = [
            path
            for path in self.citations
            if not os.path.isfile(os.path.join(REPOSITORY_ROOT, path))
        ]

        self.assertEqual([], missing)


class AnIncompleteSweepSaysSo(unittest.TestCase):
    """The one way a traceability document can actively mislead.

    The sweep lands twice into the same file. Between the landings it is
    deliberately incomplete, and a reader who does not know that takes an
    unfinished row for a covered one — which is worse than no document,
    because the whole point of the thing is to be trusted.

    So: **while any row says "not yet", the notice at the top must be
    there.** The second landing removes the rows and the notice together,
    and this test is what stops one going without the other.

    It does not require the notice when nothing is outstanding. Deciding the
    sweep is finished is a person's call, not this test's.
    """

    NOTICE = "THIS IS THE FIRST OF TWO LANDINGS"
    OUTSTANDING = "**Not yet**"

    def test_the_document_is_readable_and_has_rows(self):
        self.assertGreaterEqual(len(swept_codes()), 49)

    def test_an_outstanding_row_requires_the_notice(self):
        text = read(SWEEP)

        if self.OUTSTANDING in text:
            self.assertIn(
                self.NOTICE,
                text,
                "the sweep still has an outstanding row but no longer warns "
                "the reader that it is incomplete",
            )

    def test_the_notice_names_the_item_that_closes_the_gap(self):
        text = read(SWEEP)

        if self.NOTICE in text:
            notice = text[text.index(self.NOTICE) : text.index(self.NOTICE) + 2000]
            self.assertIn("WI-18", notice)
            self.assertIn("WI-21", notice)


class TheSweepHonoursAmendmentFour(unittest.TestCase):
    """A9 / C-6: no row may claim 274 as an achieved score.

    A whole game is worth 259 to 271 points, measured over 200 seeded mazes,
    so ``CLEARED  score 274`` is a formatting exemplar and nothing else. The
    check is narrow on purpose: the sweep is allowed — and required — to
    discuss 274, so what is forbidden is the word "achieved" or "reached"
    next to it, and any row claiming it as a score.
    """

    def test_the_sweep_says_274_is_not_reachable(self):
        text = read(SWEEP)

        self.assertIn("274", text)
        self.assertIn("formatting exemplar", text)

    def test_no_sweep_row_calls_274_a_score_that_was_reached(self):
        text = read(SWEEP).lower()

        for claim in (
            "score of 274 was reached",
            "reached 274",
            "achieved 274",
            "274 was achieved",
        ):
            self.assertNotIn(claim, text)


class TheSweepIsFinished(unittest.TestCase):
    """WI-20b: the second landing's own claim, made checkable.

    The class above says *an incomplete sweep must warn the reader*.  This
    one says *this sweep is not incomplete* — the notice is gone and nothing
    is outstanding.  They are different claims and both are worth keeping:
    the first is a standing invariant for anyone who reopens a row later,
    and this one is what the second landing actually delivered.
    """

    NOTICE = AnIncompleteSweepSaysSo.NOTICE
    OUTSTANDING = AnIncompleteSweepSaysSo.OUTSTANDING

    def test_all_forty_nine_rows_are_there_to_be_finished(self):
        """The floor, so the two checks below cannot pass over nothing."""
        self.assertEqual(49, len(swept_codes()))

    def test_the_incompleteness_notice_has_been_removed(self):
        self.assertNotIn(
            self.NOTICE,
            read(SWEEP),
            "the sweep still warns that it is the first of two landings",
        )

    def test_no_row_is_still_waiting_on_a_work_item(self):
        self.assertNotIn(
            self.OUTSTANDING,
            read(SWEEP),
            "a row is still outstanding, so the sweep is not finished",
        )

    def test_it_says_in_words_that_it_is_complete(self):
        """So a reader knows which of the two states they are holding."""
        self.assertIn("This document is complete", read(SWEEP))


class CtrlFiveIsNotTicked(unittest.TestCase):
    """A11: CTRL-5 is honoured for letters and **not** for modified arrows.

    ``KeyPress`` carries no modifier state, so control-Up cannot be told from
    Up and moves the player.  Modified *letters* are rejected, because a
    letter's character changes under a modifier and an arrow's does not.

    The plan says of this row, in as many words: *say so; do not tick it*.
    So the check is narrow and it is about the row rather than about the
    game — a tick here would be the sweep claiming something the application
    does not do, which is the one failure a traceability document must not
    have.
    """

    def setUp(self):
        self.row = row_for("CTRL-5")

    def test_there_is_a_ctrl_five_row_at_all(self):
        self.assertNotEqual([], self.row)

    def test_it_names_the_assumption_that_governs_it(self):
        self.assertIn("A11", " ".join(self.row))

    def test_it_says_modified_arrows_are_not_covered(self):
        said = " ".join(self.row).lower()

        self.assertIn("modified arrow", said)
        self.assertIn("not for modified arrows", said)

    def test_it_does_not_carry_a_tick(self):
        """The row may explain what *is* pinned; it may not claim the code is."""
        self.assertNotIn(
            "**Pinned**",
            " ".join(self.row),
            "CTRL-5 is ticked, but a modified arrow moves the player",
        )


class NoRowClaimsTestCoverageForWhatOnlyAPersonHasSeen(unittest.TestCase):
    """Amendment 9's rule, made mechanical.

    Two functions in the Shell construct a toolkit interpreter, which house
    rule 5 forbids the suite, so **no test reaches them**.  The answer the
    plan settled on is not to work around the rule but to label the hole:
    *covered by observation, not by test*, with the observation recorded in
    ``docs/findings/`` and cited.

    What must never happen is a row citing a test for either of them.  That
    would turn "a person watched this work once" into "this is pinned", and
    the whole document trades on the difference.
    """

    UNTESTABLE = ("measure_metrics", "create_surface")

    def test_the_sweep_declares_both_of_them(self):
        text = read(SWEEP)

        for function in self.UNTESTABLE:
            self.assertIn(function, text, "{0} is not declared".format(function))

    def test_it_uses_the_category_the_plan_names(self):
        self.assertIn("covered by observation, not by test", read(SWEEP).lower())

    def test_neither_is_presented_as_pinned(self):
        for function in self.UNTESTABLE:
            for line in lines_naming(function):
                self.assertNotIn(
                    "**Pinned**",
                    line,
                    "{0} cannot be pinned by anything: {1}".format(function, line),
                )

    def test_neither_is_offered_a_test_citation(self):
        for function in self.UNTESTABLE:
            for line in lines_naming(function):
                self.assertEqual(
                    [],
                    CITED_TEST.findall(line),
                    "{0} is cited as tested: {1}".format(function, line),
                )

    def test_the_observation_that_covers_them_is_cited(self):
        """A recorded observation is weaker coverage; an unrecorded one is none."""
        cited = set(CITED_DOCUMENT.findall(read(SWEEP)))

        self.assertIn("docs/findings/WI-2-cell-metrics.md", cited)
        self.assertIn("docs/findings/WI-16-the-look.md", cited)


class EveryOpenQuestionIsStillRecordedAsOpen(unittest.TestCase):
    """The most valuable thing in the document, and the easiest to lose.

    Every one of these reads like an unfinished job, which is exactly why a
    later tidy-up would delete them.  They are findings.  Five developers in
    a row declined to convert a measurement into an answer and each was
    right; this is what stops the sixth reader undoing that quietly.

    Matched with word boundaries so that ``A1`` does not match ``A10``.
    """

    #: Each assumption or contradiction that is open, and the shortest
    #: unambiguous phrase for the two that have no code.
    OPEN = (
        r"\bA1\b",
        r"\bA2 revised\b",
        r"\bA3\b",
        r"\bA4\b",
        r"\bA7\b",
        r"\bA8\b",
        r"\bA9\b",
        r"\bA10\b",
        r"\bA11\b",
        r"\bC-7\b",
        r"tie-break",
        r"whole game",
    )

    def setUp(self):
        self.section = section_thirteen()

    def test_the_section_was_found_and_is_not_a_stub(self):
        """So the loop below cannot pass over an empty string."""
        self.assertGreater(len(self.section), 2000)
        self.assertIn("What is open", self.section)

    def test_every_one_of_them_is_named(self):
        missing = [
            pattern
            for pattern in self.OPEN
            if not re.search(pattern, self.section)
        ]

        self.assertEqual(
            [],
            missing,
            "no longer recorded as open: {0}".format(", ".join(missing)),
        )

    def test_the_section_says_what_a_person_must_do(self):
        """An open question nobody can act on is a complaint, not a finding."""
        self.assertIn("What a person does", self.section)

    def test_the_sweep_does_not_claim_to_settle_them(self):
        self.assertIn("this sweep settles none of them", self.section.lower())


class EveryMeasurementThisRunTookIsCited(unittest.TestCase):
    """The sweep is the index of what this project actually measured.

    Thirteen findings were written while the run was going on, by three
    developers, and each records something that was run rather than reasoned
    about.  The spikes that produced them are gone and the PR summaries will
    not be read again, so **the sweep is the only place left that points at
    them**.  A measurement nobody cites is a measurement that is lost the
    next time somebody asks what we actually know.

    Listed explicitly rather than read off the directory, so that a finding
    added by a later work item does not turn this red for the wrong reason.
    """

    FINDINGS = (
        "WI-2-cell-metrics",
        "WI-3-tk-window-probe",
        "WI-4-first-window",
        "WI-5-specimen-grid-structure",
        "WI-6-start-squares",
        "WI-7-ghost-roaming",
        "WI-8-glyph-census",
        "WI-13-status-line-literals",
        "WI-14-anchor-query",
        "WI-16-the-look",
        "WI-17-real-window-manners",
        "WI-18-the-game-on-screen",
        "WI-21-the-five-questions",
    )

    def test_all_thirteen_are_on_disk(self):
        """The floor: the list below describes the tree it is checked against."""
        directory = os.path.join(REPOSITORY_ROOT, "docs", "findings")
        present = set(os.listdir(directory))

        self.assertGreaterEqual(len(present), len(self.FINDINGS))
        for stem in self.FINDINGS:
            self.assertIn(stem + ".md", present)

    def test_the_sweep_cites_every_one_of_them(self):
        cited = set(CITED_DOCUMENT.findall(read(SWEEP)))

        missing = sorted(
            "docs/findings/{0}.md".format(stem)
            for stem in self.FINDINGS
            if "docs/findings/{0}.md".format(stem) not in cited
        )

        self.assertEqual(
            [],
            missing,
            "measured, written down, and now cited by nothing: {0}".format(
                ", ".join(missing)
            ),
        )


if __name__ == "__main__":
    unittest.main()
