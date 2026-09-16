# -*- coding: utf-8 -*-
"""WI-20a — the specification sweep cannot drift out of step with the spec.

A traceability document is only worth having while it is true, and the way
it stops being true is quiet: a requirement is added, or a test is renamed,
and the document still reads as though everything is covered. Checked by eye
it stays wrong until somebody re-reads all forty-nine rows.

So four things are checked automatically, and they are different things:

1. **Every requirement code in the specification appears in the sweep**, and
   exactly once. This is what the plan asks for.
2. **The sweep invents no code** the specification does not have.
3. **Every test the sweep names exists** — the file, the class, and the
   method. A citation is a promise that something is pinned, and a renamed
   test turns that promise into a lie without anybody noticing.
4. **Every document the sweep cites exists.** WI-20b's test list asks for
   this; it costs nothing to have it from the first landing.

None of these can pass over an empty set: each asserts a floor first, so a
path going stale fails loudly rather than checking nothing.

The sweep names no tests in this file, and this file asserts nothing about
what any requirement means. It only checks that the document and the tree
still agree about what exists.
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


if __name__ == "__main__":
    unittest.main()
