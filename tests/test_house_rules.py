# -*- coding: utf-8 -*-
"""WI-10 — the rules of the house, enforced.

Three jobs, and they are different jobs:

1. **This repository satisfies all six rules.**  One test each, so a breach
   turns exactly one of them red and the failure message names the file and
   the line.
2. **The guard cannot pass vacuously.**  A rule that inspected nothing has
   not been satisfied — it has been skipped — and every rule reports its own
   violation when that happens.  Several tests here also name a file each
   rule must have looked at, so a path going stale is caught rather than
   quietly matching nothing.
3. **Each rule notices what it is for, and only that.**  Small trees are
   written into a temporary directory with one breach planted in each, and
   the rule is asked what it sees.

A note on the third job, because it can be misread.  **This is not proving a
test can fail, and no working code is broken anywhere in this file.**  The
subject under test is a *checker*; feeding a checker an input it should
reject is how a checker is tested, and the inputs are throwaway files in a
temporary directory that no part of the application imports.  Nothing in
``terminal_game/`` or ``tools/`` is touched, edited, or reverted.

Rule 5 is the one to read carefully.  It is checked without creating a Tk
interpreter, because creating one is the thing it forbids: the rule is a
function of :data:`tkinter._default_root`, and the tests pass it ``None`` and
then a stand-in object.
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
import tempfile
import unittest

from tests import house_rules
from tests.house_rules import (
    REPOSITORY_ROOT,
    TREE_RULES,
    Report,
    domain_names_nothing_above_it,
    no_layer_names_one_above_it,
    exactly_one_root_package,
    imports_of,
    no_tk_interpreter_constructed,
    no_toolkit_below_the_shell,
    nothing_but_tests_depends_on_tests,
    nothing_draws_an_image,
    python_files,
)


def plant(root, path, source):
    """Write *source* to *path* under *root*, making directories as needed."""
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as handle:
        handle.write(source)


class PlantedTree(unittest.TestCase):
    """A throwaway repository, shaped like this one, for the rules to read.

    Nothing here is part of the application and nothing imports it.  It
    exists so a rule can be shown an input it should reject without anybody
    breaking a working file to watch something go red.
    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="house-rules-")
        self.addCleanup(shutil.rmtree, self.root, True)
        for package in (
            "app",
            "app/domain",
            "app/presentation",
            "app/shell",
            "tests",
            "tools",
        ):
            plant(self.root, os.path.join(package, "__init__.py"), "")
        plant(self.root, "app/domain/maze.py", "VALUE = 1\n")
        plant(
            self.root,
            "app/presentation/frame.py",
            "from app.domain.maze import VALUE\n",
        )
        plant(self.root, "app/shell/tk_grid.py", "import tkinter\n")
        plant(self.root, "tools/probe.py", "import tkinter\n")
        plant(self.root, "tests/test_thing.py", "import tkinter\n")

    def only(self, report):
        """The one violation in *report*, or a readable failure."""
        self.assertEqual(
            1, len(report.violations), report.describe()
        )
        return report.violations[0]


# ---------------------------------------------------------------------------
# 1. This repository satisfies all six rules
# ---------------------------------------------------------------------------


class ThisRepositoryObeysTheRules(unittest.TestCase):
    """The six rules, over the real tree, one test each."""

    def test_rule_1_no_production_code_below_the_shell_names_the_toolkit(self):
        report = no_toolkit_below_the_shell()

        self.assertEqual((), report.violations, report.describe())

    def test_rule_2_the_domain_names_nothing_above_it(self):
        report = domain_names_nothing_above_it()

        self.assertEqual((), report.violations, report.describe())

    def test_rule_3_nothing_draws_an_image(self):
        report = nothing_draws_an_image()

        self.assertEqual((), report.violations, report.describe())

    def test_rule_4_there_is_exactly_one_root_package(self):
        report = exactly_one_root_package()

        self.assertEqual((), report.violations, report.describe())

    def test_rule_5_the_suite_constructs_no_tk_interpreter(self):
        """The live check, over the interpreter this suite is running in.

        Every test module is imported first, because the rule is about what
        importing them did.  Discovery has already imported them by the time
        this runs; doing it again by name is cheap and makes the test say
        what it depends on rather than relying on the runner's order.
        """
        import tkinter

        for name in every_test_module():
            importlib.import_module(name)

        report = no_tk_interpreter_constructed(tkinter._default_root)

        self.assertEqual((), report.violations, report.describe())

    def test_rule_6_nothing_but_tests_depends_on_test_code(self):
        report = nothing_but_tests_depends_on_tests()

        self.assertEqual((), report.violations, report.describe())


