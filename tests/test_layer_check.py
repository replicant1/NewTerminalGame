"""WI-1/C3, C4: the layer rule of IMPLEMENTATION_PLAN.md section 1.4 is a test.

Most tests build a small sample tree in a temporary directory, with its own
``pyproject.toml`` declaring the layers the same way this repository does, and
assert exactly what :func:`tools.layer_check.check_repository` reports.  The
last group runs the check over the real tree.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from tools import layer_check

ROOT = Path(__file__).resolve().parents[1]

DECLARATION = """
[tool.terminal_game.layers]
shell = "terminal_game.shell"
presentation = "terminal_game.presentation"
application = "terminal_game.application"
domain = "terminal_game.domain"
"""

EMPTY_LAYERS = {
    "terminal_game/__init__.py": "",
    "terminal_game/shell/__init__.py": "",
    "terminal_game/presentation/__init__.py": "",
    "terminal_game/application/__init__.py": "",
    "terminal_game/domain/__init__.py": "",
}


def _tree(tmp_path: Path, modules: dict, declaration: str = DECLARATION,
          base: dict = EMPTY_LAYERS) -> Path:
    (tmp_path / "pyproject.toml").write_text(declaration)
    for name, source in {**base, **modules}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source))
    return tmp_path


def _found(tmp_path, modules, **kwargs):
    """(module, imported, rule) for every violation in a sample tree."""
    report = layer_check.check_repository(_tree(tmp_path, modules, **kwargs))
    return [(v.module, v.imported, v.rule) for v in report.violations]


# --------------------------------------------------------------------------
# WI-1/C3: every import that breaks the rule is reported, naming both ends
# --------------------------------------------------------------------------


def test_a_domain_module_importing_the_shell_is_named_with_what_it_imported(tmp_path):
    report = layer_check.check_repository(_tree(tmp_path, {
        "terminal_game/shell/window.py": "",
        "terminal_game/domain/maze.py": "import terminal_game.shell.window\n",
    }))
    assert len(report.violations) == 1
    violation = report.violations[0]
    assert (violation.module, violation.imported, violation.rule, violation.lineno) == (
        "terminal_game.domain.maze", "terminal_game.shell.window", "upward", 1)
    assert violation.describe().startswith(
        "terminal_game.domain.maze:1 imports terminal_game.shell.window  [upward]")
    assert not report.ok


@pytest.mark.parametrize("importer, source, imported", [
    ("terminal_game/application/turns.py",
     "from terminal_game.presentation import frames\n", "terminal_game.presentation.frames"),
    ("terminal_game/domain/maze.py", "from ..shell import window\n", "terminal_game.shell.window"),
    ("terminal_game/domain/maze.py", "from terminal_game import application\n",
     "terminal_game.application"),
    ("terminal_game/presentation/frames.py", "from terminal_game.shell.window import Window\n",
     "terminal_game.shell.window.Window"),
    ("terminal_game/domain/sub/deep.py", "from ...application import turns\n",
     "terminal_game.application.turns"),
])
def test_every_form_of_upward_import_is_reported(tmp_path, importer, source, imported):
    modules = {importer: source, "terminal_game/domain/sub/__init__.py": ""}
    found = _found(tmp_path, modules)
    module = importer[:-3].replace("/", ".")
    assert found == [(module, imported, "upward")]


def test_importing_downward_and_sideways_is_allowed(tmp_path):
    assert _found(tmp_path, {
        "terminal_game/shell/window.py":
            "import tkinter\nimport os\nimport time\nfrom terminal_game.presentation import frames\n"
            "from terminal_game.application import session\nfrom terminal_game.domain import maze\n",
        "terminal_game/presentation/frames.py":
            "from terminal_game.application import session\nfrom . import glyphs\n",
        "terminal_game/presentation/glyphs.py": "from terminal_game.domain.maze import Maze\n",
        "terminal_game/application/session.py": "from ..domain import maze\nimport random\n",
        "terminal_game/domain/maze.py":
            "from __future__ import annotations\nimport random\nfrom typing import List\n"
            "from terminal_game.domain import game\n\n"
            "def generate(rng: random.Random, seed: int):\n"
            "    return random.Random(seed)\n",
        "terminal_game/domain/game.py": "from dataclasses import dataclass\n",
    }) == []


@pytest.mark.parametrize("layer", ["presentation", "application", "domain"])
@pytest.mark.parametrize("source, imported", [
    ("import tkinter\n", "tkinter"),
    ("from tkinter import ttk\n", "tkinter"),
    ("import os.path\n", "os.path"),
    ("import subprocess\n", "subprocess"),
    ("import AppKit\n", "AppKit"),
    ("import importlib\nimportlib.import_module('tkinter')\n", "tkinter"),
    ("__import__('_tkinter')\n", "_tkinter"),
])
def test_only_the_shell_may_import_the_toolkit_or_the_operating_system(tmp_path, layer, source, imported):
    found = _found(tmp_path, {"terminal_game/%s/thing.py" % layer: source})
    assert found == [("terminal_game.%s.thing" % layer, imported, "toolkit-or-os")]


@pytest.mark.parametrize("source, imported, rule", [
    ("from builtins import __import__ as load\nload('terminal_game.shell.window')\n",
     "terminal_game.shell.window", "upward"),
    ("from importlib import import_module as im\nim('tkinter')\n", "tkinter", "toolkit-or-os"),
    ("import importlib as il\nil.import_module('tkinter')\n", "tkinter", "toolkit-or-os"),
    ("import builtins\nbuiltins.__import__('tkinter')\n", "tkinter", "toolkit-or-os"),
    ("import importlib\nimportlib.__import__('terminal_game.shell')\n",
     "terminal_game.shell", "upward"),
])
def test_an_aliased_import_function_is_followed(tmp_path, source, imported, rule):
    """Copilot, PR #122: aliases of ``__import__`` and ``import_module`` must not hide an import."""
    found = _found(tmp_path, {"terminal_game/domain/thing.py": source,
                              "terminal_game/shell/window.py": ""})
    assert found == [("terminal_game.domain.thing", imported, rule)]


