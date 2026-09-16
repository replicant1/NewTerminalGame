# -*- coding: utf-8 -*-
"""The single command that plays the game (WI-18).

    /usr/bin/python3 -m terminal_game

The interpreter matters: ``/usr/bin/python3`` is 3.9.6 with Tk 8.5.9, and
the other Python on this machine has no windowing toolkit at all.  Write the
path out in full.

There is nothing here but the call.  The assembly lives in
:mod:`terminal_game.shell.game`, which is in the Shell layer because it is
the only layer allowed to name the toolkit; this file names no toolkit and
holds no decision, so the layer guard has nothing to catch.
"""

import sys

from terminal_game.shell.game import main

if __name__ == "__main__":  # pragma: no cover - this is the command itself
    sys.exit(main(sys.argv[1:]))