def every_test_module():
    """Every ``test_*.py`` module in the suite, as dotted names."""
    return tuple(
        "tests." + os.path.basename(path)[:-3]
        for path in python_files(REPOSITORY_ROOT, "tests")
        if os.path.basename(path).startswith("test_")
    )


# ---------------------------------------------------------------------------
# 2. The guard cannot pass vacuously
# ---------------------------------------------------------------------------


class ItCannotPassOverAnEmptySet(unittest.TestCase):
    """A rule that looked at nothing has been skipped, not satisfied."""

    def test_every_tree_rule_inspected_something(self):
        for rule in TREE_RULES:
            report = rule()

            self.assertTrue(
                report.inspected,
                "{0} inspected no files at all".format(report.rule),
            )

    def test_a_rule_that_inspects_nothing_reports_a_violation(self):
        """Not left to the caller to remember: the report says so itself."""
        root = tempfile.mkdtemp(prefix="house-rules-empty-")
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "app"))
        with open(os.path.join(root, "app", "__init__.py"), "w") as handle:
            handle.write("")
        os.remove(os.path.join(root, "app", "__init__.py"))
        os.makedirs(os.path.join(root, "app", "domain"))
        with open(
            os.path.join(root, "app", "domain", "__init__.py"), "w"
        ) as handle:
            handle.write("")

        report = Report("a rule that looked at nothing", (), ())
        made = house_rules._report("a rule that looked at nothing", (), ())

        self.assertEqual((), report.violations)
        self.assertEqual(1, len(made.violations))
        self.assertIn("inspected no files", made.violations[0].detail)
        self.assertIn("INSPECTED NOTHING", made.describe())

    def test_each_rule_looked_at_a_file_it_must_have_looked_at(self):
        """Names real files, so a stale path is caught rather than skipped."""
        expected = {
            "no toolkit below the Shell": "terminal_game/domain/maze.py",
            "the Domain names nothing above it": "terminal_game/domain/maze.py",
            "nothing draws an image": "terminal_game/shell/grid_surface.py",
            "exactly one root package": "tests/test_house_rules.py",
            "nothing but tests depends on test code": (
                "tools/walking_skeleton.py"
            ),
            "no layer names one above it": (
                "terminal_game/application/session.py"
            ),
        }

        for rule in TREE_RULES:
            report = rule()
            wanted = expected[report.rule]

            self.assertIn(
                wanted,
                [path.replace(os.sep, "/") for path in report.inspected],
                "{0} never looked at {1}".format(report.rule, wanted),
            )

    def test_rule_3_looks_at_the_tools_as_well_as_the_application(self):
        """A script paints the real screen; SCRN-2 binds it too."""
        inspected = [
            path.replace(os.sep, "/")
            for path in nothing_draws_an_image().inspected
        ]

        self.assertIn("tools/walking_skeleton.py", inspected)
        self.assertIn("terminal_game/shell/grid_surface.py", inspected)

    def test_rule_1_does_not_look_at_the_shell_or_the_suite(self):
        """The Shell may name the toolkit, and so may a test of the adapter."""
        inspected = [
            path.replace(os.sep, "/")
            for path in no_toolkit_below_the_shell().inspected
        ]

        self.assertNotIn("terminal_game/shell/tk_toolkit.py", inspected)
        self.assertNotIn("tests/test_tk_toolkit.py", inspected)
        self.assertIn("terminal_game/presentation/frame.py", inspected)


