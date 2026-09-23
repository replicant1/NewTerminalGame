# FIX-1: the characters-only guard judges canvas drawing calls, not every `create_` name

Risk: MEDIUM. It changes the evidence behind WI-3/C8 (a guard that runs in the default suite), not production code, and it turns `main` green again. The conductor set the floor at MEDIUM. I have not raised it to HIGH: nothing that opens or draws a window changes, and the guard ends up flagging the same eight canvas item types it always could.

**Base:** `53e89be` (`main` with WI-3 #123 and WI-9 #132). **Lane C, Dev C.** This replaces #134, the same change under a WI-3 name, which I have closed.

## What went wrong

WI-3's guard, `tests/test_shell_characters_only.py`, is the evidence for WI-3/C8. It flagged every attribute or name starting `create_` except `create_text`. WI-9's `terminal_game/shell/anchor.py:108` calls `ctypes.create_string_buffer`, which draws nothing. Each pull request was green on its own head, because WI-9 was verified at a head without WI-3's guard. Together on `main` at `53e89be`, the default suite is `1 failed, 545 passed, 1 skipped, 17 deselected`. I wrote both.

## The change

The guard now names exactly what a Tk canvas can draw that is not text: the eight other item types, `create_arc`, `create_bitmap`, `create_image`, `create_line`, `create_oval`, `create_polygon`, `create_rectangle` and `create_window`, and the ways to make an image, `PhotoImage`, `BitmapImage` and `image_create`. A name is flagged when it matches one of these, not when it merely starts with `create_`. **C8 is not weakened.** Every canvas call the old prefix rule could catch is in the list; the only names it no longer flags are non-canvas ones like `create_string_buffer`.

## Claims

| Claim | Claim | Evidence | Output shows | Control |
|---|---|---|---|---|
| **FIX-1/A1** | The characters-only guard flags every non-text Tk canvas drawing call and every image maker by name, and does not flag a name that is not one, so `ctypes.create_string_buffer` in the shell passes it. The reason: a `create_` prefix is not a canvas call, and treating it as one failed `main`. | Executable: `.venv/bin/python -m pytest -q -v tests/test_shell_characters_only.py -k "every_canvas_item_type or makes_no_drawing_call"` | `2 passed`: `test_the_scan_catches_every_canvas_item_type_but_text_and_nothing_that_is_not_one` (all eight `create_<type>` flagged; `create_text` and `create_string_buffer` not) and `test_the_shell_makes_no_drawing_call_but_create_text` (the real shell, `anchor.py` included, is clean) | Control: `git checkout --detach 53e89be && .venv/bin/python -m pytest -q tests/test_shell_characters_only.py`, with no overlay: the base's own guard over the base's own shell. It fails at `test_the_shell_makes_no_drawing_call_but_create_text` with `'terminal_game/shell/anchor.py:108 create_string_buffer'`, `1 failed, 2 passed`. |
| **FIX-1/A2** | C8 still bites on the real drawing code: `terminal_game/shell/window.py`'s source, with one `canvas.create_line`, `canvas.create_rectangle` or `canvas.create_image` added in memory, is reported for exactly that call. | Executable: `.venv/bin/python -m pytest -q -v tests/test_shell_characters_only.py -k "real_canvas or every_kind"` | `2 passed`: `test_a_real_canvas_drawing_call_in_the_window_module_would_be_caught`, and the earlier sample control `test_the_scan_catches_every_kind_of_non_text_drawing` (rectangle, line, oval, polygon, image, window, `PhotoImage`) | n/a: nothing on the base to compare it against. The base's prefix rule would also flag these three, so this claim shows the fix lost nothing; it does not show a change. |
| **FIX-1/A3** | The default suite is green on `main` plus this change. | Executable: `.venv/bin/python -m pytest -q` | `548 passed, 1 skipped, 17 deselected` | Control: the same command at `53e89be` gives `1 failed, 545 passed, 1 skipped, 17 deselected`, with no overlay. |

## Diff map

```
tests/test_shell_characters_only.py:19-27   -> FIX-1/A1 (the explicit forbidden set, and why)
tests/test_shell_characters_only.py:41      -> FIX-1/A1 (match by name, not by prefix)
tests/test_shell_characters_only.py:80-87   -> FIX-1/A1 (control: every item type yes; create_text and create_string_buffer no)
tests/test_shell_characters_only.py:90-100  -> FIX-1/A2 (control on the real window source, in memory)
docs/prs/PR-FIX-1-guard-anchor.md, docs/progress/r8-fix-1-guard-anchor.md -> records
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
