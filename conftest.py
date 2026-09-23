"""Root conftest: loads the suite's guards for every run from the repository root.

``tools.pytest_guards`` refuses a wrong interpreter, keeps desktop tests out of
the default suite and stops an unmarked test from opening a window.  ``pytester``
is pytest's own plugin for running pytest inside a test; the guards' tests use it.
"""

pytest_plugins = ["tools.pytest_guards", "pytester"]