# ---------------------------------------------------------------------------
# 3. Each rule notices what it is for, and names the place
# ---------------------------------------------------------------------------


class RuleOneNoticesTheToolkitBelowTheShell(PlantedTree):
    def test_it_names_the_file_and_the_line(self):
        plant(
            self.root,
            "app/presentation/composer.py",
            "from app.domain.maze import VALUE\nimport tkinter\n",
        )

        violation = self.only(
            no_toolkit_below_the_shell(self.root, application="app")
        )

        self.assertEqual("app/presentation/composer.py", violation.path)
        self.assertEqual(2, violation.line)
        self.assertIn("tkinter", violation.detail)

    def test_the_shell_may_name_it_and_is_not_reported(self):
        report = no_toolkit_below_the_shell(self.root, application="app")

        self.assertEqual((), report.violations, report.describe())

    def test_a_relative_import_of_the_toolkit_is_caught_too(self):
        plant(self.root, "app/domain/clockless.py", "from tkinter import Tk\n")

        violation = self.only(
            no_toolkit_below_the_shell(self.root, application="app")
        )

        self.assertEqual("app/domain/clockless.py", violation.path)


class RuleSixGuardsTheWholeChainAndNotOnlyTheDomain(PlantedTree):
    """The gap this rule was written for.

    Rule 2 guards the Domain. The plan fixes the whole chain — Shell to
    Presentation to Application to Domain — and until this rule existed the
    middle of it was unguarded: a module under `application` could import
    Presentation or the Shell and every rule in `TREE_RULES` passed. That was
    measured, not supposed.
    """

    def test_the_application_reaching_up_into_presentation_is_named(self):
        plant(
            self.root,
            "app/application/session.py",
            "from app.presentation.frame_composer import compose\n",
        )

        violation = self.only(
            no_layer_names_one_above_it(self.root, application="app")
        )

        self.assertEqual("app/application/session.py", violation.path)
        self.assertIn("app.presentation.frame_composer", violation.detail)
        self.assertIn("Application", violation.detail)

    def test_the_application_reaching_up_into_the_shell_is_named(self):
        plant(
            self.root,
            "app/application/session.py",
            "from ..shell.tk_grid import create_surface\n",
        )

        self.assertEqual(
            "app/application/session.py",
            self.only(
                no_layer_names_one_above_it(self.root, application="app")
            ).path,
        )

    def test_presentation_reaching_up_into_the_shell_is_named(self):
        plant(
            self.root,
            "app/presentation/frame_composer.py",
            "from app.shell.grid_surface import paint\n",
        )

        self.assertIn(
            "Presentation",
            self.only(
                no_layer_names_one_above_it(self.root, application="app")
            ).detail,
        )

    def test_naming_a_layer_below_is_not_a_breach(self):
        """The rule must permit the dependency it exists to direct."""
        plant(
            self.root,
            "app/application/session.py",
            "from app.domain.game_state import GameState\n",
        )
        plant(
            self.root,
            "app/presentation/frame_composer.py",
            "from app.application.session import Session\n",
        )
        plant(
            self.root,
            "app/shell/window.py",
            "from app.presentation.frame_composer import compose\n",
        )

        self.assertEqual(
            (), no_layer_names_one_above_it(self.root, application="app").violations
        )

    def test_the_shell_may_name_anything_and_the_domain_is_still_guarded(self):
        plant(self.root, "app/shell/window.py", "from app.domain.maze import Maze\n")
        plant(self.root, "app/domain/leaky.py", "from app.shell.window import W\n")

        violation = self.only(
            no_layer_names_one_above_it(self.root, application="app")
        )

        self.assertEqual("app/domain/leaky.py", violation.path)


