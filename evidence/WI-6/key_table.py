"""WI-6: what each kind of key translates to, printed as a table.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-6/key_table.py

It prints the intent for the four arrows, ``q`` and ``Q``, and a count of how
many of 123 other Tk key names (letters, digits, punctuation, space, Return,
Escape, Tab, BackSpace, F1-F20, every modifier alone, keypad arrows, and
lookalike strings such as ``up`` and ``Quit``) translate to anything but nothing.
"""

from __future__ import annotations

import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terminal_game.presentation.input_translation import NOTHING, translate  # noqa: E402

MAPPED = ["Up", "Down", "Left", "Right", "q", "Q"]
OTHERS = (
    [c for c in string.ascii_letters + string.digits if c not in "qQ"]
    + ["space", "Return", "KP_Enter", "Escape", "Tab", "BackSpace", "Delete"]
    + ["F%d" % n for n in range(1, 21)]
    + ["Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L", "Meta_R",
       "Super_L", "Super_R", "Caps_Lock"]
    + ["Home", "End", "Prior", "Next", "KP_Up", "KP_Down", "KP_Left", "KP_Right"]
    + ["comma", "period", "slash", "minus", "equal", "semicolon", "apostrophe", "grave"]
    + ["up", "UP", "down", "left", "right", "Quit", "quit", "qq", ""]
)


def main() -> int:
    for key in MAPPED:
        print("  %-8r -> %r" % (key, translate(key)))
    leaks = [k for k in OTHERS if translate(k) is not NOTHING]
    print("  %d other key names -> %d translate to something%s"
          % (len(OTHERS), len(leaks), (": %r" % leaks) if leaks else ""))
    ok = ([translate(k) for k in MAPPED] == ["up", "down", "left", "right", "quit", "quit"]
          and not leaks)
    print("WI-6 %s" % ("HOLDS: four moves, q and Q quit, everything else nothing" if ok else "DOES NOT HOLD"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
