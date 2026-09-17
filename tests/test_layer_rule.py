"""The dependency rule of IMPLEMENTATION_PLAN.md section 1.3, as a test.

The plan says why this is a test rather than a paragraph: *"a sentence
remembers what was true once and nothing re-runs it."*

There are two halves here and they do different jobs.

**Over the real tree** — one test, which reads every module under
``terminal_game`` and asserts the rule holds.  That is the assertion the whole
project leans on, and it is the one that will go red on the day somebody
reaches across a layer.

**Over fixture trees** — the rest, which build small packages in ``tmp_path``
that break the rule on purpose and assert that the checker names the
violation.  These are fixtures, written to be wrong; no working code is
altered to produce them, and nothing outside ``tmp_path`` is touched.  They
exist because the real-tree test would pass just as happily against a checker
that judged nothing at all, and at WI-0 the real tree is four empty packages,
so it would pass vacuously by construction.
"""

from __future__ import annotations

import os
from typing import Dict, List

from tools.layer_rule import (
    LAYERS,
    PAINTING_MODULE,
    TOOLKIT_MODULES,
    check_imports,
    check_package,
    describe,
    find_modules,
    imports_in_source,
    layer_of,
    scan,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(REPO_ROOT, "terminal_game")
PACKAGE_NAME = "terminal_game"


# --------------------------------------------------------------------------
# The real tree
# --------------------------------------------------------------------------


def test_the_real_source_tree_obeys_the_layer_rule() -> None:
    """Domain names nothing above it and nothing impure; application names no
    toolkit and no clock; only the painting module names the toolkit."""
    violations = check_package(PACKAGE_DIR)
    assert violations == [], describe(violations)


def test_the_scan_visits_every_python_file_in_the_package() -> None:
    """The rule is only as wide as the set of files it read.

    Found independently of the scanner's own walk, so that a scanner which
    quietly skipped a directory would be caught rather than believed.
    """
    on_disk = set()
    for dirpath, dirnames, filenames in os.walk(PACKAGE_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for filename in filenames:
            if filename.endswith(".py"):
                on_disk.add(os.path.join(dirpath, filename))

    scanned = {module.path for module in find_modules(PACKAGE_DIR)}
    assert scanned == on_disk
    assert on_disk, "the package has no source files at all, which cannot be right"


def test_all_four_layers_exist_as_packages() -> None:
    """The four names are not a convention to be remembered; they are on disk."""
    scanned = {module.name for module in find_modules(PACKAGE_DIR)}
    expected = {PACKAGE_NAME} | {
        "{}.{}".format(PACKAGE_NAME, layer) for layer in LAYERS
    }
    assert expected <= scanned, "missing layer packages: {}".format(
        sorted(expected - scanned)
    )


def test_every_module_in_the_package_belongs_to_a_layer() -> None:
    """Code directly under ``terminal_game`` would sit outside the rule.

    ``terminal_game/__init__.py`` is the one exemption and it is deliberate:
    it is the package marker, not a place for logic.
    """
    unplaced = [
        module.name
        for module in find_modules(PACKAGE_DIR)
        if module.name != PACKAGE_NAME and layer_of(module.name, PACKAGE_NAME) is None
    ]
    assert unplaced == [], (
        "these modules are in no layer, so the rule cannot judge them; move "
        "each into one of {}: {}".format(", ".join(LAYERS), unplaced)
    )


def test_nothing_in_the_package_imports_the_developer_tooling() -> None:
    """``tools`` is outside the scanned tree; the game must not depend on it."""
    reaching = [
        site.describe()
        for sites in scan(PACKAGE_DIR).values()
        for site in sites
        if site.imported.split(".")[0] == "tools"
    ]
    assert reaching == []


def test_exactly_one_module_may_name_the_toolkit_inside_presentation() -> None:
    """The exception is a single module, and widening it should be visible.

    If WI-5 renames its surface module, this test is not what fails — the
    constant moves with it.  What this pins is that the exception stays
    *one* module and stays inside presentation.
    """
    assert isinstance(PAINTING_MODULE, str)
    assert PAINTING_MODULE.startswith(PACKAGE_NAME + ".presentation.")
    assert layer_of(PAINTING_MODULE, PACKAGE_NAME) == "presentation"


# --------------------------------------------------------------------------
# Fixture trees, built wrong on purpose
# --------------------------------------------------------------------------


def build(tmp_path, modules: Dict[str, str], root: str = "terminal_game") -> str:
    """Write a fixture package and return its directory.

    ``modules`` maps a dotted module name to its source.  Missing ``__init__``
    files are created empty, so a fixture only has to write the module whose
    imports are the point.
    """
    package_dir = os.path.join(str(tmp_path), root)
    needed = set()
    for name in modules:
        parts = name.split(".")
        for index in range(1, len(parts)):
            needed.add(".".join(parts[:index]))
    for name in sorted(needed | set(modules)):
        parts = name.split(".")
        assert parts[0] == root
        if name in modules:
            path = os.path.join(package_dir, *parts[1:])
            path = path + ".py" if parts[1:] else os.path.join(package_dir, "__init__.py")
            source = modules[name]
        else:
            path = os.path.join(package_dir, *parts[1:], "__init__.py")
            source = ""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(source)
    for layer in LAYERS:
        init = os.path.join(package_dir, layer, "__init__.py")
        if not os.path.exists(init):
            os.makedirs(os.path.dirname(init), exist_ok=True)
            open(init, "w").close()
    root_init = os.path.join(package_dir, "__init__.py")
    if not os.path.exists(root_init):
        open(root_init, "w").close()
    return package_dir


def rules_broken(tmp_path, modules: Dict[str, str]) -> List[str]:
    """The ``rule`` handle of every violation the checker reports, sorted."""
    return sorted(v.rule for v in check_package(build(tmp_path, modules)))


def test_a_clean_fixture_tree_reports_nothing(tmp_path) -> None:
    """The baseline: the checker is not simply reporting everything it sees."""
    assert rules_broken(
        tmp_path,
        {
            "terminal_game.domain.maze": "from dataclasses import dataclass\nimport enum\n",
            "terminal_game.application.session": "from terminal_game.domain import maze\n",
            "terminal_game.presentation.frame": "from terminal_game.application import session\n",
            "terminal_game.shell.main": "import tkinter, time, os, random\n",
        },
    ) == []


def test_domain_may_not_import_application(tmp_path) -> None:
    assert rules_broken(
        tmp_path,
        {"terminal_game.domain.maze": "from terminal_game.application import session\n"},
    ) == ["layer-order"]


def test_domain_may_not_import_presentation_or_shell(tmp_path) -> None:
    assert rules_broken(
        tmp_path,
        {
            "terminal_game.domain.maze": (
                "from terminal_game.presentation import frame\n"
                "from terminal_game.shell import window\n"
            )
        },
    ) == ["layer-order", "layer-order"]  # two lines, two layers, two mistakes


def test_a_relative_cross_layer_import_is_caught_too(tmp_path) -> None:
    """Written with dots it is the same violation, and it must read the same."""
    assert rules_broken(
        tmp_path, {"terminal_game.domain.maze": "from ..shell import window\n"}
    ) == ["layer-order"]


def test_one_written_import_line_reports_as_one_violation(tmp_path) -> None:
    """``from X import Y`` is two names to the scanner and one line to a human.

    Reporting it twice would make every cross-layer import look like two
    mistakes, and the count in a failure message is the first thing anyone
    reads.
    """
    assert rules_broken(
        tmp_path,
        {"terminal_game.domain.maze": "from terminal_game.shell import window\n"},
    ) == ["layer-order"]


def test_two_things_named_on_one_line_still_report_as_two(tmp_path) -> None:
    """Collapsing must not swallow a second, genuinely different name."""
    assert rules_broken(
        tmp_path, {"terminal_game.domain.maze": "import tkinter, random\n"}
    ) == ["domain-purity", "domain-purity"]


def test_application_may_not_import_presentation(tmp_path) -> None:
    assert rules_broken(
        tmp_path,
        {"terminal_game.application.session": "from terminal_game.presentation import frame\n"},
    ) == ["layer-order"]


def test_presentation_may_not_import_shell(tmp_path) -> None:
    assert rules_broken(
        tmp_path,
        {"terminal_game.presentation.frame": "from terminal_game.shell import window\n"},
    ) == ["layer-order"]


def test_a_layer_may_import_itself_and_everything_below_it(tmp_path) -> None:
    assert rules_broken(
        tmp_path,
        {
            "terminal_game.domain.maze": "from terminal_game.domain import grid\n",
            "terminal_game.domain.grid": "",
            "terminal_game.presentation.frame": (
                "from terminal_game.domain import maze\n"
                "from terminal_game.application import session\n"
                "from terminal_game.presentation import glyphs\n"
            ),
            "terminal_game.presentation.glyphs": "",
        },
    ) == []


def test_domain_may_not_read_a_clock(tmp_path) -> None:
    assert rules_broken(tmp_path, {"terminal_game.domain.maze": "import time\n"}) == [
        "domain-purity"
    ]


def test_domain_may_not_reach_for_a_module_level_random_source(tmp_path) -> None:
    """MAZE-4/5/6 are testable only because randomness arrives as an argument."""
    assert rules_broken(tmp_path, {"terminal_game.domain.maze": "import random\n"}) == [
        "domain-purity"
    ]


def test_domain_may_not_touch_the_filesystem_or_the_environment(tmp_path) -> None:
    assert rules_broken(
        tmp_path, {"terminal_game.domain.maze": "import os\nimport pathlib\nimport sys\n"}
    ) == ["domain-purity", "domain-purity", "domain-purity"]


def test_domain_may_not_start_a_process_or_a_thread(tmp_path) -> None:
    assert rules_broken(
        tmp_path, {"terminal_game.domain.maze": "import subprocess\nimport threading\n"}
    ) == ["domain-purity", "domain-purity"]


def test_domain_may_not_name_the_toolkit(tmp_path) -> None:
    assert rules_broken(tmp_path, {"terminal_game.domain.maze": "import tkinter\n"}) == [
        "domain-purity"
    ]


def test_domain_may_use_pure_standard_library_modules(tmp_path) -> None:
    """The rule bans impurity, not the standard library."""
    assert rules_broken(
        tmp_path,
        {
            "terminal_game.domain.maze": (
                "from __future__ import annotations\n"
                "import enum\nimport dataclasses\nimport itertools\n"
                "import collections\nimport typing\nimport math\n"
            )
        },
    ) == []


def test_application_may_not_name_the_toolkit(tmp_path) -> None:
    assert rules_broken(
        tmp_path, {"terminal_game.application.session": "import tkinter\n"}
    ) == ["application-toolkit"]


def test_application_may_not_read_a_clock(tmp_path) -> None:
    """A tick arrives as a call; the cadence belongs to the shell's timer."""
    assert rules_broken(
        tmp_path, {"terminal_game.application.session": "from time import monotonic\n"}
    ) == ["application-clock"]


def test_application_may_still_use_the_filesystem_free_standard_library(tmp_path) -> None:
    """The ban on application is the toolkit and the clock, and no more."""
    assert rules_broken(
        tmp_path, {"terminal_game.application.session": "import enum\nimport typing\n"}
    ) == []


def test_presentation_may_not_name_the_toolkit_outside_the_painting_module(tmp_path) -> None:
    assert rules_broken(
        tmp_path, {"terminal_game.presentation.frame": "import tkinter\n"}
    ) == ["presentation-toolkit"]


def test_the_painting_module_may_name_the_toolkit(tmp_path) -> None:
    """The one exception, and the reason the layer is testable at all."""
    assert rules_broken(tmp_path, {PAINTING_MODULE: "import tkinter\n"}) == []


def test_the_shell_may_name_anything(tmp_path) -> None:
    assert rules_broken(
        tmp_path,
        {
            "terminal_game.shell.main": (
                "import tkinter, time, os, sys, random, subprocess\n"
                "from terminal_game.presentation import frame\n"
                "from terminal_game.application import session\n"
                "from terminal_game.domain import maze\n"
            )
        },
    ) == []


def test_a_module_in_no_layer_is_reported(tmp_path) -> None:
    """Otherwise the rule is dodged by putting the module one level up."""
    assert rules_broken(tmp_path, {"terminal_game.helpers": "import tkinter\n"}) == [
        "unplaced-module"
    ]


def test_a_dynamic_import_does_not_escape_the_rule(tmp_path) -> None:
    """Naming the toolkit in a string is still naming the toolkit."""
    assert rules_broken(
        tmp_path,
        {
            "terminal_game.domain.maze": (
                "import importlib\n\n"
                "def toolkit():\n    return importlib.import_module('tkinter')\n"
            )
        },
    ) == ["domain-purity"]


def test_an_import_hidden_inside_a_function_does_not_escape_the_rule(tmp_path) -> None:
    assert rules_broken(
        tmp_path,
        {"terminal_game.domain.maze": "def draw():\n    import tkinter\n    return tkinter\n"},
    ) == ["domain-purity"]


# --------------------------------------------------------------------------
# What a failure tells the person reading it
# --------------------------------------------------------------------------


def test_a_violation_names_the_module_the_line_and_what_was_imported() -> None:
    """A red suite that does not say where is a red suite somebody ignores."""
    source = "import tkinter\n"
    sites = imports_in_source(source, "terminal_game.domain.maze")
    violations = check_imports(sites, [], PACKAGE_NAME)

    assert len(violations) == 1
    rendered = describe(violations)
    assert "terminal_game.domain.maze" in rendered
    assert "tkinter" in rendered
    assert ":1" in rendered
    assert "domain-purity" in rendered


def test_the_toolkit_set_covers_the_binding_the_project_actually_uses() -> None:
    """``tkinter`` is the toolkit of section 1.2, and ``_tkinter`` is under it."""
    assert "tkinter" in TOOLKIT_MODULES
    assert "_tkinter" in TOOLKIT_MODULES