@pytest.mark.parametrize("source", [
    "import importlib\nloader = importlib.import_module\n",
    "from importlib import import_module\nLOADERS = [import_module]\n",
    "import importlib\ngetattr(importlib, 'import_module')('tkinter')\n",
])
def test_an_import_function_used_other_than_by_a_literal_call_is_reported(tmp_path, source):
    found = _found(tmp_path, {"terminal_game/domain/thing.py": source})
    assert found == [("terminal_game.domain.thing", "<dynamic import>", "dynamic-import")]


def test_a_dynamic_import_it_cannot_read_is_reported_outside_the_shell(tmp_path):
    found = _found(tmp_path, {
        "terminal_game/domain/thing.py": "from importlib import import_module\nimport_module(NAME)\n",
        "terminal_game/shell/thing.py": "from importlib import import_module\nimport_module(NAME)\n",
    })
    assert found == [("terminal_game.domain.thing", "<dynamic import>", "dynamic-import")]


@pytest.mark.parametrize("layer", ["application", "domain"])
@pytest.mark.parametrize("source, imported", [
    ("import time\n", "time"),
    ("from datetime import datetime\n", "datetime"),
    ("import sched\n", "sched"),
])
def test_the_application_and_the_domain_read_no_clock(tmp_path, layer, source, imported):
    found = _found(tmp_path, {"terminal_game/%s/thing.py" % layer: source})
    assert found == [("terminal_game.%s.thing" % layer, imported, "clock")]


def test_the_domain_uses_the_standard_library_only(tmp_path):
    found = _found(tmp_path, {
        "terminal_game/domain/thing.py": "import pytest\n",
        "terminal_game/application/thing.py": "import pytest\n",
    })
    assert found == [("terminal_game.domain.thing", "pytest", "stdlib-only")]


@pytest.mark.parametrize("source, used", [
    ("import random\nx = random.randint(1, 6)\n", "random.randint"),
    ("from random import choice\n", "random.choice"),
    ("import random as r\nr.shuffle([])\n", "random.shuffle"),
    ("import random\nrng = random.Random()\n", "random.Random() with no seed"),
    ("from random import Random\nrng = Random()\n", "random.Random() with no seed"),
    ("import random\nrng = random.Random(None)\n", "random.Random() with no seed"),
    ("from random import Random\nrng = Random(x=None)\n", "random.Random() with no seed"),
    ("import secrets\n", "secrets"),
    ("import uuid\n", "uuid"),
])
def test_the_domain_uses_no_randomness_it_was_not_handed(tmp_path, source, used):
    found = _found(tmp_path, {"terminal_game/domain/thing.py": source})
    assert found == [("terminal_game.domain.thing", used, "randomness")]


def test_a_module_outside_every_layer_is_reported(tmp_path):
    found = _found(tmp_path, {
        "terminal_game/helpers.py": "",
        "terminal_game/domain/maze.py": "import terminal_game.helpers\n",
    })
    assert sorted(found) == [
        ("terminal_game.domain.maze", "terminal_game.helpers", "undeclared"),
        ("terminal_game.helpers", "(nothing)", "undeclared"),
    ]


def test_the_entry_modules_are_held_to_the_shells_rules(tmp_path):
    assert _found(tmp_path, {
        "terminal_game/__main__.py": "import tkinter\nfrom terminal_game.shell import window\n",
        "terminal_game/shell/window.py": "",
    }) == []
    assert _found(tmp_path, {
        "terminal_game/domain/maze.py": "from terminal_game import __main__\n",
    }) == [("terminal_game.domain.maze", "terminal_game.__main__", "upward")]


def test_every_violation_in_a_tree_is_reported_not_just_the_first(tmp_path):
    found = _found(tmp_path, {
        "terminal_game/shell/window.py": "",
        "terminal_game/presentation/frames.py": "import tkinter\nimport terminal_game.shell.window\n",
        "terminal_game/application/session.py": "import time\nimport terminal_game.presentation.frames\n",
        "terminal_game/domain/maze.py": "import terminal_game.application.session\nimport os\n",
    })
    assert sorted(found) == sorted([
        ("terminal_game.presentation.frames", "tkinter", "toolkit-or-os"),
        ("terminal_game.presentation.frames", "terminal_game.shell.window", "upward"),
        ("terminal_game.application.session", "time", "clock"),
        ("terminal_game.application.session", "terminal_game.presentation.frames", "upward"),
        ("terminal_game.domain.maze", "terminal_game.application.session", "upward"),
        ("terminal_game.domain.maze", "os", "toolkit-or-os"),
    ])