class RuleTwoNoticesTheDomainReachingUpward(PlantedTree):
    def test_an_absolute_import_of_a_layer_above_is_named(self):
        plant(
            self.root,
            "app/domain/leaky.py",
            "from app.presentation.frame import VALUE\n",
        )

        violation = self.only(
            domain_names_nothing_above_it(self.root, application="app")
        )

        self.assertEqual("app/domain/leaky.py", violation.path)
        self.assertIn("app.presentation.frame", violation.detail)

    def test_a_relative_import_of_a_layer_above_is_named(self):
        """``from ..shell import x`` is the same breach differently spelled."""
        plant(
            self.root,
            "app/domain/leaky.py",
            "from ..shell.tk_grid import something\n",
        )

        violation = self.only(
            domain_names_nothing_above_it(self.root, application="app")
        )

        self.assertIn("app.shell.tk_grid", violation.detail)

    def test_reading_a_clock_is_named(self):
        plant(self.root, "app/domain/timed.py", "import time\n")

        violation = self.only(
            domain_names_nothing_above_it(self.root, application="app")
        )

        self.assertIn("clock", violation.detail)

    def test_reaching_for_the_global_random_source_is_named(self):
        plant(
            self.root,
            "app/domain/lucky.py",
            "import random\n\n\ndef pick(items):\n    return random.choice(items)\n",
        )

        violation = self.only(
            domain_names_nothing_above_it(self.root, application="app")
        )

        self.assertEqual(5, violation.line)
        self.assertIn("random.choice", violation.detail)

    def test_importing_random_for_the_type_alone_is_not_a_breach(self):
        """The generator and the ghost are *handed* a ``random.Random``.

        They name the type in their signatures, which is right, and a rule
        that forbade the import would fail honest work — the same shape of
        mistake amendment 2 corrected in rule 5.
        """
        plant(
            self.root,
            "app/domain/handed.py",
            "import random\n\n\ndef lay_out(source: random.Random):\n"
            "    return source.choice([1, 2])\n",
        )

        report = domain_names_nothing_above_it(self.root, application="app")

        self.assertEqual((), report.violations, report.describe())


class RuleThreeNoticesAnImage(PlantedTree):
    def test_a_canvas_image_is_named(self):
        plant(
            self.root,
            "app/shell/painter.py",
            "def paint(canvas):\n    canvas.create_image(0, 0)\n",
        )

        violation = self.only(
            nothing_draws_an_image(self.root, application="app")
        )

        self.assertEqual("app/shell/painter.py", violation.path)
        self.assertEqual(2, violation.line)
        self.assertIn("create_image", violation.detail)

    def test_a_geometric_primitive_standing_in_for_a_glyph_is_named(self):
        plant(
            self.root,
            "app/shell/painter.py",
            "def block(canvas):\n    canvas.create_rectangle(0, 0, 9, 9)\n",
        )

        violation = self.only(
            nothing_draws_an_image(self.root, application="app")
        )

        self.assertIn("create_rectangle", violation.detail)

    def test_a_photo_image_is_named_wherever_it_comes_from(self):
        plant(
            self.root,
            "app/shell/painter.py",
            "from tkinter import PhotoImage\n",
        )

        violation = self.only(
            nothing_draws_an_image(self.root, application="app")
        )

        self.assertIn("PhotoImage", violation.detail)

    def test_a_script_in_tools_is_caught_as_readily_as_the_application(self):
        plant(
            self.root,
            "tools/show.py",
            "def paint(canvas):\n    canvas.create_oval(0, 0, 9, 9)\n",
        )

        violation = self.only(
            nothing_draws_an_image(self.root, application="app")
        )

        self.assertEqual("tools/show.py", violation.path)

    def test_the_name_written_in_prose_is_not_a_breach(self):
        """The real ``grid_surface.py`` docstring lists these names to forbid
        them.  A rule that read text rather than syntax would fail the file
        whose documentation is the thing keeping the rule.
        """
        plant(
            self.root,
            "app/shell/painter.py",
            '"""Do not add create_image, create_rectangle or PhotoImage."""\n'
            "\n\ndef paint(canvas):\n    canvas.create_text(0, 0, text='x')\n",
        )

        report = nothing_draws_an_image(self.root, application="app")

        self.assertEqual((), report.violations, report.describe())


