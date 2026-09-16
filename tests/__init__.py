"""The test suite.

Run it, from the repository root, with exactly:

    /usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"

``/usr/bin/python3`` is 3.9.6 with Tk 8.5.  The other interpreter on this
machine has no ``_tkinter`` at all and the whole shell layer fails to import
on it.

No test in this suite opens a window.  Anything that has to appear on screen
is a separate script a person runs deliberately, and it is never named
``test_*``.
"""
