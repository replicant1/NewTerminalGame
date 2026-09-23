"""WI-5: the status row, printed so you can read it.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-5/status_rows.py

It prints a column ruler, then the row for each of the plan's three examples
between ``|`` bars (40 cells exactly, trailing blanks visible as the gap before
the right bar), with the set of colour roles used.  Then it sweeps every score
from 0 to 459 in each state and reports, per state, the cells the score and the
text after it start in, and every width seen.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terminal_game.presentation.status_line import LOST, PLAYING, WON, status_row, status_text  # noqa: E402

CASES = [("play, score 0", 0, PLAYING), ("loss, score 37", 37, LOST), ("win, score 274", 274, WON)]


def main() -> int:
    print("      " + "".join(str(i // 10) for i in range(40)))
    print("      " + "".join(str(i % 10) for i in range(40)))
    for label, score, outcome in CASES:
        row = status_row(score, outcome)
        text = "".join(c for c, _ in row)
        print("     |%s|  %-15s roles %s" % (text, label, sorted({r for _, r in row})))
    print()
    ok = True
    for name, outcome, word in (("play", PLAYING, "arrows"), ("loss", LOST, "q quits"),
                                ("win", WON, "q quits")):
        widths, score_cells, tail_cells = set(), set(), set()
        for score in range(460):
            text = status_text(score, outcome)
            widths.add(len(text))
            score_cells.add(text.index("score ") + 6)
            tail_cells.add(text.index(word, text.index("score ") + 6))
        print("%-4s scores 0-459: widths %s; score starts in cell %s; text after it in cell %s"
              % (name, sorted(widths), sorted(score_cells), sorted(tail_cells)))
        ok &= widths == {40} and len(score_cells) == 1 and len(tail_cells) == 1
    print("WI-5 sweep %s" % ("CONSISTENT: every row 40 cells, one score cell and one tail cell per state"
                             if ok else "INCONSISTENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