class RuleFourNoticesASecondRootPackage(PlantedTree):
    def test_a_second_root_package_is_named(self):
        """The M0 case exactly: two roots, neither importing the other."""
        plant(self.root, "terminalgame/__init__.py", "")
        plant(self.root, "terminalgame/thing.py", "VALUE = 2\n")

        violation = self.only(exactly_one_root_package(self.root))

        self.assertIn("exactly one root package", violation.detail)
        self.assertIn("app", violation.detail)
        self.assertIn("terminalgame", violation.detail)

    def test_the_suite_and_the_tools_do_not_count_as_roots(self):
        report = exactly_one_root_package(self.root)

        self.assertEqual((), report.violations, report.describe())

    def test_an_import_of_a_second_root_is_named_with_its_line(self):
        """The second witness: a root spelled without an ``__init__.py``.

        The directory half sees only proper packages, so a namespace-package
        root slips past it and the tree looks fine. The import half is what
        notices, and it names the importing file and its line.
        """
        plant(self.root, "other/thing.py", "VALUE = 2\n")
        plant(
            self.root,
            "tests/test_two.py",
            "from app.domain.maze import VALUE\nfrom other.thing import VALUE\n",
        )

        violations = exactly_one_root_package(self.root).violations
        by_path = [
            violation
            for violation in violations
            if violation.path.replace(os.sep, "/") == "tests/test_two.py"
        ]

        self.assertEqual(1, len(by_path), exactly_one_root_package(self.root))
        self.assertEqual(2, by_path[0].line)
        self.assertIn("other.thing", by_path[0].detail)


class RuleFiveNoticesAConstructedInterpreter(unittest.TestCase):
    """The rule amendment 2 rewrote, and why the rewrite mattered.

    Checked without creating a Tk interpreter, because creating one is what
    it forbids and what would put a window on somebody's screen.  The rule is
    a function of ``tkinter._default_root``; these tests hand it the two
    values that matter.
    """

    def test_no_interpreter_is_clean(self):
        report = no_tk_interpreter_constructed(None)

        self.assertEqual((), report.violations, report.describe())

    def test_an_interpreter_is_reported_and_described(self):
        stand_in = "<a Tk root, as tkinter would leave one here>"

        report = no_tk_interpreter_constructed(stand_in)

        self.assertEqual(1, len(report.violations))
        self.assertIn("window server", report.violations[0].detail)
        self.assertIn(stand_in, report.violations[0].detail)

    def test_it_does_not_fire_on_a_module_that_merely_imports_the_toolkit(self):
        """The whole point of amendment 2's correction, asserted directly.

        ``tests/test_tk_toolkit.py`` imports the real adapter, and the
        adapter imports ``tkinter``.  Amendment 1's rule — that the suite
        loads neither ``tkinter`` nor ``_tkinter`` — would fail that test,
        which is the one keeping the adapter honest.  So: the toolkit **is**
        loaded, and the rule is **still** clean.
        """
        import tkinter

        importlib.import_module("tests.test_tk_toolkit")

        self.assertIn("tkinter", sys.modules)
        self.assertEqual(
            (),
            no_tk_interpreter_constructed(tkinter._default_root).violations,
        )


class RuleSixNoticesADependencyOnTestCode(PlantedTree):
    def test_a_script_importing_the_suite_is_named(self):
        plant(
            self.root,
            "tools/show.py",
            "from tests.specimen import PICTURE\n",
        )

        violation = self.only(
            nothing_but_tests_depends_on_tests(self.root, application="app")
        )

        self.assertEqual("tools/show.py", violation.path)
        self.assertIn("tests.specimen", violation.detail)

    def test_the_application_importing_the_suite_is_named(self):
        plant(
            self.root,
            "app/presentation/thing.py",
            "import tests.doubles\n",
        )

        violation = self.only(
            nothing_but_tests_depends_on_tests(self.root, application="app")
        )

        self.assertEqual("app/presentation/thing.py", violation.path)

    def test_a_test_importing_the_application_is_not_a_breach(self):
        """Tests may reach anywhere; nothing may reach into them."""
        plant(
            self.root,
            "tests/test_more.py",
            "from app.domain.maze import VALUE\nimport tests.house_rules\n",
        )

        report = nothing_but_tests_depends_on_tests(
            self.root, application="app"
        )

        self.assertEqual((), report.violations, report.describe())


