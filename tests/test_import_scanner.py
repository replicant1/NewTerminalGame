"""The import scanner, on its own.

``tests/test_layer_rule.py`` runs the rule over the real source tree and
asserts that it finds nothing wrong.  That assertion is only worth anything if
the scanner underneath it can see.  A scanner that returned an empty list for
every file would make the layer test pass for ever, and pass loudest on the
day somebody imports ``tkinter`` into the domain.

So these tests own one question: **given source that imports something, does
the scanner find it?**  They answer it on source written here, which is why
the answer stays true without anything in the real tree being touched.
"""

from __future__ import annotations

import os
from typing import List

from tools.layer_rule import ImportSite, find_modules, imports_in_source, scan


def imported_names(source: str, module: str = "pkg.layer.mod", is_package: bool = False) -> List[str]:
    return [site.imported for site in imports_in_source(source, module, is_package)]


# --------------------------------------------------------------------------
# The ordinary ways of naming a module
# --------------------------------------------------------------------------


def test_a_plain_import_is_found() -> None:
    assert imported_names("import tkinter\n") == ["tkinter"]


def test_a_dotted_import_keeps_its_full_name() -> None:
    assert imported_names("import os.path\n") == ["os.path"]


def test_several_names_on_one_import_line_are_all_found() -> None:
    assert imported_names("import time, random, json\n") == ["time", "random", "json"]


def test_an_aliased_import_is_recorded_under_its_real_name() -> None:
    """``import random as r`` is still an import of ``random``."""
    assert imported_names("import random as r\n") == ["random"]


def test_a_from_import_yields_both_the_package_and_the_name() -> None:
    """``c`` may itself be a submodule, so the rule has to see both.

    Without the second entry, ``from terminal_game import shell`` inside the
    domain would read as an import of ``terminal_game`` and slip through.
    """
    assert imported_names("from a.b import c\n") == ["a.b", "a.b.c"]


def test_a_star_import_records_the_package_only() -> None:
    assert imported_names("from tkinter import *\n") == ["tkinter"]


def test_a_module_that_imports_nothing_yields_nothing() -> None:
    """The scanner does not invent imports — an empty answer means empty."""
    assert imports_in_source('"""Just a docstring."""\n\nVALUE = 3\n', "pkg.layer.mod") == []


# --------------------------------------------------------------------------
# The ways somebody gets around a rule like this
# --------------------------------------------------------------------------


def test_an_import_inside_a_function_is_found() -> None:
    """Moving the import into a function is the first thing anyone tries."""
    source = "def paint():\n    import tkinter\n    return tkinter\n"
    assert imported_names(source) == ["tkinter"]


def test_an_import_inside_a_try_block_is_found() -> None:
    source = "try:\n    import tkinter\nexcept ImportError:\n    tkinter = None\n"
    assert imported_names(source) == ["tkinter"]


def test_an_import_guarded_by_type_checking_is_found() -> None:
    source = (
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from terminal_game.shell import window\n"
    )
    assert "terminal_game.shell" in imported_names(source)


def test_importlib_import_module_with_a_literal_name_is_found() -> None:
    source = "import importlib\n\ndef load():\n    return importlib.import_module('tkinter')\n"
    assert "tkinter" in imported_names(source)


def test_dunder_import_with_a_literal_name_is_found() -> None:
    assert "tkinter" in imported_names("toolkit = __import__('tkinter')\n")


def test_a_dynamic_import_is_labelled_as_dynamic() -> None:
    """The kind is carried through so a failure says how the name was written."""
    sites = imports_in_source("import importlib\nimportlib.import_module('time')\n", "pkg.layer.mod")
    dynamic = [site for site in sites if site.imported == "time"]
    assert [site.kind for site in dynamic] == ["dynamic"]


# --------------------------------------------------------------------------
# Relative imports, which have to become absolute before they can be judged
# --------------------------------------------------------------------------


def test_one_dot_from_a_plain_module_means_its_own_package() -> None:
    assert imported_names("from . import maze\n", "terminal_game.domain.grid") == [
        "terminal_game.domain",
        "terminal_game.domain.maze",
    ]


def test_one_dot_from_a_package_init_means_the_package_itself() -> None:
    assert imported_names(
        "from . import maze\n", "terminal_game.domain", is_package=True
    ) == ["terminal_game.domain", "terminal_game.domain.maze"]


def test_two_dots_climb_to_the_parent_package() -> None:
    """This is the shape a cross-layer import takes when it is written relatively."""
    assert imported_names(
        "from ..shell import window\n", "terminal_game.domain.grid"
    ) == ["terminal_game.shell", "terminal_game.shell.window"]


def test_a_relative_import_with_a_dotted_tail_resolves_in_full() -> None:
    assert imported_names(
        "from ..presentation.surface import paint\n", "terminal_game.domain.grid"
    ) == [
        "terminal_game.presentation.surface",
        "terminal_game.presentation.surface.paint",
    ]


# --------------------------------------------------------------------------
# Walking a tree on disk
# --------------------------------------------------------------------------


def write(path: str, source: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(source)


def test_find_modules_names_every_python_file_in_the_tree(tmp_path) -> None:
    root = os.path.join(str(tmp_path), "pkg")
    write(os.path.join(root, "__init__.py"), "")
    write(os.path.join(root, "domain", "__init__.py"), "")
    write(os.path.join(root, "domain", "maze.py"), "")
    write(os.path.join(root, "domain", "deep", "__init__.py"), "")
    write(os.path.join(root, "domain", "deep", "nested.py"), "")
    write(os.path.join(root, "notes.txt"), "not python")

    assert [module.name for module in find_modules(root)] == [
        "pkg",
        "pkg.domain",
        "pkg.domain.deep",
        "pkg.domain.deep.nested",
        "pkg.domain.maze",
    ]


def test_find_modules_marks_package_inits_as_packages(tmp_path) -> None:
    """The package flag is what makes a single-dot relative import resolve right."""
    root = os.path.join(str(tmp_path), "pkg")
    write(os.path.join(root, "__init__.py"), "")
    write(os.path.join(root, "maze.py"), "")

    flags = {module.name: module.is_package for module in find_modules(root)}
    assert flags == {"pkg": True, "pkg.maze": False}


def test_find_modules_ignores_compiled_bytecode(tmp_path) -> None:
    root = os.path.join(str(tmp_path), "pkg")
    write(os.path.join(root, "__init__.py"), "")
    write(os.path.join(root, "__pycache__", "stale.cpython-39.pyc"), "")
    write(os.path.join(root, "__pycache__", "ghost.py"), "import tkinter\n")

    assert [module.name for module in find_modules(root)] == ["pkg"]


def test_scan_reads_the_imports_of_each_file_it_finds(tmp_path) -> None:
    root = os.path.join(str(tmp_path), "pkg")
    write(os.path.join(root, "__init__.py"), "")
    write(os.path.join(root, "one.py"), "import time\n")
    write(os.path.join(root, "two.py"), "from . import one\n")

    found = {module.name: [site.imported for site in sites] for module, sites in scan(root).items()}
    assert found == {
        "pkg": [],
        "pkg.one": ["time"],
        "pkg.two": ["pkg", "pkg.one"],
    }
