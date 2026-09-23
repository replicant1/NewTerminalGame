# WI-5: Status line

Risk: LOW
The plan's floor: a pure presentation leaf that turns a score and an outcome into 40 cells. A defect would be visible on the bottom row and local to it.

Lane A, Dev A. Branch `r8/wi-5-status-line`, cut from `origin/main` at `75723e7` (WI-1 merged). Not stacked.

**What it adds:**

- `terminal_game/presentation/status_line.py`: `status_text(score, outcome)` returns the 40 characters, and `status_row(score, outcome)` returns 40 `(character, role)` cells, all with the role `"status"`. `outcome` is one of `PLAYING` (`None`), `LOST` (`"lost"`) or `WON` (`"won"`).
  - The score is left-aligned in a fixed field, so the text after it always starts where the specimen's examples put it: cell 12 during play, 20 on a loss, 21 on a win.
  - It refuses a negative or non-integer score, an unknown outcome, and a score too long for its field, instead of shifting the text. An unhashable outcome such as `[]` is refused with the same `ValueError`.
- `terminal_game/presentation/roles.py`: the six colour-role strings (`"wall"`, `"dot"`, `"player"`, `"ghost"`, `"status"`, `"background"`). They are the same strings lane C's `terminal_game/shell/palette.py` uses on PR #123. Presentation may not import the shell, so a frame built here carries role strings the shell's frame check accepts. Lane C could import these from presentation if it wants one source; that is its call.

## Claims

Commands run from the repository root with the §1.2 environment. `-v` without `-q` prints each test's name.

| Claim | Statement (word for word from the plan) | Evidence | What the output shows |
|---|---|---|---|
| **WI-5/C1** | During play with a score of 0 the row reads exactly ` score 0    arrows, q quits`, followed by blanks to 40 cells. | Executable: `.venv/bin/python evidence/WI-5/status_rows.py`, and `.venv/bin/python -m pytest -v tests/test_status_line.py -k c1` | The harness prints `\| score 0    arrows, q quits             \|` under a 0–39 column ruler, 40 cells between the bars. The test asserts the exact string plus 13 blanks. |
| **WI-5/C2** | On a loss with a score of 37 the row reads exactly ` CAUGHT  score 37   q quits`, and on a win with a score of 274 exactly ` CLEARED  score 274  q quits`, each followed by blanks to 40 cells. | Executable: same harness, and `.venv/bin/python -m pytest -v tests/test_status_line.py -k c2` | The harness prints `\| CAUGHT  score 37   q quits             \|` and `\| CLEARED  score 274  q quits            \|`. The test asserts both exactly, with 13 and 12 blanks. |
| **WI-5/C3** | For every score from 0 to 459 in each of the three states, the row is exactly 40 cells, shows the score in decimal, and the text after the score starts in the same cell as it does in the C1 and C2 examples for that state. | Executable: same harness, and `.venv/bin/python -m pytest -v tests/test_status_line.py -k c3` | The harness sweep prints `widths [40]; score starts in cell [7]; text after it in cell [12]` for play, `[15]` and `[20]` for a loss, and `[16]` and `[21]` for a win, then `WI-5 sweep CONSISTENT`. The test runs 3 × 460 rows. It takes the tail cell by measuring the plan's example strings, not from the module's constants, and asserts each row's width, digits and tail position. |
| **WI-5/C4** | The row contains the state word (on an ending), the score and the key hints, and no other text. | Executable: `.venv/bin/python -m pytest -v tests/test_status_line.py -k c4` | 3 PASSED lines, one per state. Each asserts that the row's words are exactly `score N arrows, q quits`, `CAUGHT score N q quits` or `CLEARED score N q quits`, for scores with 1, 2, 3 digits and 459. |
| **WI-5/C5** | Every cell of the row is in the status colour. | Executable: `.venv/bin/python -m pytest -v tests/test_status_line.py -k c5`, and the harness | PASSED: every cell's role is `status`, in every state, for four scores. The harness prints `roles ['status']` beside each example row. |

Suite at the head: `.venv/bin/python -m pytest -q` gives **150 passed, 1 skipped**. `.venv/bin/python -m tools.layer_check` passes, with `status_line` and `roles` in the presentation layer.

## Diff map

```
terminal_game/presentation/status_line.py (new) -> WI-5/C1-C5
terminal_game/presentation/roles.py (new)       -> WI-5/C5 (the status role string)
tests/test_status_line.py (new)                 -> evidence for C1-C5
evidence/WI-5/status_rows.py (new)              -> evidence for C1-C3, C5
docs/prs/PR-WI-5-status-line.md                 -> this brief
docs/progress/r8-wi-5-status-line.md            -> progress log
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
