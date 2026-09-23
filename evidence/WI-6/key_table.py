"""WI-6: what each kind of key translates to, printed as a table.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-6/key_table.py

It prints the intent for the four arrows, ``q`` and ``Q``, then counts how many
of the other key names translate to anything but nothing. The other names are
the same corpus the unit tests use, imported from
``tests/test_input_translation.py`` so the two cannot drift apart: every letter
and digit except ``q``/``Q``, punctuation, space, Return, Escape, Tab,
BackSpace, F1-F20, modifiers pressed alone (Shift, Control, Alt, Meta, Super,
Caps_Lock, Num_Lock, Mode_switch), keypad arrows, and lookalike strings such as
``up`` and ``Quit``. It prints the size of that corpus.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from terminal_game.presentation.input_translation import NOTHING, translate  # noqa: E402
from test_input_translation import LETTERS_AND_DIGITS, LOOKALIKES, NAMED_OTHERS  # noqa: E402

MAPPED = ["Up", "Down", "Left", "Right", "q", "Q"]
OTHERS = NAMED_OTHERS + LETTERS_AND_DIGITS + LOOKALIKES


def main() -> int:
    for key in MAPPED:
        print("  %-8r -> %r" % (key, translate(key)))
    modifiers = [k for k in NAMED_OTHERS if k.endswith(("_L", "_R")) or k in ("Caps_Lock", "Num_Lock", "Mode_switch")]
    print("  modifiers alone among them: %s" % ", ".join(modifiers))
    leaks = [k for k in OTHERS if translate(k) is not NOTHING]
    print("  %d other key names -> %d translate to something%s"
          % (len(OTHERS), len(leaks), (": %r" % leaks) if leaks else ""))
    ok = ([translate(k) for k in MAPPED] == ["up", "down", "left", "right", "quit", "quit"]
          and not leaks)
    print("WI-6 %s" % ("HOLDS: four moves, q and Q quit, everything else nothing" if ok else "DOES NOT HOLD"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
