"""The layer rule, stated as a test rather than as a paragraph.

Implementation plan §3: "The Screen port is an interface; the terminal
adapter is the only thing behind it that knows `curses` exists. Nothing above
the port imports `curses`."

That rule is easy to keep while the tree is four files and easy to lose once
it is forty. This is the cheapest possible guard on it: if a second module
ever imports curses, the next person to run the suite finds out.
"""

from __future__ import annotations

import os
import unittest

import terminalgame

PACKAGE_ROOT = os.path.dirname(os.path.abspath(terminalgame.__file__))

#: The one module in the whole game process allowed to know curses exists.
THE_ADAPTER = os.path.join("screen", "curses_adapter.py")


def python_files():
    for directory, _, filenames in os.walk(PACKAGE_ROOT):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                path = os.path.join(directory, filename)
                yield os.path.relpath(path, PACKAGE_ROOT), path


def source_of(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def imports(source, module_name):
    """Does this source actually import that module?

    Crude on purpose — it looks at import statements only, so the word
    appearing in a comment or a docstring does not count.
    """
    for line in source.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ")
                or stripped.startswith("from ")):
            continue
        words = stripped.replace(",", " ").split()
        if module_name in words:
            return True
        for word in words:
            if word.split(".")[0] == module_name and word not in ("from", "import"):
                return True
    return False


class LayerRuleTest(unittest.TestCase):

    def test_only_the_terminal_adapter_knows_that_curses_exists(self):
        offenders = [name for name, path in python_files()
                     if name != THE_ADAPTER and imports(source_of(path), "curses")]
        self.assertEqual([], offenders,
                         "curses has leaked above the screen port; only {0} "
                         "may import it (implementation plan §3)"
                         .format(THE_ADAPTER))

    def test_the_adapter_is_where_it_is_said_to_be(self):
        # If the adapter is moved or renamed, the test above would quietly
        # start permitting nothing at all rather than permitting the wrong
        # thing. This is what stops that going unnoticed.
        names = [name for name, _ in python_files()]
        self.assertIn(THE_ADAPTER, names)
        self.assertTrue(imports(source_of(os.path.join(PACKAGE_ROOT, THE_ADAPTER)),
                                "curses"))

    def test_the_game_process_never_touches_the_desktop(self):
        """Caution C11 — only the launcher drives windows.

        `subprocess` is how the desktop gets driven, by `osascript`. The game
        process has no business with it at all.
        """
        offenders = [name for name, path in python_files()
                     if imports(source_of(path), "subprocess")]
        self.assertEqual([], offenders,
                         "the game process must not shell out; moving, "
                         "titling and closing windows belongs to the "
                         "launcher alone (caution C11)")


if __name__ == "__main__":
    unittest.main()
