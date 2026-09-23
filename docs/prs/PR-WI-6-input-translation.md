# WI-6: Input translation

Risk: LOW
The plan's floor: a pure lookup from a key name to an intent, with no window and no state. A defect would show up as a key doing the wrong thing, and would be local.

Lane A, Dev A. Branch `r8/wi-6-input-translation`, cut from `origin/main` at `75723e7` (WI-1 merged). Not stacked.

**What it adds:** `terminal_game/presentation/input_translation.py`, where `translate(key_name)` returns an intent.

- `"Up"`, `"Down"`, `"Left"` and `"Right"` give `"up"`, `"down"`, `"left"` and `"right"`.
- `"q"` and `"Q"` give `"quit"`.
- Anything else gives `None` (`NOTHING`).

Key names are Tk keysyms, which is what lane C's shell passes to `on_key` (PR #123, `Window.run`). The intents are plain strings, exported as `MOVE_UP`, `MOVE_DOWN`, `MOVE_LEFT`, `MOVE_RIGHT` and `QUIT`, because the application layer, which receives them in WI-12, may not import from presentation. **For lane B (WI-12):** compare against these strings, or map them into your own type at the seam. If you would rather the intent type lived in the application layer, say so and I will move it.

## Claims

Commands run from the repository root with the §1.2 environment.

| Claim | Statement (word for word from the plan) | Evidence | What the output shows |
|---|---|---|---|
| **WI-6/C1** | The up, down, left and right arrow keys translate to moves up, down, left and right respectively. | Executable: `.venv/bin/python evidence/WI-6/key_table.py`, and `.venv/bin/python -m pytest -v tests/test_input_translation.py -k c1` | The harness prints `'Up' -> 'up'`, `'Down' -> 'down'`, `'Left' -> 'left'` and `'Right' -> 'right'`. 5 PASSED lines: one per arrow, plus one showing that the four are distinct intents. |
| **WI-6/C2** | `q` and `Q` both translate to quit, including `Q` typed with Caps Lock on. | Executable: same harness, and `.venv/bin/python -m pytest -v tests/test_input_translation.py -k c2` | `'q' -> 'quit'` and `'Q' -> 'quit'`, and 2 PASSED lines. Tk reports a capital `q` as keysym `Q` whether it came from Shift or from Caps Lock, so `Q` is the case Caps Lock produces. If a Tk build reported plain `q` under Caps Lock, that also translates to quit. Either way the claim holds. |
| **WI-6/C3** | Every other key, including letters, digits, space, Return, Escape, Tab, Backspace, function keys and a modifier pressed alone, translates to nothing. | Executable: same harness, and `.venv/bin/python -m pytest -v tests/test_input_translation.py -k c3` | The harness prints the modifiers it covers, then `138 other key names -> 0 translate to something`, then `WI-6 HOLDS`. It imports the same corpus the unit tests use, so the two cannot drift apart. 139 PASSED lines: one per key name, plus a sweep asserting that exactly the six mapped names give an intent. The key names cover every letter and digit except `q`/`Q`, `space`, `Return`, `KP_Enter`, `Escape`, `Tab`, `BackSpace`, `Delete`, `F1`–`F20`, every modifier alone (`Shift_L/R`, `Control_L/R`, `Alt_L/R`, `Meta_L/R`, `Super_L/R`, `Caps_Lock` and others), keypad arrows, punctuation, and lookalikes such as `up`, `Quit` and `" q"`. |

Suite at the head: `.venv/bin/python -m pytest -q` gives **279 passed, 1 skipped**. `.venv/bin/python -m tools.layer_check` passes.

## Diff map

```
terminal_game/presentation/input_translation.py (new) -> WI-6/C1, C2, C3
tests/test_input_translation.py (new)                 -> evidence for C1-C3
evidence/WI-6/key_table.py (new)                      -> evidence for C1-C3
docs/prs/PR-WI-6-input-translation.md                 -> this brief
docs/progress/r8-wi-6-input-translation.md            -> progress log
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