# ---------------------------------------------------------------------------
# Each rule reports separately
# ---------------------------------------------------------------------------


class TheRulesAreReportedSeparately(PlantedTree):
    """One breach turns one rule red, and the others stay clean.

    This is what makes the guard usable: six rules in one report would tell
    you the house is untidy, and these tell you which rule and where.
    """

    def test_a_toolkit_import_below_the_shell_trips_only_rule_one(self):
        plant(self.root, "app/domain/leaky.py", "import tkinter\n")

        self.assertEqual(
            1,
            len(no_toolkit_below_the_shell(self.root, application="app").violations),
        )
        self.assertEqual(
            (),
            nothing_draws_an_image(self.root, application="app").violations,
        )
        self.assertEqual((), exactly_one_root_package(self.root).violations)
        self.assertEqual(
            (),
            nothing_but_tests_depends_on_tests(
                self.root, application="app"
            ).violations,
        )

    def test_an_image_in_the_shell_trips_only_rule_three(self):
        plant(
            self.root,
            "app/shell/painter.py",
            "def paint(c):\n    c.create_image(0, 0)\n",
        )

        self.assertEqual(
            (),
            no_toolkit_below_the_shell(self.root, application="app").violations,
        )
        self.assertEqual(
            (),
            domain_names_nothing_above_it(
                self.root, application="app"
            ).violations,
        )
        self.assertEqual(
            1,
            len(nothing_draws_an_image(self.root, application="app").violations),
        )

    def test_every_rule_carries_its_own_name(self):
        names = {rule(self.root).rule for rule in (exactly_one_root_package,)}
        names |= {
            rule(self.root, application="app").rule
            for rule in (
                no_toolkit_below_the_shell,
                domain_names_nothing_above_it,
                nothing_draws_an_image,
                nothing_but_tests_depends_on_tests,
            )
        }

        self.assertEqual(5, len(names))


# ---------------------------------------------------------------------------
# The import reader the rules are built on
# ---------------------------------------------------------------------------


class ReadingTheImports(PlantedTree):
    """Relative imports are resolved, because a breach can be spelled either
    way and a rule that only saw absolute ones would be half a rule.
    """

    def test_an_absolute_import_comes_back_as_written(self):
        plant(self.root, "app/domain/x.py", "from app.domain.maze import VALUE\n")

        self.assertEqual(
            (("app.domain.maze", 1),), imports_of(self.root, "app/domain/x.py")
        )

    def test_a_sibling_relative_import_resolves_to_its_package(self):
        plant(self.root, "app/domain/x.py", "from .maze import VALUE\n")

        self.assertEqual(
            (("app.domain.maze", 1),), imports_of(self.root, "app/domain/x.py")
        )

    def test_a_parent_relative_import_resolves_across_the_layer(self):
        plant(self.root, "app/domain/x.py", "from ..shell.tk_grid import Y\n")

        self.assertEqual(
            (("app.shell.tk_grid", 1),),
            imports_of(self.root, "app/domain/x.py"),
        )

    def test_a_plain_import_is_reported_with_its_line(self):
        plant(self.root, "app/domain/x.py", "VALUE = 1\nimport enum\n")

        self.assertEqual((("enum", 2),), imports_of(self.root, "app/domain/x.py"))

    def test_an_import_inside_a_function_is_seen_too(self):
        """``walking_skeleton`` imports inside a function; a rule that only
        read the top of the file would miss exactly the breach that is there.
        """
        plant(
            self.root,
            "tools/show.py",
            "def go():\n    from tests.specimen import PICTURE\n    return PICTURE\n",
        )

        self.assertEqual(
            (("tests.specimen", 2),), imports_of(self.root, "tools/show.py")
        )


if __name__ == "__main__":
    unittest.main()
