# WI-3 follow-up: the characters-only guard names canvas item types, not every `create_`

Risk: MEDIUM. The plan names no floor for a follow-up, so MEDIUM is the default. It is a test-only change, and it restores a green `main`.

**Base:** `53e89be` (`main` with WI-3 #123 and WI-9 #132). **Lane C, Dev C.**

## What went wrong

WI-3's guard (`tests/test_shell_characters_only.py`, WI-3/C8) flagged every attribute starting `create_` other than `create_text`. WI-9's `anchor.py` calls `ctypes.create_string_buffer`, which draws nothing. Each PR was green on its own branch, but together they fail on `main`: at `53e89be` the default suite is `1 failed, 545 passed`. I wrote both, and both merged within minutes of each other.

## The change

The guard now names every Tk canvas item type except text, one by one: `create_arc`, `create_bitmap`, `create_image`, `create_line`, `create_oval`, `create_polygon`, `create_rectangle`, `create_window`. It also names the image makers: `PhotoImage`, `BitmapImage`, `image_create`. That is exactly the set a canvas can draw that is not text, so C8's rule is unchanged. A new control shows that all eight item types are caught and that `create_text` and `create_string_buffer` are not.

## Claims

| Claim | Claim | Evidence | Output shows | Control |
|---|---|---|---|---|
| **A1** | The characters-only guard reports every non-text canvas item type and image maker in the shell's source, and nothing that is not one, so the shell's use of `ctypes.create_string_buffer` does not fail it. | Executable: `.venv/bin/python -m pytest -q -v tests/test_shell_characters_only.py` | `4 passed`, including `test_the_scan_catches_every_canvas_item_type_but_text_and_nothing_that_is_not_one` and `test_the_shell_makes_no_drawing_call_but_create_text` | Control: `git checkout --detach 53e89be && .venv/bin/python -m pytest -q tests/test_shell_characters_only.py` (no overlay: the base's own guard over the base's own shell). It fails at `test_the_shell_makes_no_drawing_call_but_create_text` with `'terminal_game/shell/anchor.py:108 create_string_buffer'`, `1 failed, 2 passed`. |
| **A2** | The default suite on `main` plus this change is green. | Executable: `.venv/bin/python -m pytest -q` | `547 passed, 1 skipped, 17 deselected` | Control: the same command at `53e89be` gives `1 failed, 545 passed, 1 skipped, 17 deselected` |

## Diff map

```
tests/test_shell_characters_only.py:19-28  -> A1 (the explicit forbidden set, and why)
tests/test_shell_characters_only.py:42     -> A1 (match by name, not by prefix)
tests/test_shell_characters_only.py:end    -> A1 (the new control test)
docs/prs/PR-WI-3-guard-fix.md, docs/progress/r8-wi-3-guard-fix.md -> records
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