@pytest.mark.parametrize("importer, source", [
    ("terminal_game/domain/maze.py", "from .... import x\n"),
    ("terminal_game/domain/maze.py", "from ... import x\n"),
    ("terminal_game/__main__.py", "from .. import x\n"),
])
def test_a_relative_import_climbing_out_of_the_package_is_reported(tmp_path, importer, source):
    """``from ... import x`` in ``terminal_game.domain.maze`` is beyond the top-level package."""
    found = _found(tmp_path, {importer: source})
    module = importer[:-3].replace("/", ".")
    assert [(m, rule) for m, _, rule in found] == [(module, "unresolvable")]


# --------------------------------------------------------------------------
# WI-1/C4: it counts what it examined, and examining nothing is a failure
# --------------------------------------------------------------------------


def test_it_reports_how_many_modules_it_examined_in_each_layer(tmp_path):
    report = layer_check.check_repository(_tree(tmp_path, {
        "terminal_game/shell/window.py": "",
        "terminal_game/shell/keys.py": "",
        "terminal_game/domain/maze.py": "",
        "terminal_game/domain/generator/__init__.py": "",
        "terminal_game/domain/generator/carve.py": "",
        "terminal_game/__main__.py": "",
    }))
    assert report.examined == {"shell": 3, "presentation": 1, "application": 1,
                               "domain": 4, "entry": 2}
    assert report.summary().splitlines()[0] == (
        "layer check examined: shell 3, presentation 1, application 1, domain 4, entry 2")
    assert report.ok


def test_a_declared_layer_with_no_module_fails(tmp_path):
    base = {k: v for k, v in EMPTY_LAYERS.items() if "presentation" not in k}
    (tmp_path / "terminal_game" / "presentation").mkdir(parents=True)  # there, but empty
    report = layer_check.check_repository(_tree(tmp_path, {}, base=base))
    assert report.violations == []
    assert report.examined["presentation"] == 0
    assert report.problems == [
        "examined no module in the presentation layer (terminal_game.presentation), which the "
        "tree declares; a check that examined nothing proves nothing"]
    assert not report.ok


def test_a_tree_with_no_package_at_all_fails_on_every_layer(tmp_path):
    report = layer_check.check_repository(_tree(tmp_path, {}, base={}))
    assert [p.split(" (")[0] for p in report.problems] == [
        "examined no module in the %s layer" % name for name in layer_check.LAYER_ORDER]
    assert not report.ok


def test_a_module_it_cannot_parse_fails_instead_of_being_skipped(tmp_path):
    report = layer_check.check_repository(_tree(tmp_path, {
        "terminal_game/domain/broken.py": "def (:\n"}))
    assert len(report.problems) == 1
    assert "broken.py" in report.problems[0] and "not checked" in report.problems[0]
    assert not report.ok


def test_a_declaration_missing_a_layer_is_refused(tmp_path):
    declaration = DECLARATION.replace('domain = "terminal_game.domain"\n', "")
    with pytest.raises(ValueError, match=r"missing \['domain'\]"):
        layer_check.check_repository(_tree(tmp_path, {}, declaration=declaration))


def test_a_declaration_with_an_unknown_layer_is_refused(tmp_path):
    declaration = DECLARATION + 'utilities = "terminal_game.utilities"\n'
    with pytest.raises(ValueError, match=r"unknown \['utilities'\]"):
        layer_check.check_repository(_tree(tmp_path, {}, declaration=declaration))


def test_the_command_line_prints_the_counts_and_fails_on_a_violation(tmp_path, capsys):
    root = _tree(tmp_path, {"terminal_game/domain/maze.py": "import tkinter\n"})
    assert layer_check.main([str(root)]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "layer check examined: shell 1, presentation 1, application 1, domain 2, entry 1"
    assert out[1].startswith("VIOLATION terminal_game.domain.maze:1 imports tkinter  [toolkit-or-os]")
    assert out[-1] == "layer check: FAIL (1 violation(s), 0 problem(s))"


# --------------------------------------------------------------------------
# The real tree
# --------------------------------------------------------------------------


def test_the_real_tree_breaks_no_layer_rule_and_examines_every_layer():
    report = layer_check.check_repository(ROOT)
    assert report.violations == [], report.summary()
    assert report.problems == [], report.summary()
    for name in layer_check.LAYER_ORDER:
        assert report.examined[name] >= 1, report.summary()


def test_the_real_declaration_names_the_four_layers_of_section_1_4():
    assert layer_check.read_declaration(ROOT / "pyproject.toml") == {
        "shell": "terminal_game.shell",
        "presentation": "terminal_game.presentation",
        "application": "terminal_game.application",
        "domain": "terminal_game.domain",
    }
